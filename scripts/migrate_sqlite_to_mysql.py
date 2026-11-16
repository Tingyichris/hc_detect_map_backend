"""Replace a migrated MySQL database's application data from the dev SQLite DB."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import MetaData, create_engine, select, text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    source_path = args.source.resolve()
    if not source_path.is_file():
        raise SystemExit(f"SQLite source not found: {source_path}")

    source = create_engine(f"sqlite:///{source_path.as_posix()}")
    target = create_engine(args.target)
    source_meta = MetaData()
    target_meta = MetaData()
    source_meta.reflect(bind=source)
    target_meta.reflect(bind=target)

    table_names = sorted(
        (set(source_meta.tables) & set(target_meta.tables)) - {"alembic_version"}
    )
    if not table_names:
        raise SystemExit("No common application tables found")

    rows_by_table: dict[str, list[dict]] = {}
    with source.connect() as connection:
        for name in table_names:
            rows_by_table[name] = []
            for row in connection.execute(
                select(source_meta.tables[name])
            ).mappings():
                converted = {
                    key: json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
                rows_by_table[name].append(converted)

    with target.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        try:
            for name in reversed(table_names):
                connection.execute(target_meta.tables[name].delete())
            for name in table_names:
                rows = rows_by_table[name]
                if rows:
                    connection.execute(target_meta.tables[name].insert(), rows)
        finally:
            connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    with target.connect() as connection:
        for name in table_names:
            count = connection.execute(
                select(text("count(*)")).select_from(target_meta.tables[name])
            ).scalar_one()
            expected = len(rows_by_table[name])
            if count != expected:
                raise SystemExit(f"Count mismatch for {name}: {count} != {expected}")
            print(f"{name}: {count}")


if __name__ == "__main__":
    main()
