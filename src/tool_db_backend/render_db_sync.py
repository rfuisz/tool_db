import os
import shutil
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import psycopg

from tool_db_backend.config import Settings
from tool_db_backend.db_migrations import MigrationRunner


class RenderDbSyncError(RuntimeError):
    pass


def get_database_import_preflight(settings: Settings) -> Dict[str, Any]:
    if not settings.database_url:
        raise RenderDbSyncError("DATABASE_URL must point at the target database.")

    return {
        "status": "ready",
        "message": "Hosted database import endpoint is ready.",
        "render_database_source": "current_database",
        "render_database": {
            "postgres_id": None,
            "postgres_name": None,
            "display_url": _build_display_database_url(settings.database_url),
        },
        "target_summary": _read_database_summary(settings.database_url),
    }


def import_sql_dump_into_database(settings: Settings, sql_dump: str) -> Dict[str, Any]:
    if not settings.database_url:
        raise RenderDbSyncError("DATABASE_URL must point at the target database.")

    normalized_dump = sql_dump.strip()
    if not normalized_dump:
        raise RenderDbSyncError("The uploaded SQL dump is empty.")

    MigrationRunner(settings).apply_all()
    started_at = time.time()
    target_before_summary = _read_database_summary(settings.database_url)
    truncate_statement = _build_truncate_statement(settings.database_url)
    table_count = truncate_statement.count('", "') + 1 if truncate_statement else 0

    with psycopg.connect(_normalize_database_url_for_connection(settings.database_url)) as conn:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(truncate_statement)
                cursor.execute(normalized_dump)
                cursor.execute("ANALYZE;")

    target_after_summary = _read_database_summary(settings.database_url)
    duration_seconds = round(time.time() - started_at, 2)
    return {
        "status": "success",
        "message": "Hosted Postgres was overwritten from the uploaded local database dump.",
        "duration_seconds": duration_seconds,
        "table_count": table_count,
        "render_database_source": "current_database",
        "render_database": {
            "postgres_id": None,
            "postgres_name": None,
            "display_url": _build_display_database_url(settings.database_url),
        },
        "target_before_summary": target_before_summary,
        "target_after_summary": target_after_summary,
    }


def get_render_database_sync_preflight(settings: Settings) -> Dict[str, Any]:
    if not settings.database_url:
        raise RenderDbSyncError("DATABASE_URL must point at the local source database.")

    target = _resolve_render_database_target(settings)
    if settings.database_url.strip() == target["database_url"].strip():
        raise RenderDbSyncError("DATABASE_URL and RENDER_DATABASE_URL must not be identical.")

    return {
        "status": "ready",
        "message": "Render DB sync target resolved successfully.",
        "render_database_source": target["source"],
        "render_database": {
            "postgres_id": target.get("postgres_id"),
            "postgres_name": target.get("postgres_name"),
            "display_url": _build_display_database_url(target["database_url"]),
        },
        "source_summary": _read_database_summary(settings.database_url),
        "target_summary": _read_database_summary(target["database_url"]),
    }


def sync_render_database(settings: Settings) -> Dict[str, Any]:
    if not settings.database_url:
        raise RenderDbSyncError("DATABASE_URL must point at the local source database.")
    target = _resolve_render_database_target(settings)
    render_database_url = _normalize_database_url_for_connection(target["database_url"])
    if settings.database_url.strip() == render_database_url.strip():
        raise RenderDbSyncError("DATABASE_URL and RENDER_DATABASE_URL must not be identical.")

    pg_dump = shutil.which("pg_dump")
    psql = shutil.which("psql")
    if not pg_dump or not psql:
        raise RenderDbSyncError("Both pg_dump and psql must be installed to sync databases.")

    started_at = time.time()
    source_summary = _read_database_summary(settings.database_url)
    target_before_summary = _read_database_summary(render_database_url)
    truncate_statement = _build_truncate_statement(render_database_url)
    table_count = truncate_statement.count('", "') + 1 if truncate_statement else 0

    with tempfile.TemporaryDirectory(prefix="tool-db-render-sync-") as temp_dir:
        temp_root = Path(temp_dir)
        dump_path = temp_root / "local-data.sql"
        sync_path = temp_root / "render-sync.sql"

        _run_command(
            [
                pg_dump,
                "--data-only",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                settings.database_url,
                "--file",
                str(dump_path),
            ],
            "pg_dump local database",
        )

        sync_path.write_text(
            "-- Overwrite hosted Render database from local Postgres.\n"
            f"{truncate_statement}\n"
            f"{dump_path.read_text()}\n"
            "ANALYZE;\n"
        )

        _run_command(
            [
                psql,
                "--set",
                "ON_ERROR_STOP=1",
                "--single-transaction",
                "--dbname",
                render_database_url,
                "--file",
                str(sync_path),
            ],
            "psql restore into Render database",
        )

    target_after_summary = _read_database_summary(render_database_url)
    duration_seconds = round(time.time() - started_at, 2)
    return {
        "status": "success",
        "message": "Hosted Render Postgres was overwritten from the local Postgres database.",
        "duration_seconds": duration_seconds,
        "table_count": table_count,
        "render_database_source": target["source"],
        "render_database": {
            "postgres_id": target.get("postgres_id"),
            "postgres_name": target.get("postgres_name"),
            "display_url": _build_display_database_url(render_database_url),
        },
        "source_summary": source_summary,
        "target_before_summary": target_before_summary,
        "target_after_summary": target_after_summary,
    }


