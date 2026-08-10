#!/usr/bin/env python3

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import plan_migration


class PlanMigrationTests(unittest.TestCase):
    def test_path_map_uses_longest_prefix(self) -> None:
        mappings = plan_migration.parse_path_maps(
            ["/old=/new", "/old/specific=/replacement"]
        )
        self.assertEqual(
            plan_migration.map_path("/old/specific/project", mappings),
            Path("/replacement/project"),
        )

    def test_missing_t3_state_blocks_project_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            warnings: list[str] = []
            existing, status = plan_migration.existing_t3_projects(root, warnings)
            projects = plan_migration.assemble_projects(
                [],
                [],
                [project],
                [],
                existing,
                target_inventory_ok=status == "ok",
            )
            self.assertEqual(status, "missing")
            self.assertEqual(len(warnings), 1)
            self.assertEqual(projects[0]["action"], "blocked-target-unavailable")

    def test_missing_provider_homes_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = plan_migration.main(
                    [
                        "--projects-only",
                        "--codex-home",
                        str(root / "missing-codex"),
                        "--claude-home",
                        str(root / "missing-claude"),
                        "--t3-home",
                        str(root / "missing-t3"),
                    ]
                )
            plan = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(plan["summary"]["source_stores_missing"], 2)
            self.assertEqual(
                plan["source_homes"]["codex"]["inventory_status"], "missing"
            )
            self.assertEqual(
                plan["source_homes"]["claude_code"]["inventory_status"],
                "missing",
            )

    def test_claude_active_branch_excludes_abandoned_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            project_dir = root / "claude" / "projects" / "encoded"
            project_dir.mkdir(parents=True)
            session_id = "11111111-1111-4111-8111-111111111111"
            transcript = project_dir / f"{session_id}.jsonl"
            records = [
                self.message("user", "root", None, workspace, "hello"),
                self.message("assistant", "abandoned", "root", workspace, "old"),
                {
                    "type": "system",
                    "uuid": "bridge",
                    "parentUuid": "root",
                    "cwd": str(workspace),
                },
                self.message("assistant", "active", "bridge", workspace, "new"),
                {"type": "last-prompt", "sessionId": session_id, "leafUuid": "active"},
            ]
            transcript.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions = plan_migration.scan_claude(
                root / "claude",
                "active",
                [],
                [],
                False,
                True,
                warnings,
            )
            self.assertEqual(warnings, [])
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["message_count"], 2)
            self.assertEqual(sessions[0]["branch_count"], 2)
            self.assertTrue(sessions[0]["resume"]["candidate"])

    def test_nested_session_uses_git_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository"
            (repository / ".git").mkdir(parents=True)
            workspace = repository / "nested" / "folder"
            workspace.mkdir(parents=True)
            session = {
                "provider": "codex",
                "workspace_root": str(workspace),
            }
            projects = plan_migration.assemble_projects(
                [session],
                [],
                [],
                [],
                {
                    str(Path(directory).resolve()): {
                        "project_id": "broad-parent",
                        "title": "Broad parent",
                    }
                },
            )
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0]["workspace_root"], str(repository.resolve()))
            self.assertEqual(session["project_root"], str(repository.resolve()))

    def test_malformed_codex_session_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            sessions_root = root / "codex" / "sessions" / "2026" / "08" / "10"
            sessions_root.mkdir(parents=True)
            session_id = "44444444-4444-4444-8444-444444444444"
            transcript = sessions_root / f"rollout-test-{session_id}.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "session_meta",
                        "payload": {"id": session_id, "cwd": str(workspace)},
                    }
                )
                + "\n[]\n{malformed\n",
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions, _ = plan_migration.scan_codex(
                root / "codex",
                False,
                [],
                [],
                False,
                True,
                warnings,
            )
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["parse_error_count"], 2)
            self.assertFalse(sessions[0]["source_ready"])
            self.assertFalse(sessions[0]["resume"]["candidate"])
            self.assertEqual(len(warnings), 2)

    def test_non_uuid_codex_session_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            sessions_root = root / "codex" / "sessions" / "2026" / "08" / "10"
            sessions_root.mkdir(parents=True)
            transcript = sessions_root / "rollout-test-not-a-uuid.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "session_meta",
                        "payload": {"id": "not-a-uuid", "cwd": str(workspace)},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions, _ = plan_migration.scan_codex(
                root / "codex",
                False,
                [],
                [],
                False,
                True,
                warnings,
            )
            self.assertEqual(len(sessions), 1)
            self.assertFalse(sessions[0]["session_id_valid"])
            self.assertFalse(sessions[0]["source_ready"])
            self.assertFalse(sessions[0]["resume"]["candidate"])
            self.assertEqual(len(warnings), 1)

    def test_codex_mirrored_image_is_not_double_counted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            sessions_root = root / "codex" / "sessions" / "2026" / "08" / "10"
            sessions_root.mkdir(parents=True)
            session_id = "66666666-6666-4666-8666-666666666666"
            transcript = sessions_root / f"rollout-test-{session_id}.jsonl"
            records = [
                {
                    "type": "session_meta",
                    "payload": {"id": session_id, "cwd": str(workspace)},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_image", "image_url": "private"}],
                    },
                },
                {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "local_images": ["private"]},
                },
            ]
            transcript.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions, _ = plan_migration.scan_codex(
                root / "codex",
                False,
                [],
                [],
                False,
                True,
                warnings,
            )
            self.assertEqual(warnings, [])
            self.assertEqual(sessions[0]["attachment_count"], 1)
            self.assertEqual(
                sessions[0]["attachment_source_counts"],
                {"response_items": 1, "event_messages": 1},
            )

    def test_project_filter_does_not_assign_cwdless_claude_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected_project = root / "selected"
            selected_project.mkdir()
            project_dir = root / "claude" / "projects" / "encoded"
            project_dir.mkdir(parents=True)
            session_id = "77777777-7777-4777-8777-777777777777"
            transcript = project_dir / f"{session_id}.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "user",
                        "sessionId": session_id,
                        "uuid": "root",
                        "parentUuid": None,
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": "hello"}],
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions = plan_migration.scan_claude(
                root / "claude",
                "active",
                [],
                [selected_project.resolve()],
                False,
                True,
                warnings,
            )
            self.assertEqual(warnings, [])
            self.assertEqual(sessions, [])

    def test_linked_worktree_maps_to_main_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            metadata = repository / ".git" / "worktrees" / "test"
            metadata.mkdir(parents=True)
            (metadata / "commondir").write_text("../..\n", encoding="utf-8")
            worktree = root / "worktree"
            worktree.mkdir()
            (worktree / ".git").write_text(
                f"gitdir: {metadata}\n",
                encoding="utf-8",
            )
            workspace = worktree / "nested"
            workspace.mkdir()
            session = {
                "provider": "codex",
                "workspace_root": str(workspace),
            }
            projects = plan_migration.assemble_projects(
                [session],
                [],
                [],
                [],
                {},
            )
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0]["workspace_root"], str(repository.resolve()))
            self.assertEqual(session["worktree_path"], str(worktree.resolve()))

    def test_project_filter_includes_linked_worktree_codex_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            metadata = repository / ".git" / "worktrees" / "test"
            metadata.mkdir(parents=True)
            (metadata / "commondir").write_text("../..\n", encoding="utf-8")
            worktree = root / "worktree"
            worktree.mkdir()
            (worktree / ".git").write_text(
                f"gitdir: {metadata}\n",
                encoding="utf-8",
            )
            workspace = worktree / "nested"
            workspace.mkdir()
            sessions_root = root / "codex" / "sessions" / "2026" / "08" / "10"
            sessions_root.mkdir(parents=True)
            session_id = "88888888-8888-4888-8888-888888888888"
            transcript = sessions_root / f"rollout-test-{session_id}.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "session_meta",
                        "payload": {"id": session_id, "cwd": str(workspace)},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions, _ = plan_migration.scan_codex(
                root / "codex",
                False,
                [],
                [repository.resolve()],
                False,
                True,
                warnings,
            )
            self.assertEqual(warnings, [])
            self.assertEqual(len(sessions), 1)
            projects = plan_migration.assemble_projects(
                sessions,
                [],
                [],
                [],
                {},
            )
            self.assertEqual(projects[0]["workspace_root"], str(repository.resolve()))
            self.assertEqual(sessions[0]["worktree_path"], str(worktree.resolve()))

    def test_git_submodule_is_not_treated_as_linked_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            superproject = root / "superproject"
            metadata = superproject / ".git" / "modules" / "submodule"
            metadata.mkdir(parents=True)
            submodule = superproject / "submodule"
            submodule.mkdir()
            (submodule / ".git").write_text(
                f"gitdir: {metadata}\n",
                encoding="utf-8",
            )
            workspace = submodule / "nested"
            workspace.mkdir()
            session = {
                "provider": "codex",
                "workspace_root": str(workspace),
            }
            projects = plan_migration.assemble_projects(
                [session],
                [],
                [],
                [],
                {},
            )
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0]["workspace_root"], str(submodule.resolve()))
            self.assertEqual(session["project_root"], str(submodule.resolve()))
            self.assertNotIn("worktree_path", session)

    def test_claude_uses_history_project_when_transcript_cwd_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            claude_home = root / "claude"
            project_dir = claude_home / "projects" / "encoded"
            project_dir.mkdir(parents=True)
            session_id = "55555555-5555-4555-8555-555555555555"
            transcript = project_dir / f"{session_id}.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "user",
                        "sessionId": session_id,
                        "uuid": "root",
                        "parentUuid": None,
                        "message": {
                            "role": "user",
                            "content": [{"type": "text", "text": "hello"}],
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (claude_home / "history.jsonl").write_text(
                json.dumps({"sessionId": session_id, "project": str(workspace)}) + "\n",
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions = plan_migration.scan_claude(
                claude_home,
                "active",
                [],
                [],
                False,
                True,
                warnings,
            )
            self.assertEqual(warnings, [])
            self.assertEqual(sessions[0]["workspace_root"], str(workspace.resolve()))
            self.assertEqual(sessions[0]["workspace_source"], "history-project")
            self.assertTrue(sessions[0]["source_ready"])

    def test_codex_uses_first_session_meta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            sessions_root = root / "codex" / "sessions" / "2026" / "08" / "10"
            sessions_root.mkdir(parents=True)
            session_id = "22222222-2222-4222-8222-222222222222"
            transcript = sessions_root / f"rollout-test-{session_id}.jsonl"
            records = [
                {
                    "type": "session_meta",
                    "payload": {"id": session_id, "cwd": str(workspace)},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "hello"}],
                    },
                },
                {
                    "type": "session_meta",
                    "payload": {
                        "id": "33333333-3333-4333-8333-333333333333",
                        "cwd": "/wrong",
                    },
                },
            ]
            transcript.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            warnings: list[str] = []
            sessions, _ = plan_migration.scan_codex(
                root / "codex",
                False,
                [],
                [],
                False,
                True,
                warnings,
            )
            self.assertEqual(warnings, [])
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["native_session_id"], session_id)
            self.assertEqual(sessions[0]["workspace_root"], str(workspace.resolve()))

    @staticmethod
    def message(
        role: str,
        node_id: str,
        parent_id: str | None,
        workspace: Path,
        text: str,
    ) -> dict[str, object]:
        return {
            "type": role,
            "sessionId": "11111111-1111-4111-8111-111111111111",
            "uuid": node_id,
            "parentUuid": parent_id,
            "cwd": str(workspace),
            "message": {"role": role, "content": [{"type": "text", "text": text}]},
        }


if __name__ == "__main__":
    unittest.main()
