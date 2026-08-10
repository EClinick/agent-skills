#!/usr/bin/env python3
"""Build a read-only, content-free plan for migrating projects and sessions to T3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import quote


SCHEMA_VERSION = 1
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


@dataclass(frozen=True)
class PathMap:
    source: Path
    target: Path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only migration plan for T3 Code."
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--projects-only",
        action="store_true",
        help="Plan project registration without sessions.",
    )
    scope.add_argument(
        "--provider",
        action="append",
        choices=("codex", "claude", "claude-code"),
        help="Plan sessions for a provider. Repeat to select both.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        metavar="PATH",
        help="Limit scope to a project path. Repeat as needed.",
    )
    parser.add_argument(
        "--session",
        action="append",
        default=[],
        metavar="ID",
        help="Limit provider scope to a native or plan session ID. Repeat as needed.",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Include archived Codex sessions.",
    )
    parser.add_argument(
        "--claude-branches",
        choices=("active", "all"),
        default="active",
    )
    parser.add_argument(
        "--no-resume-links",
        action="store_true",
        help="Plan display-only imports without provider resume cursors.",
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))),
    )
    parser.add_argument(
        "--claude-home",
        type=Path,
        default=Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))),
    )
    parser.add_argument(
        "--t3-home",
        type=Path,
        default=Path(os.environ.get("T3CODE_HOME", str(Path.home() / ".t3"))),
    )
    parser.add_argument(
        "--path-map",
        action="append",
        default=[],
        metavar="OLD=NEW",
        help="Map a source path prefix before canonicalization. Repeat as needed.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the private JSON plan to this path instead of stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON.",
    )
    args = parser.parse_args(argv)
    if args.projects_only and args.session:
        parser.error("--session cannot be combined with --projects-only")
    return args


def normalize_providers(values: list[str] | None, projects_only: bool) -> list[str]:
    if projects_only:
        return []
    if not values:
        return ["codex", "claude-code"]
    normalized = ["claude-code" if value == "claude" else value for value in values]
    return sorted(set(normalized))


def parse_path_maps(values: list[str]) -> list[PathMap]:
    mappings: list[PathMap] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid path map {value!r}; expected OLD=NEW")
        source, target = value.split("=", 1)
        if not source or not target:
            raise ValueError(f"invalid path map {value!r}; expected OLD=NEW")
        mappings.append(
            PathMap(
                source=Path(source).expanduser().absolute(),
                target=Path(target).expanduser().absolute(),
            )
        )
    return sorted(mappings, key=lambda item: len(str(item.source)), reverse=True)


def map_path(value: str | Path | None, mappings: list[PathMap]) -> Path | None:
    if value is None or not str(value).strip():
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = path.absolute()
    for mapping in mappings:
        try:
            relative = path.relative_to(mapping.source)
        except ValueError:
            continue
        path = mapping.target / relative
        break
    if path.exists():
        return Path(os.path.realpath(path))
    return Path(os.path.normpath(path))


def path_selected(path: Path | None, selected: list[Path]) -> bool:
    if not selected:
        return True
    if path is None:
        return False
    for root in selected:
        if path == root:
            return True
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def find_git_root(path: Path) -> Path | None:
    candidate = path if path.is_dir() or not path.exists() else path.parent
    for parent in (candidate, *candidate.parents):
        if (parent / ".git").exists():
            return parent
    return None


def linked_worktree_main_root(git_root: Path) -> Path | None:
    marker = git_root / ".git"
    if not marker.is_file():
        return None
    try:
        first_line = marker.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return None
    if not first_line.startswith("gitdir:"):
        return None
    metadata = Path(first_line.split(":", 1)[1].strip())
    if not metadata.is_absolute():
        metadata = (git_root / metadata).resolve()
    common_file = metadata / "commondir"
    try:
        common_value = common_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    common_directory = (metadata / common_value).resolve()
    if common_directory.name != ".git" or not common_directory.parent.is_dir():
        return None
    return Path(os.path.realpath(common_directory.parent))


def infer_project_root(path: Path) -> Path:
    candidate = path if path.is_dir() or not path.exists() else path.parent
    git_root = find_git_root(path)
    if git_root is None:
        return candidate
    return linked_worktree_main_root(git_root) or git_root


def workspace_selected(path: Path | None, selected: list[Path]) -> bool:
    if path_selected(path, selected):
        return True
    if path is None or not path.exists():
        return False
    return path_selected(infer_project_root(path), selected)


def containing_project_root(path: Path, candidates: Iterable[Path]) -> Path | None:
    matches: list[Path] = []
    for candidate in candidates:
        if path == candidate:
            matches.append(candidate)
            continue
        try:
            path.relative_to(candidate)
            matches.append(candidate)
        except ValueError:
            continue
    return max(matches, key=lambda item: len(item.parts), default=None)


def safe_title(value: Any, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    normalized = " ".join(value.split())
    return normalized[:160] if normalized else fallback


def iso_from_epoch(value: Any, milliseconds: bool = False) -> str | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value) if isinstance(value, str) and value else None
    if milliseconds:
        numeric /= 1000
    try:
        return datetime.fromtimestamp(numeric, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def file_content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_fingerprint(path: Path, include_content_hash: bool) -> dict[str, Any]:
    stat = path.stat()
    result: dict[str, Any] = {
        "size_bytes": stat.st_size,
        "modified_ns": stat.st_mtime_ns,
    }
    if include_content_hash:
        result["sha256"] = file_content_hash(path)
    fingerprint_payload = json.dumps(result, sort_keys=True, separators=(",", ":"))
    result["fingerprint"] = hashlib.sha256(fingerprint_payload.encode()).hexdigest()
    return result


def iter_jsonl(
    path: Path,
    warnings: list[str],
    parse_errors: list[int] | None = None,
) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                value = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                warnings.append(f"{path}: skipped malformed JSONL line {line_number}")
                if parse_errors is not None:
                    parse_errors.append(line_number)
                continue
            if not isinstance(value, dict):
                warnings.append(f"{path}: skipped non-object JSONL line {line_number}")
                if parse_errors is not None:
                    parse_errors.append(line_number)
                continue
            yield line_number, value


def read_json(path: Path, warnings: list[str]) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        warnings.append(f"{path}: could not read JSON ({error})")
        return None


def readonly_sqlite(path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(path.resolve()))}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def sqlite_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}


def codex_names(home: Path, warnings: list[str]) -> dict[str, str]:
    path = home / "session_index.jsonl"
    names: dict[str, tuple[str, str]] = {}
    if not path.is_file():
        return {}
    for _, record in iter_jsonl(path, warnings):
        session_id = record.get("id")
        title = record.get("thread_name")
        updated = str(record.get("updated_at") or "")
        if isinstance(session_id, str) and isinstance(title, str):
            previous = names.get(session_id)
            if previous is None or updated >= previous[0]:
                names[session_id] = (updated, title)
    return {session_id: title for session_id, (_, title) in names.items()}


def codex_catalog(home: Path, warnings: list[str]) -> dict[str, dict[str, Any]]:
    path = home / "state_5.sqlite"
    if not path.is_file():
        return {}
    try:
        connection = readonly_sqlite(path)
    except sqlite3.Error as error:
        warnings.append(f"{path}: could not open read-only catalog ({error})")
        return {}
    try:
        columns = sqlite_columns(connection, "threads")
        wanted = [
            name
            for name in (
                "id",
                "rollout_path",
                "cwd",
                "title",
                "name",
                "created_at",
                "created_at_ms",
                "updated_at",
                "updated_at_ms",
                "archived",
                "git_branch",
                "model",
                "model_provider",
            )
            if name in columns
        ]
        if "id" not in wanted:
            return {}
        rows = connection.execute(f"SELECT {', '.join(wanted)} FROM threads")
        return {str(row["id"]): dict(row) for row in rows}
    except sqlite3.Error as error:
        warnings.append(f"{path}: could not query thread catalog ({error})")
        return {}
    finally:
        connection.close()


def codex_global_projects(home: Path, warnings: list[str]) -> list[dict[str, Any]]:
    path = home / ".codex-global-state.json"
    if not path.is_file():
        return []
    state = read_json(path, warnings)
    if not isinstance(state, dict):
        return []
    local_projects = state.get("local-projects")
    if not isinstance(local_projects, dict):
        return []
    projects: list[dict[str, Any]] = []
    for value in local_projects.values():
        if not isinstance(value, dict):
            continue
        roots = value.get("rootPaths")
        if not isinstance(roots, list):
            continue
        for root in roots:
            if isinstance(root, str):
                projects.append(
                    {
                        "path": root,
                        "title": value.get("name"),
                        "source": "codex-global-state",
                        "provider": "codex",
                    }
                )
    return projects


def codex_paths(home: Path, include_archived: bool) -> Iterator[tuple[Path, bool]]:
    sessions = home / "sessions"
    if sessions.is_dir():
        for path in sorted(sessions.glob("*/*/*/*.jsonl")):
            yield path, False
    if include_archived:
        archived = home / "archived_sessions"
        if archived.is_dir():
            for path in sorted(archived.glob("*.jsonl")):
                yield path, True


def visible_codex_message(payload: dict[str, Any]) -> bool:
    if payload.get("type") != "message":
        return False
    if payload.get("role") not in ("user", "assistant"):
        return False
    content = payload.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return any(
            isinstance(block, dict)
            and block.get("type")
            in (
                "input_text",
                "output_text",
                "text",
                "image",
                "input_image",
                "output_image",
            )
            for block in content
        )
    return False


def scan_codex(
    home: Path,
    include_archived: bool,
    mappings: list[PathMap],
    selected: list[Path],
    hash_content: bool,
    resume_links: bool,
    warnings: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    catalog = codex_catalog(home, warnings)
    names = codex_names(home, warnings)
    sessions: dict[str, dict[str, Any]] = {}
    project_hints = codex_global_projects(home, warnings)

    for path, archived in codex_paths(home, include_archived):
        before = path.stat()
        header: dict[str, Any] | None = None
        invalid_header = False
        message_count = 0
        activity_count = 0
        response_attachment_count = 0
        event_attachment_count = 0
        record_count = 0
        parse_errors: list[int] = []
        for _, record in iter_jsonl(path, warnings, parse_errors):
            record_count += 1
            outer_type = record.get("type")
            payload = record.get("payload")
            if record_count == 1:
                if outer_type == "session_meta" and isinstance(payload, dict):
                    header = payload
                else:
                    invalid_header = True
            elif outer_type == "response_item" and isinstance(payload, dict):
                if visible_codex_message(payload):
                    message_count += 1
                content = payload.get("content")
                if isinstance(content, list):
                    response_attachment_count += sum(
                        1
                        for block in content
                        if isinstance(block, dict)
                        and block.get("type")
                        in ("image", "input_image", "output_image")
                    )
                if payload.get("type") in (
                    "function_call",
                    "function_call_output",
                    "custom_tool_call",
                    "custom_tool_call_output",
                ):
                    activity_count += 1
            elif outer_type == "event_msg" and isinstance(payload, dict):
                if payload.get("type") not in (
                    "user_message",
                    "agent_message",
                    "token_count",
                ):
                    activity_count += 1
                for key in ("local_images", "local_audio", "images", "audio"):
                    value = payload.get(key)
                    if isinstance(value, list):
                        event_attachment_count += len(value)

        after = path.stat()
        if invalid_header or header is None:
            warnings.append(f"{path}: missing initial session_meta payload")
            continue
        session_id = header.get("id")
        if not isinstance(session_id, str) or not session_id:
            warnings.append(f"{path}: missing native Codex session ID")
            continue
        session_id_valid = bool(UUID_RE.fullmatch(session_id))
        if not session_id_valid:
            warnings.append(f"{path}: native Codex session ID is not a UUID")
        if session_id_valid and not path.stem.endswith(session_id):
            warnings.append(f"{path}: filename UUID does not match session metadata")
            continue
        catalog_row = catalog.get(session_id, {})
        workspace = map_path(header.get("cwd") or catalog_row.get("cwd"), mappings)
        if not workspace_selected(workspace, selected):
            continue
        title = safe_title(
            catalog_row.get("name")
            or names.get(session_id)
            or catalog_row.get("title"),
            session_id,
        )
        created_at = (
            header.get("timestamp")
            or iso_from_epoch(catalog_row.get("created_at_ms"), milliseconds=True)
            or iso_from_epoch(catalog_row.get("created_at"))
        )
        updated_at = iso_from_epoch(
            catalog_row.get("updated_at_ms"), milliseconds=True
        ) or iso_from_epoch(catalog_row.get("updated_at"))
        fingerprint = file_fingerprint(path, hash_content)
        final = path.stat()
        stable = (
            (before.st_size, before.st_mtime_ns)
            == (after.st_size, after.st_mtime_ns)
            == (final.st_size, final.st_mtime_ns)
            == (fingerprint["size_bytes"], fingerprint["modified_ns"])
        )
        if not stable:
            warnings.append(f"{path}: changed while being scanned")
        catalog_archived = (
            bool(catalog_row.get("archived")) if "archived" in catalog_row else None
        )
        archive_conflict = catalog_archived is not None and catalog_archived != archived
        if archive_conflict:
            warnings.append(
                f"{path}: archive location disagrees with the Codex catalog"
            )
        candidate = {
            "provider": "codex",
            "native_session_id": session_id,
            "native_import_id": f"codex:{session_id}",
            "source_path": str(path.resolve()),
            "source_fingerprint": fingerprint,
            "stable": stable,
            "workspace_root": str(workspace) if workspace else None,
            "workspace_exists": workspace.exists() if workspace else False,
            "title": title,
            "created_at": created_at,
            "updated_at": updated_at,
            "archived": bool(archived),
            "archive_conflict": archive_conflict,
            "session_id_valid": session_id_valid,
            "parse_error_count": len(parse_errors),
            "record_count": record_count,
            "message_count": message_count,
            "activity_count": activity_count,
            "attachment_count": max(
                response_attachment_count,
                event_attachment_count,
            ),
            "attachment_source_counts": {
                "response_items": response_attachment_count,
                "event_messages": event_attachment_count,
            },
            "git_branch": catalog_row.get("git_branch"),
            "model": catalog_row.get("model"),
            "source_ready": bool(
                stable
                and not archive_conflict
                and not parse_errors
                and session_id_valid
                and workspace
                and workspace.exists()
            ),
            "resume": {
                "requested": resume_links,
                "candidate": bool(
                    resume_links
                    and stable
                    and not archive_conflict
                    and not parse_errors
                    and not archived
                    and session_id_valid
                    and workspace
                    and workspace.exists()
                ),
                "native_session_id": session_id,
                "requires_provider_validation": bool(resume_links),
            },
        }
        previous = sessions.get(session_id)
        if (
            previous is None
            or candidate["source_fingerprint"]["modified_ns"]
            > previous["source_fingerprint"]["modified_ns"]
        ):
            sessions[session_id] = candidate

    return sorted(sessions.values(), key=session_sort_key), project_hints


def claude_paths(home: Path) -> Iterator[Path]:
    projects = home / "projects"
    if not projects.is_dir():
        return
    for project_dir in sorted(projects.iterdir()):
        if not project_dir.is_dir():
            continue
        for path in sorted(project_dir.glob("*.jsonl")):
            yield path


def claude_history_projects(home: Path, warnings: list[str]) -> dict[str, str]:
    path = home / "history.jsonl"
    if not path.is_file():
        return {}
    projects: dict[str, str] = {}
    for _, record in iter_jsonl(path, warnings):
        session_id = record.get("sessionId")
        project = record.get("project")
        if isinstance(session_id, str) and isinstance(project, str) and project:
            projects[session_id] = project
    return projects


def content_summary(message: Any) -> tuple[bool, int, int]:
    if not isinstance(message, dict):
        return False, 0, 0
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip()), 0, 0
    if not isinstance(content, list):
        return False, 0, 0
    visible = False
    activities = 0
    attachments = 0
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text" and isinstance(block.get("text"), str):
            visible = visible or bool(block["text"].strip())
        elif block_type in ("tool_use", "tool_result"):
            activities += 1
        elif block_type == "image":
            visible = True
            attachments += 1
    return visible, activities, attachments


def active_chain(
    nodes: dict[str, tuple[str | None, bool, int, int]], leaf: str | None
) -> tuple[list[str], bool]:
    if leaf is None or leaf not in nodes:
        return [], False
    chain: list[str] = []
    seen: set[str] = set()
    complete = True
    current: str | None = leaf
    while current:
        if current in seen:
            complete = False
            break
        seen.add(current)
        node = nodes.get(current)
        if node is None:
            complete = False
            break
        chain.append(current)
        current = node[0]
    chain.reverse()
    return chain, complete


def record_title(record: dict[str, Any]) -> str | None:
    record_type = record.get("type")
    keys_by_type = {
        "custom-title": ("customTitle", "title"),
        "ai-title": ("aiTitle", "title"),
        "agent-name": ("agentName", "name"),
    }
    for key in keys_by_type.get(str(record_type), ()):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def scan_claude(
    home: Path,
    branch_mode: str,
    mappings: list[PathMap],
    selected: list[Path],
    hash_content: bool,
    resume_links: bool,
    warnings: list[str],
) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    history_projects = claude_history_projects(home, warnings)
    for path in claude_paths(home):
        before = path.stat()
        nodes: dict[str, tuple[str | None, bool, int, int]] = {}
        children: set[str] = set()
        append_order: list[str] = []
        session_id = path.stem
        workspace_value: str | None = None
        relocated_value: str | None = None
        latest_leaf: str | None = None
        titles: dict[str, str] = {}
        seen_session_ids: set[str] = set()
        duplicate_node_count = 0
        created_at: str | None = None
        updated_at: str | None = None
        record_count = 0
        top_level_attachments = 0
        parse_errors: list[int] = []

        for _, record in iter_jsonl(path, warnings, parse_errors):
            record_count += 1
            record_session = record.get("sessionId")
            if isinstance(record_session, str):
                seen_session_ids.add(record_session)
            timestamp = record.get("timestamp")
            if isinstance(timestamp, str):
                created_at = created_at or timestamp
                updated_at = timestamp
            cwd = record.get("cwd")
            if isinstance(cwd, str) and cwd:
                workspace_value = cwd
            if record.get("type") == "relocated":
                relocated = record.get("relocatedCwd")
                if isinstance(relocated, str) and relocated:
                    relocated_value = relocated
            candidate_title = record_title(record)
            if candidate_title:
                titles[str(record.get("type"))] = candidate_title
            if record.get("type") == "last-prompt":
                leaf = record.get("leafUuid")
                if isinstance(leaf, str):
                    latest_leaf = leaf
            if record.get("type") == "attachment":
                top_level_attachments += 1
            node_id = record.get("uuid")
            if not isinstance(node_id, str) or not node_id:
                continue
            parent = record.get("parentUuid")
            parent_id = parent if isinstance(parent, str) and parent else None
            if record.get("type") in ("user", "assistant"):
                visible, activity_count, attachment_count = content_summary(
                    record.get("message")
                )
            else:
                visible, activity_count, attachment_count = False, 0, 0
            if record.get("isMeta"):
                visible = False
            if node_id in nodes:
                duplicate_node_count += 1
            nodes[node_id] = (parent_id, visible, activity_count, attachment_count)
            append_order.append(node_id)
            if parent_id:
                children.add(parent_id)

        after = path.stat()
        history_workspace = history_projects.get(session_id)
        workspace_source = (
            "relocatedCwd"
            if relocated_value
            else "transcript-cwd"
            if workspace_value
            else "history-project"
            if history_workspace
            else None
        )
        workspace_input = relocated_value or workspace_value or history_workspace
        workspace = map_path(workspace_input, mappings)
        if not workspace_selected(workspace, selected):
            continue
        unique_nodes = list(dict.fromkeys(append_order))
        leaves = [node_id for node_id in unique_nodes if node_id not in children]
        if latest_leaf not in nodes:
            conversation_order = [
                node_id
                for node_id in unique_nodes
                if nodes[node_id][1] or nodes[node_id][2]
            ]
            latest_leaf = conversation_order[-1] if conversation_order else None
        if branch_mode == "all":
            selected_leaves = list(leaves)
            if latest_leaf and latest_leaf not in selected_leaves:
                selected_leaves.append(latest_leaf)
        else:
            selected_leaves = [latest_leaf] if latest_leaf else []
        if not selected_leaves:
            selected_leaves = [None]
        fingerprint = file_fingerprint(path, hash_content)
        final = path.stat()
        stable = (
            (before.st_size, before.st_mtime_ns)
            == (after.st_size, after.st_mtime_ns)
            == (final.st_size, final.st_mtime_ns)
            == (fingerprint["size_bytes"], fingerprint["modified_ns"])
        )
        if not stable:
            warnings.append(f"{path}: changed while being scanned")
        session_id_conflict = bool(seen_session_ids - {session_id})
        if session_id_conflict:
            warnings.append(
                f"{path}: record sessionId disagrees with the filename UUID"
            )
        session_id_valid = bool(UUID_RE.match(session_id))
        if not session_id_valid:
            warnings.append(f"{path}: filename is not a Claude session UUID")
        title = (
            titles.get("custom-title")
            or titles.get("ai-title")
            or titles.get("agent-name")
        )
        missing_parent_count = sum(
            1
            for parent_id, _, _, _ in nodes.values()
            if parent_id is not None and parent_id not in nodes
        )
        root_count = sum(
            1 for parent_id, _, _, _ in nodes.values() if parent_id is None
        )
        subagent_root = path.parent / path.stem / "subagents"
        subagent_count = (
            sum(1 for _ in subagent_root.rglob("agent-*.jsonl"))
            if subagent_root.is_dir()
            else 0
        )
        namespace_source = str(workspace) if workspace else str(path.parent.resolve())
        source_namespace = hashlib.sha256(namespace_source.encode()).hexdigest()[:16]

        for branch_index, leaf in enumerate(selected_leaves, 1):
            chain, complete_chain = active_chain(nodes, leaf)
            message_count = sum(1 for node_id in chain if nodes[node_id][1])
            activity_count = sum(nodes[node_id][2] for node_id in chain)
            attachment_count = top_level_attachments + sum(
                nodes[node_id][3] for node_id in chain
            )
            native_import_id = f"claude-code:{source_namespace}:{session_id}"
            branch_title = safe_title(title, session_id)
            ready = bool(
                stable
                and not parse_errors
                and not session_id_conflict
                and session_id_valid
                and complete_chain
                and duplicate_node_count == 0
                and workspace
                and workspace.exists()
            )
            resume_candidate = bool(
                resume_links
                and stable
                and not parse_errors
                and not session_id_conflict
                and session_id_valid
                and workspace
                and workspace.exists()
                and leaf == latest_leaf
            )
            if branch_mode == "all" and len(selected_leaves) > 1:
                native_import_id = f"{native_import_id}:{leaf or branch_index}"
                branch_title = f"{branch_title} (branch {branch_index})"
            sessions.append(
                {
                    "provider": "claude-code",
                    "native_session_id": session_id,
                    "native_import_id": native_import_id,
                    "source_path": str(path.resolve()),
                    "source_fingerprint": fingerprint,
                    "stable": stable,
                    "workspace_root": str(workspace) if workspace else None,
                    "workspace_source": workspace_source,
                    "workspace_exists": workspace.exists() if workspace else False,
                    "title": branch_title,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "record_count": record_count,
                    "parse_error_count": len(parse_errors),
                    "message_count": message_count,
                    "activity_count": activity_count,
                    "attachment_count": attachment_count,
                    "branch_leaf_uuid": leaf,
                    "branch_chain_complete": complete_chain,
                    "branch_count": len(leaves),
                    "graph_root_count": root_count,
                    "graph_missing_parent_count": missing_parent_count,
                    "graph_duplicate_node_count": duplicate_node_count,
                    "session_id_conflict": session_id_conflict,
                    "session_id_valid": session_id_valid,
                    "subagent_count": subagent_count,
                    "subagents_action": "unsupported-not-planned",
                    "source_ready": ready,
                    "resume": {
                        "requested": resume_links,
                        "candidate": resume_candidate,
                        "native_session_id": session_id,
                        "requires_provider_validation": bool(resume_links),
                    },
                }
            )

    return sorted(sessions, key=session_sort_key)


def session_sort_key(session: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(session.get("workspace_root") or ""),
        str(session.get("provider") or ""),
        str(session.get("native_import_id") or session.get("native_session_id") or ""),
    )


def existing_t3_projects(
    home: Path, warnings: list[str]
) -> tuple[dict[str, dict[str, Any]], str]:
    path = home / "userdata" / "state.sqlite"
    if not path.is_file():
        warnings.append(f"{path}: T3 state database is missing")
        return {}, "missing"
    try:
        connection = readonly_sqlite(path)
    except sqlite3.Error as error:
        warnings.append(f"{path}: could not open T3 state read-only ({error})")
        return {}, "unavailable"
    try:
        rows = connection.execute(
            "SELECT project_id, title, workspace_root, deleted_at FROM projection_projects"
        )
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            root = map_path(row["workspace_root"], [])
            if root is None or row["deleted_at"] is not None:
                continue
            result[str(root)] = {
                "project_id": row["project_id"],
                "title": row["title"],
            }
        return result, "ok"
    except sqlite3.Error as error:
        warnings.append(f"{path}: could not query T3 projects ({error})")
        return {}, "incompatible"
    finally:
        connection.close()


def t3_version() -> str | None:
    plist_path = Path("/Applications/T3 Code (Nightly).app/Contents/Info.plist")
    if not plist_path.is_file():
        plist_path = Path("/Applications/T3 Code.app/Contents/Info.plist")
    if not plist_path.is_file():
        return None
    try:
        with plist_path.open("rb") as handle:
            value = plistlib.load(handle).get("CFBundleShortVersionString")
        return str(value) if value else None
    except (OSError, plistlib.InvalidFileException):
        return None


def assemble_projects(
    sessions: list[dict[str, Any]],
    project_hints: list[dict[str, Any]],
    explicit: list[str | Path],
    mappings: list[PathMap],
    existing: dict[str, dict[str, Any]],
    target_inventory_ok: bool = True,
) -> list[dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = {}

    def add(
        path_value: str | Path | None,
        provider: str,
        title: Any = None,
        infer_root: bool = False,
        already_mapped: bool = False,
    ) -> Path | None:
        path = map_path(path_value, [] if already_mapped else mappings)
        if path is None:
            return None
        if infer_root:
            path = infer_project_root(path)
        key = str(path)
        item = projects.setdefault(
            key,
            {
                "workspace_root": key,
                "title": safe_title(title, path.name or key),
                "exists": path.exists(),
                "providers": [],
                "source_session_count": 0,
                "existing_t3_project": existing.get(key),
            },
        )
        if provider not in item["providers"]:
            item["providers"].append(provider)
        return path

    for path in explicit:
        add(path, "explicit")
    for hint in project_hints:
        hint_path = (
            map_path(hint.get("path"), [])
            if hint.get("mapped")
            else map_path(hint.get("path"), mappings)
        )
        add(
            hint_path,
            str(hint.get("provider") or "unknown"),
            hint.get("title"),
            infer_root=(
                str(hint.get("source") or "").endswith("transcript")
                or hint.get("source") == "codex-global-state"
            ),
            already_mapped=True,
        )
    for session in sessions:
        workspace = map_path(session.get("workspace_root"), [])
        if workspace is None:
            continue
        candidates = [Path(value) for value in (*projects.keys(), *existing.keys())]
        git_root = find_git_root(workspace)
        if git_root is not None:
            main_worktree = linked_worktree_main_root(git_root)
            if main_worktree is not None:
                project_root = main_worktree
                session["worktree_path"] = str(git_root)
            else:
                repository_candidates = [
                    candidate
                    for candidate in candidates
                    if candidate == git_root
                    or (
                        containing_project_root(candidate, [git_root]) is not None
                        and containing_project_root(workspace, [candidate]) is not None
                    )
                ]
                project_root = (
                    containing_project_root(workspace, repository_candidates)
                    or git_root
                )
        else:
            project_root = containing_project_root(workspace, candidates) or workspace
        existing_project = existing.get(str(project_root))
        add(
            project_root,
            str(session.get("provider")),
            existing_project.get("title") if existing_project else None,
            already_mapped=True,
        )
        session["project_root"] = str(project_root)
        project = projects.get(str(project_root))
        if project is not None:
            project["source_session_count"] += 1

    for project in projects.values():
        project["providers"].sort()
        project["action"] = (
            "blocked-target-unavailable"
            if not target_inventory_ok
            else "reuse"
            if project["existing_t3_project"]
            else "create"
            if project["exists"]
            else "skip-missing"
        )
    return sorted(projects.values(), key=lambda item: item["workspace_root"])


def plan_hash(plan: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in plan.items()
        if key not in ("generated_at", "plan_hash")
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def write_plan(plan: dict[str, Any], output: Path | None, compact: bool) -> None:
    indent = None if compact else 2
    text = json.dumps(plan, indent=indent, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
        return
    output = output.expanduser().absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        os.chmod(temporary, 0o600)
        handle.write(text)
    os.replace(temporary, output)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        mappings = parse_path_maps(args.path_map)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    providers = normalize_providers(args.provider, args.projects_only)
    selected = [
        path
        for value in args.project
        if (path := map_path(value, mappings)) is not None
    ]
    warnings: list[str] = []
    sessions: list[dict[str, Any]] = []
    project_discovery_sessions: list[dict[str, Any]] = []
    project_hints: list[dict[str, Any]] = []
    resume_links = not args.no_resume_links and not args.projects_only
    codex_home = args.codex_home.expanduser()
    claude_home = args.claude_home.expanduser()
    source_status = {
        "codex": "not-selected",
        "claude-code": "not-selected",
    }

    discover_codex_projects = (
        args.projects_only and not args.project
    ) or "codex" in providers
    if discover_codex_projects:
        source_status["codex"] = "ok" if codex_home.is_dir() else "missing"
        if source_status["codex"] != "ok":
            warnings.append(f"{codex_home}: Codex home is missing")
        codex_sessions, project_hints = scan_codex(
            codex_home,
            args.include_archived,
            mappings,
            selected,
            True,
            resume_links,
            warnings,
        )
        if args.projects_only:
            project_discovery_sessions.extend(codex_sessions)
        if selected:
            project_hints = [
                hint
                for hint in project_hints
                if workspace_selected(map_path(hint.get("path"), mappings), selected)
            ]
        if not args.projects_only and "codex" in providers:
            sessions.extend(codex_sessions)

    discover_claude_projects = (
        args.projects_only and not args.project
    ) or "claude-code" in providers
    if discover_claude_projects:
        source_status["claude-code"] = "ok" if claude_home.is_dir() else "missing"
        if source_status["claude-code"] != "ok":
            warnings.append(f"{claude_home}: Claude Code home is missing")
        claude_sessions = scan_claude(
            claude_home,
            args.claude_branches,
            mappings,
            selected,
            True,
            resume_links,
            warnings,
        )
        if not args.projects_only and "claude-code" in providers:
            sessions.extend(claude_sessions)
        elif args.projects_only:
            project_discovery_sessions.extend(claude_sessions)

    sessions_by_import_id: dict[str, list[dict[str, Any]]] = {}
    for session in sessions:
        sessions_by_import_id.setdefault(
            str(session.get("native_import_id")), []
        ).append(session)
    duplicate_import_ids = sorted(
        import_id
        for import_id, matches in sessions_by_import_id.items()
        if len(matches) > 1
    )
    for import_id in duplicate_import_ids:
        warnings.append(f"duplicate planned session identity: {import_id}")
        for session in sessions_by_import_id[import_id]:
            session["import_id_conflict"] = True
            session["source_ready"] = False

    unmatched_session_selectors: list[str] = []
    ambiguous_session_selectors: list[str] = []
    if args.session:
        selected_sessions: list[dict[str, Any]] = []
        selected_import_ids: set[str] = set()
        for selector in dict.fromkeys(args.session):
            matches = [
                session
                for session in sessions
                if session.get("native_session_id") == selector
                or session.get("native_import_id") == selector
            ]
            if not matches:
                unmatched_session_selectors.append(selector)
                warnings.append(f"session selector did not match: {selector}")
            elif len(matches) > 1:
                ambiguous_session_selectors.append(selector)
                warnings.append(f"session selector is ambiguous: {selector}")
            else:
                import_id = str(matches[0].get("native_import_id"))
                if import_id not in selected_import_ids:
                    selected_sessions.append(matches[0])
                    selected_import_ids.add(import_id)
        sessions = selected_sessions
        project_hints = []

    existing, target_inventory_status = existing_t3_projects(
        args.t3_home.expanduser(), warnings
    )
    projects = assemble_projects(
        project_discovery_sessions if args.projects_only else sessions,
        project_hints,
        args.project,
        mappings,
        existing,
        target_inventory_ok=target_inventory_status == "ok",
    )
    for session in sessions:
        session["destination_action"] = "blocked-capability-unverified"
    skipped_sessions = sum(1 for session in sessions if not session.get("source_ready"))
    plan: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": {
            "projects_only": bool(args.projects_only),
            "providers": providers,
            "include_archived": bool(args.include_archived),
            "claude_branches": args.claude_branches,
            "resume_links": resume_links,
            "content_hashes": True,
        },
        "source_homes": {
            "codex": {
                "path": str(codex_home.absolute()),
                "inventory_status": source_status["codex"],
            },
            "claude_code": {
                "path": str(claude_home.absolute()),
                "inventory_status": source_status["claude-code"],
            },
        },
        "target": {
            "t3_home": str(args.t3_home.expanduser().absolute()),
            "detected_version": t3_version(),
            "project_inventory_status": target_inventory_status,
            "historical_import_capability": "unverified",
            "planner_mutates_state": False,
            "exact_apply_plan": False,
        },
        "path_maps": [
            {"source": str(mapping.source), "target": str(mapping.target)}
            for mapping in mappings
        ],
        "selection": {
            "requested_session_ids": list(dict.fromkeys(args.session)),
            "unmatched_session_ids": unmatched_session_selectors,
            "ambiguous_session_ids": ambiguous_session_selectors,
        },
        "projects": projects,
        "sessions": sorted(sessions, key=session_sort_key),
        "summary": {
            "projects": len(projects),
            "projects_to_create": sum(
                1 for project in projects if project["action"] == "create"
            ),
            "projects_to_reuse": sum(
                1 for project in projects if project["action"] == "reuse"
            ),
            "projects_missing": sum(
                1 for project in projects if project["action"] == "skip-missing"
            ),
            "projects_blocked": sum(
                1
                for project in projects
                if project["action"] == "blocked-target-unavailable"
            ),
            "sessions": len(sessions),
            "sessions_blocked": len(sessions),
            "duplicate_session_identities": len(duplicate_import_ids),
            "selection_issues": len(unmatched_session_selectors)
            + len(ambiguous_session_selectors),
            "source_stores_missing": sum(
                1 for status in source_status.values() if status == "missing"
            ),
            "sessions_source_not_ready": skipped_sessions,
            "messages": sum(
                int(session.get("message_count") or 0) for session in sessions
            ),
            "activities": sum(
                int(session.get("activity_count") or 0) for session in sessions
            ),
            "attachments": sum(
                int(session.get("attachment_count") or 0) for session in sessions
            ),
            "unsupported_subagents": sum(
                int(session.get("subagent_count") or 0) for session in sessions
            ),
            "resume_candidates": sum(
                1 for session in sessions if session.get("resume", {}).get("candidate")
            ),
            "claude_incomplete_chains": sum(
                1
                for session in sessions
                if session.get("provider") == "claude-code"
                and not session.get("branch_chain_complete")
            ),
            "parse_errors": sum(
                int(session.get("parse_error_count") or 0) for session in sessions
            ),
        },
        "warnings": sorted(set(warnings)),
    }
    plan["plan_hash"] = plan_hash(plan)
    write_plan(plan, args.output, args.compact)
    if args.output:
        print(
            f"Wrote private migration plan to {args.output.expanduser().absolute()} "
            f"with hash {plan['plan_hash']}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