def _resolve_render_database_target(settings: Settings) -> Dict[str, Any]:
    if settings.render_database_url:
        return {
            "database_url": settings.render_database_url,
            "source": "direct_env",
            "postgres_id": settings.render_postgres_id.strip() or None,
            "postgres_name": settings.render_postgres_name.strip() or None,
        }
    if not settings.render_api_key:
        raise RenderDbSyncError(
            "Set RENDER_DATABASE_URL directly, or provide RENDER_API_KEY plus RENDER_POSTGRES_ID/RENDER_POSTGRES_NAME."
        )

    postgres = _resolve_render_postgres(settings)
    postgres_id = postgres["id"]
    connection_info = _render_api_get(
        f"https://api.render.com/v1/postgres/{postgres_id}/connection-info",
        settings.render_api_key,
    )
    connection_string = (
        connection_info.get("externalConnectionString")
        or connection_info.get("connectionString")
        or connection_info.get("external_connection_string")
    )
    if not connection_string:
        raise RenderDbSyncError("Render API did not return an external Postgres connection string.")
    return {
        "database_url": str(connection_string),
        "source": "render_api",
        "postgres_id": postgres_id,
        "postgres_name": postgres.get("name"),
    }


def _resolve_render_postgres(settings: Settings) -> Dict[str, str]:
    postgres_name = settings.render_postgres_name.strip()
    payload = _render_api_get("https://api.render.com/v1/postgres", settings.render_api_key)
    candidates = _coerce_items(payload)
    explicit_id = settings.render_postgres_id.strip()
    if explicit_id:
        for candidate in candidates:
            candidate_id = str(candidate.get("id") or "").strip()
            if candidate_id == explicit_id:
                return {
                    "id": candidate_id,
                    "name": str(candidate.get("name") or "").strip() or None,
                }
        return {"id": explicit_id, "name": postgres_name or None}
    for candidate in candidates:
        candidate_name = str(candidate.get("name") or "").strip()
        if candidate_name == postgres_name:
            postgres_id = str(candidate.get("id") or "").strip()
            if postgres_id:
                return {"id": postgres_id, "name": candidate_name}
    raise RenderDbSyncError(f"Could not find a Render Postgres instance named '{postgres_name}'.")


def _coerce_items(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [_unwrap_render_resource(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "postgres", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [_unwrap_render_resource(item) for item in value if isinstance(item, dict)]
        return [_unwrap_render_resource(payload)]
    return []


def _unwrap_render_resource(payload: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("postgres", "service"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return payload


def _render_api_get(url: str, api_key: str) -> Dict[str, Any]:
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "tool-db-render-sync",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        raise RenderDbSyncError(f"Render API request failed: {exc.code} {body}") from exc
    except URLError as exc:
        raise RenderDbSyncError(f"Render API request failed: {exc.reason}") from exc

    if not isinstance(payload, dict) and not isinstance(payload, list):
        raise RenderDbSyncError("Render API returned an unexpected response body.")
    return payload


def _build_display_database_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path.lstrip("/") or "unknown-db"
    return f"{host}{port}/{database}"


def _read_database_summary(database_url: str) -> Dict[str, int]:
    with psycopg.connect(_normalize_database_url_for_connection(database_url)) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select count(*) from toolkit_item")
            toolkit_item_count = int(cursor.fetchone()[0])
            cursor.execute(
                """
                select count(distinct slug)
                from extracted_item_candidate
                where candidate_type = 'toolkit_item'
                """
            )
            first_pass_slug_count = int(cursor.fetchone()[0])
    return {
        "toolkit_item_count": toolkit_item_count,
        "first_pass_distinct_slug_count": first_pass_slug_count,
    }


def _build_truncate_statement(database_url: str) -> str:
    with psycopg.connect(_normalize_database_url_for_connection(database_url)) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                  and table_type = 'BASE TABLE'
                order by table_name asc
                """
            )
            table_names = [row[0] for row in cursor.fetchall()]
    if not table_names:
        raise RenderDbSyncError("Render database has no public tables to sync.")

    quoted_tables = ", ".join(_quote_identifier(table_name) for table_name in table_names)
    return f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE;"


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _normalize_database_url_for_connection(database_url: str) -> str:
    parsed = urlparse(database_url)
    if not parsed.hostname or "render.com" not in parsed.hostname:
        return database_url

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if query.get("sslmode"):
        return database_url

    query["sslmode"] = "require"
    return urlunparse(parsed._replace(query=urlencode(query)))


def _run_command(command: List[str], description: str) -> None:
    env = os.environ.copy()
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if completed.returncode == 0:
        return

    stderr = (completed.stderr or "").strip()
    stdout = (completed.stdout or "").strip()
    output = stderr or stdout or f"{description} failed with exit code {completed.returncode}."
    raise RenderDbSyncError(output)
