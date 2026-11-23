#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist"
PUBLIC_FILES = ["index.html", "styles.css", "app.js"]


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    for filename in PUBLIC_FILES:
        shutil.copy2(ROOT / filename, OUTPUT / filename)

    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if supabase_url and supabase_anon_key:
        config = {"supabaseUrl": supabase_url, "supabaseAnonKey": supabase_anon_key}
        (OUTPUT / "config.js").write_text(
            "window.SHIYE_CONFIG = "
            + json.dumps(config, ensure_ascii=False, indent=2)
            + ";\n",
            encoding="utf-8",
        )
    else:
        shutil.copy2(ROOT / "config.js", OUTPUT / "config.js")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    main()

