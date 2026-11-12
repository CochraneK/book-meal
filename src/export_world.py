# -*- coding: utf-8 -*-
"""Validate / explicitly export a versioned world from legacy sources.

Examples:
  python src/export_world.py --book ming --check-only
  python src/export_world.py --book sanggan --source-root /local/private/sanggan --check-only
  python src/export_world.py --book ming --output /tmp/ming-world.json

The default is --check-only. Private Sanggan exports are REFUSED under the
public Book-Meal checkout; no network or source mutation occurs.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from world_contract import dump_json, load_json, validate_world
from world_adapters import ming, sanggan

ROOT = Path(__file__).resolve().parents[1]


def assert_safe_output(book: str, output: Path) -> None:
    if book == "sanggan" and output.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Private Sanggan world export may not be written inside public Book-Meal")


def build(book: str, source_root: Path | None = None) -> dict:
    if book == "ming":
        source = load_json(ROOT / "data/data.json")
        manifest = load_json(ROOT / "books/ming/manifest.json")
        return ming.adapt(source, manifest)
    if book == "sanggan":
        if source_root is None:
            raise ValueError("Sanggan requires --source-root pointing to an authorized private checkout")
        return sanggan.adapt(sanggan.read_source(source_root))
    raise ValueError("unknown book")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="World Contract v0.1 read-only adapter validation")
    parser.add_argument("--book", choices=("ming", "sanggan"), required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-only", action="store_true", help="validate only (default when no --output)")
    args = parser.parse_args(argv)
    if args.output and args.check_only:
        parser.error("--output and --check-only are mutually exclusive")
    if args.output:
        assert_safe_output(args.book, args.output)
    world = build(args.book, args.source_root)
    errors = validate_world(world)
    summary = {
        "book": args.book,
        "persons": len(world["persons"]), "places": len(world["places"]),
        "other_entities": len(world["entities"]), "events": len(world["events"]),
        "relations": len(world["relations"]), "evidence": len(world["evidence"]),
        "unresolved": len(world["audit"]["unresolved_endpoints"]),
        "warnings": len(world["audit"]["warnings"]), "errors": len(errors),
    }
    print(summary)
    for error in errors[:20]:
        print("ERROR:", error)
    if errors:
        return 1
    if args.output:
        dump_json(world, args.output)
        print("Exported to", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
