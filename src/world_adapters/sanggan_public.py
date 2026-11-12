# -*- coding: utf-8 -*-
"""Read-only PUBLIC Sanggan report -> shared Book-Meal World Contract.

Consumes ONLY the already-published Book-Meal books/sanggan/index.html.
This is a small public projection. Do not copy private Sanggan kernels,
SecondMe dossiers, full OCR text or unpublished annotations into the site.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from world_contract import (
    HUMAN_ONTOLOGY_VERSION, ONTOLOGY_URI, add_evidence, base_world,
    stable_id, unresolved_entity,
)

SOURCE_PATH = "books/sanggan/index.html"
SOURCE_REPO = "CochraneK/book-meal"
DATA_PATTERN = re.compile(r"(?m)^\s*const\s+DATA\s*=\s*")


def extract_report_data(html: str) -> dict:
    """Parse exactly one literal JSON assignment, never evaluate JS."""
    found = list(DATA_PATTERN.finditer(html))
    if len(found) != 1:
        raise ValueError("expected one public DATA JSON assignment")
    start = found[0].end()
    try:
        data, consumed = json.JSONDecoder().raw_decode(html[start:])
    except ValueError as exc:
        raise ValueError("public DATA must be JSON, not executable JS") from exc
    if not html[start + consumed:].lstrip().startswith(";"):
        raise ValueError("public DATA assignment must end with a semicolon")
    if not isinstance(data, dict):
        raise ValueError("public DATA must be an object")
    for key in ("characters", "events", "relations"):
        if not isinstance(data.get(key), list):
            raise ValueError("missing public DATA list: " + key)
    return data


def read_public_report(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return extract_report_data(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def adapt(source: dict, *, title: str = "太阳照在桑乾河上",
          author: str = "丁玲", source_sha256: str = "") -> dict:
    world = base_world("sanggan", title, author, SOURCE_REPO)
    people, places = {}, {}
    source_persons = source.get("characters") or []
    source_events = source.get("events") or []
    source_relations = source.get("relations") or []

    for person in source_persons:
        native = str(person.get("id") or "").strip()
        name = str(person.get("name") or "").strip()
        if not native or not name or name in people:
            world["audit"]["warnings"].append("incomplete/duplicate public character")
            continue
        pid = stable_id("person", "sanggan", native)
        people[name] = pid
        chapter = person.get("first_chapter")
        has_chapter = type(chapter) is int and chapter > 0
        eid = add_evidence(
            world, pid, kind="BOOK" if has_chapter else "UNKNOWN",
            repo=SOURCE_REPO, path=SOURCE_PATH, native_id=native,
            chapters=[f"第{chapter}章"] if has_chapter else [],
            note="Existing public report index; original text not independently checked",
        )
        world["persons"].append({
            "id": pid, "source_id": native, "name": name,
            "ontology_version": HUMAN_ONTOLOGY_VERSION, "ontology_ref": ONTOLOGY_URI,
            "aliases": [], "roles": [str(person["role_in_book"])] if person.get("role_in_book") else [],
            "evidence_ids": [eid],
            "extensions": {"sanggan_public": {"first_chapter": chapter if has_chapter else None}},
        })

    # Only the 15 schematic places already published in the scene diagram,
    # NOT the 41-place private index or verified geolocation.
    scene_places = (source.get("scene") or {}).get("places") or []
    for place in scene_places:
        native, name = str(place.get("id") or "").strip(), str(place.get("name") or "").strip()
        if not native or not name or name in places:
            world["audit"]["warnings"].append("incomplete/duplicate schematic place")
            continue
        lid = stable_id("place", "sanggan", "public-scene:" + native)
        places[name] = lid
        evid = add_evidence(
            world, lid, kind="INFER", repo=SOURCE_REPO, path=SOURCE_PATH,
            native_id="public-scene:" + native,
            note="Existing public schematic scene; not a verified map",
        )
        world["places"].append({
            "id": lid, "source_id": native, "name": name,
            "kind": "schematic_place", "evidence_ids": [evid],
        })

    def endpoint(value, *, expected_kind, source_part):
        name = str(value or "").strip()
        if name in people:
            return people[name]
        if name in places:
            return places[name]
        return unresolved_entity(
            world, name or "(missing)", source_path=SOURCE_PATH + "#" + source_part,
            expected_kind=str(expected_kind),
        )

    for event in source_events:
        native = str(event.get("id") or "").strip()
        if not native:
            world["audit"]["warnings"].append("public event without ID")
            continue
        eid = stable_id("event", "sanggan", native)
        chapter = event.get("chapter")
        has_chapter = type(chapter) is int and chapter > 0
        evid = add_evidence(
            world, eid, kind="BOOK" if has_chapter else "UNKNOWN",
            repo=SOURCE_REPO, path=SOURCE_PATH, native_id=native,
            chapters=[f"第{chapter}章"] if has_chapter else [],
            note="Existing published event summary, not source-text reverified",
        )
        world["events"].append({
            "id": eid, "source_id": native,
            "name": str(event.get("summary") or native),
            "participants": [
                endpoint(x, expected_kind="person", source_part="DATA.events")
                for x in (event.get("actors") or []) if x
            ],
            "time": {
                "year_start": None, "year_end": None,
                "label": str(event.get("time") or "") or None,
                "chapter": chapter if has_chapter else None,
            },
            "evidence_ids": [evid],
            "extensions": {"sanggan_public": {"narrative_time": True}},
        })

    for rel in source_relations:
        native = str(rel.get("id") or "").strip()
        if not native:
            world["audit"]["warnings"].append("public relation without ID")
            continue
        rid = stable_id("relation", "sanggan", native)
        typ = rel.get("source_type")
        kind = "INFER" if typ == "inferred" else "BOOK" if typ == "observed" else "UNKNOWN"
        evid = add_evidence(
            world, rid, kind=kind, repo=SOURCE_REPO,
            path=SOURCE_PATH, native_id=native,
            note="Published relation classification; no original quote copied",
        )
        world["relations"].append({
            "id": rid, "source_id": native,
            "from_id": endpoint(rel.get("from"), expected_kind=rel.get("from_type") or "unknown",
                                source_part="DATA.relations"),
            "to_id": endpoint(rel.get("to"), expected_kind=rel.get("to_type") or "unknown",
                              source_part="DATA.relations"),
            "predicate": str(rel.get("pred_zh") or rel.get("pred") or "related_to"),
            "canonical_path": None, "evidence_ids": [evid],
            "extensions": {"sanggan_public": {
                "original_predicate": str(rel.get("pred") or ""),
                "source_type": typ,
            }},
        })

    counts = {
        "persons": len(source_persons), "events": len(source_events),
        "relations": len(source_relations), "schematic_places": len(scene_places),
    }
    world["audit"]["source_counts"] = counts
    world["extensions"]["sanggan_public"] = {
        "source": "already published books/sanggan/index.html DATA",
        "source_sha256": source_sha256,
        "only_public_index_fields": True,
        "private_persona_kernels_included": False,
        "private_place_index_included": False,
        "not_original_text_verified": True,
    }
    declared = (source.get("disclosure") or {}).get("counts") or {}
    for src_key, key in (("characters", "persons"), ("events", "events"), ("relations", "relations")):
        if src_key in declared and declared[src_key] != counts[key]:
            world["audit"]["warnings"].append("public header count differs: " + src_key)
    return world
