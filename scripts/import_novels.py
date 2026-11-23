#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_CSV = (
    Path(__file__).resolve().parents[3]
    / "work"
    / "novels_import.csv"
)
RUNTIME_FILE = Path(__file__).resolve().parents[3] / "work" / "supabase_runtime.json"


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"缺少环境变量 {name}")
    return value


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def build_record(row: dict) -> dict:
    aliases = parse_list(row.get("aliases", ""))
    characters = parse_list(row.get("characters", ""))
    search_text = " ".join(
        [
            row.get("title", ""),
            row.get("author", ""),
            row.get("category", ""),
            row.get("status", ""),
            row.get("latest_chapter", ""),
            row.get("character_candidates", ""),
            row.get("chapter_titles", "")[:500],
            row.get("synopsis", ""),
            row.get("travel_evidence", ""),
            " ".join(aliases),
            " ".join(characters),
        ]
    ).strip()
    return {
        "source_seq": int(row["source_seq"]),
        "title": row.get("title", "").strip(),
        "author": row.get("author", "").strip(),
        "category": row.get("category", "").strip(),
        "status": row.get("status", "").strip(),
        "source_updated_at": row.get("source_updated_at") or None,
        "latest_chapter": row.get("latest_chapter", ""),
        "character_candidates": row.get("character_candidates", ""),
        "characters": characters,
        "fetched_chapter_count": int(row.get("fetched_chapter_count") or 0),
        "chapter_titles": row.get("chapter_titles", ""),
        "synopsis": row.get("synopsis", ""),
        "travel_evidence": row.get("travel_evidence", ""),
        "source_url": row.get("source_url", ""),
        "source_name": "香书小说公开页面",
        "aliases": aliases,
        "search_text": search_text,
    }


def post_batch(base_url: str, service_key: str, batch: list[dict]) -> None:
    query = urllib.parse.urlencode({"on_conflict": "source_seq"})
    url = f"{base_url.rstrip('/')}/rest/v1/novels?{query}"
    request = urllib.request.Request(
        url,
        data=json.dumps(batch, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status not in (200, 201, 204):
                raise RuntimeError(f"Supabase returned HTTP {response.status}")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Supabase HTTP {error.code}: {detail}") from error


def main() -> None:
    parser = argparse.ArgumentParser(description="导入小说数据到 Supabase")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    runtime = {}
    if RUNTIME_FILE.exists():
        runtime = json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
    supabase_url = os.environ.get("SUPABASE_URL", "").strip() or runtime.get("project_url", "")
    service_key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or runtime.get("service_role_key", "")
    )
    if not supabase_url or not service_key:
        sys.exit("缺少 SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY")
    if not args.csv.exists():
        sys.exit(f"找不到导入文件：{args.csv}")

    with args.csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [build_record(row) for row in csv.DictReader(handle)]
    if args.limit:
        rows = rows[: args.limit]

    for start in range(0, len(rows), args.batch_size):
        batch = rows[start : start + args.batch_size]
        post_batch(supabase_url, service_key, batch)
        print(f"已导入 {min(start + len(batch), len(rows))}/{len(rows)}")

    print(f"完成：{len(rows)} 本小说已写入 Supabase")


if __name__ == "__main__":
    main()

