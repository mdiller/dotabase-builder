# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**dotabase-builder** is an ETL pipeline that extracts Dota 2 game data from VPK files, transforms it, and loads it into the `dotabase` SQLite database (in the sibling `../dotabase/` project). It also exports JSON snapshots of all tables.

## Commands

**Full build (all components):**
```sh
python builder.py
```

**Build a single component:**
```sh
python builder.py abilities
python builder.py heroes
# Valid names: chat_wheel, emoticons, items, facets, abilities, heroes, talents, voices, responses, loadingscreens, patches
```

**VPK extraction (prerequisite — run when Dota 2 updates):**
```sh
bash scripts/extract.sh
```

**Debug configurations** for individual components are in `.vscode/launch.json`.

## Configuration

`config.json` (not committed) must exist at the repo root:
```json
{
  "vpk_path": "F:\\dota_vpk",
  "vpk_destination": "F:\\dota_vpk",
  "dota_path": "X:\\...\\dota 2 beta",
  "overwrite_db": true,
  "overwrite_json": false
}
```

- `overwrite_json: false` — reuse cached intermediate JSON from `jsoncache/` (faster)
- `overwrite_db: true` — wipe and recreate the database

## Architecture & Data Flow

```
Dota 2 VPK Files
    ↓  scripts/extract.sh  (ValveResourceFormat decompiler)
Extracted text/binary files  (vpk_path)
    ↓  valve2json.py  (converts Valve KV/KV3/rules → JSON, cached in jsoncache/)
Parsed JSON objects
    ↓  builder_parts/*.py  (transform and load)
dotabase.db  (SQLite via SQLAlchemy)
    ↓  generate_json.py
json/ export files
```

**builder.py** is the orchestrator. It initializes the DB session and calls each `builder_parts` module's `load()` function in dependency order: chat_wheel → emoticons → items → facets → abilities → heroes → talents → voices → responses → loadingscreens → patches.

## Key Files

| File | Role |
|------|------|
| `builder.py` | Entry point; orchestrates all parts |
| `valve2json.py` | Converts Valve file formats to JSON; defines `DotaFiles` (central file registry) and `DotaPaths` (image/script dirs); lazy-loads and caches files |
| `utils.py` | Ability special parsing, value math, text cleaning, `Config`, `ProgressBar` |
| `generate_json.py` | Exports DB tables to `../dotabase/json/` |
| `builder_parts/` | One module per entity type, each with a `load(session, files, ...)` function |
| `builderdata/` | Hand-curated JSON enrichment files (aliases, colors, voice actors, etc.) |

## ORM Models

The SQLAlchemy models live in `../dotabase/dotabase/dotabase.py`. Key models: `Hero`, `Ability`, `Talent`, `Facet`, `Item`, `Voice`, `Response`, `Criterion`, `ChatWheelMessage`, `Emoticon`, `LoadingScreen`, `Patch`, `LocaleString`.

## Notable Patterns

- **JSON caching:** VPK files are parsed once and cached in `jsoncache/`; delete cache or set `overwrite_json: true` to re-parse.
- **`CaseInsensitiveDict`:** Used throughout because Valve's file formats have inconsistent casing.
- **`LocaleString` table:** Generic multi-language support — linked by `table` + `row_id`, not foreign keys.
- **`json_data` columns:** Raw JSON stored in DB for flexibility beyond the fixed schema.
- **ProgressBar + error collection:** Batch operations collect errors and report at the end rather than failing immediately.
