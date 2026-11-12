# -*- coding: utf-8 -*-
"""Book-Meal World Contract v0.1: read-only interoperability envelope.

The AI-Persona Human Ontology v2 remains the authority for human semantics.
This module does NOT define another human ontology or infer real psychology.
No LLM, network, or third-party dependency is required.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

VERSION = "0.1.0"
HUMAN_ONTOLOGY_VERSION = "2.0.0"
EPISTEMIC = {"BOOK", "INFER", "EXT", "SIM", "UNKNOWN"}
RECORD_TYPES = ("persons", "places", "entities", "events", "relations", "evidence", "states", "experiments")
ENTITY_TYPES = ("persons", "places", "entities")
ONTOLOGY_URI = "https://github.com/CochraneK/AI-persona/blob/main/ontology/human_ontology.v2.json"


def stable_id(kind: str, world_key: str, source_key: object) -> str:
    """Namespaced, deterministic identity; never depend on list position alone."""
    if not kind or not world_key or not str(source_key):
        raise ValueError("id requires a non-empty kind, world, and source key")
    raw = json.dumps([kind, world_key, str(source_key)], ensure_ascii=False, separators=(",", ":"))
    return kind + ":" + world_key + ":" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def base_world(book_id: str, title: str, author: str, source_repo: str) -> dict:
    if not book_id or not title or not source_repo:
        raise ValueError("book id/title/source repo required")
    data = {
        "schema_version": VERSION,
        "book": {"id": "book:" + book_id, "title": title, "author": author, "source_repository": source_repo},
        "world": {"id": "world:" + book_id, "book_id": "book:" + book_id, "parent_world_id": None},
        "persons": [], "places": [], "entities": [], "events": [], "relations": [],
        "evidence": [], "states": [], "experiments": [],
        "audit": {"warnings": [], "unresolved_endpoints": [], "source_counts": {}},
        "extensions": {},
    }
    return data


def add_evidence(world: dict, record_id: str, *, kind: str, repo: str,
                 path: str, native_id: str, chapters=(), note: str = "") -> str:
    if kind not in EPISTEMIC:
        raise ValueError("unknown epistemic type: " + kind)
    evidence_id = stable_id("evidence", world["book"]["id"].removeprefix("book:"), record_id)
    record = {
        "id": evidence_id, "for_id": record_id, "kind": kind,
        "source": {"repository": repo, "path": path, "native_id": str(native_id),
                   "chapters": list(dict.fromkeys(str(x) for x in (chapters or []) if x is not None and str(x)))},
    }
    if note:
        record["note"] = note
    world["evidence"].append(record)
    return evidence_id


def unresolved_entity(world: dict, native_id: object, *, source_path: str,
                      expected_kind: str = "unknown") -> str:
    """Retain broken references without inventing additional people or places."""
    label = str(native_id)
    wid = world["book"]["id"].removeprefix("book:")
    item_id = stable_id("entity", wid, "unresolved|" + label)
    if not any(r["id"] == item_id for r in world["entities"]):
        source = world["book"]["source_repository"]
        evid = add_evidence(world, item_id, kind="UNKNOWN", repo=source, path=source_path,
                            native_id=label)
        world["entities"].append({
            "id": item_id, "name": label, "kind": "unresolved_" + expected_kind,
            "status": "unresolved", "evidence_ids": [evid], "source_id": label,
        })
        world["audit"]["unresolved_endpoints"].append({
            "source_id": label, "expected_kind": expected_kind, "source_path": source_path,
        })
    return item_id


def validate_world(world: dict) -> list[str]:
    """Validate shape, identity, time bounds, evidence refs and graph endpoints."""
    errors = []
    if world.get("schema_version") != VERSION:
        errors.append("incompatible schema_version")
    book = world.get("book") or {}
    root = world.get("world") or {}
    if not book.get("id") or root.get("book_id") != book.get("id") or not root.get("id"):
        errors.append("book/world identity mismatch")
    for key in RECORD_TYPES:
        if not isinstance(world.get(key), list):
            errors.append(key + " is not a list")
    if errors:
        return errors
    records = [row for key in RECORD_TYPES for row in world[key]]
    all_ids = [r.get("id") for r in records]
    if len(set(all_ids)) != len(all_ids):
        errors.append("duplicate record IDs")
    if any(not isinstance(x, str) or not x for x in all_ids):
        errors.append("empty or invalid ID")
    ids = set(all_ids)
    nodes = {r["id"] for key in ENTITY_TYPES for r in world[key] if isinstance(r.get("id"), str)}
    evidence_ids = {r["id"] for r in world["evidence"] if isinstance(r.get("id"), str)}
    for key in ("persons", "places", "entities", "events", "relations"):
        for row in world[key]:
            if not row.get("source_id"):
                errors.append(key + ": missing source_id " + str(row.get("id")))
            refs = row.get("evidence_ids")
            if not isinstance(refs, list) or not refs or not set(refs) <= evidence_ids:
                errors.append(key + ": missing/dangling evidence " + str(row.get("id")))
    for row in world["persons"]:
        if row.get("ontology_version") != HUMAN_ONTOLOGY_VERSION:
            errors.append("person ontology mismatch: " + str(row.get("id")))
    for row in world["evidence"]:
        source = row.get("source") or {}
        if row.get("kind") not in EPISTEMIC or row.get("for_id") not in ids:
            errors.append("evidence kind/target invalid: " + str(row.get("id")))
        if not all(source.get(k) for k in ("repository", "path", "native_id")):
            errors.append("evidence missing provenance: " + str(row.get("id")))
        if not isinstance(source.get("chapters"), list):
            errors.append("evidence chapters not a list: " + str(row.get("id")))
    for row in world["relations"]:
        if row.get("from_id") not in nodes or row.get("to_id") not in nodes:
            errors.append("relation dangling endpoint: " + str(row.get("id")))
        if not row.get("predicate"):
            errors.append("relation missing predicate: " + str(row.get("id")))
    for row in world["events"]:
        if any(x not in nodes for x in row.get("participants", [])):
            errors.append("event dangling participant: " + str(row.get("id")))
        bounds = row.get("time") or {}
        lo, hi = bounds.get("year_start"), bounds.get("year_end")
        if lo is not None and (not isinstance(lo, int) or isinstance(lo, bool)):
            errors.append("invalid start year: " + str(row.get("id")))
        if hi is not None and (not isinstance(hi, int) or isinstance(hi, bool)):
            errors.append("invalid end year: " + str(row.get("id")))
        if isinstance(lo, int) and isinstance(hi, int) and lo > hi:
            errors.append("reversed year bounds: " + str(row.get("id")))
    return errors


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(world: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(world, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
