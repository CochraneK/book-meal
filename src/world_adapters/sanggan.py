# -*- coding: utf-8 -*-
"""Private-source-aware, read-only Sanggan adapter.

NO private Sanggan data is bundled in Book-Meal. Source paths are supplied
locally by an authorized operator. Unknown endpoints become explicitly
unresolved entities, never fabricated persons.
"""
from __future__ import annotations

from pathlib import Path

from world_contract import HUMAN_ONTOLOGY_VERSION, ONTOLOGY_URI, add_evidence, base_world, load_json, stable_id, unresolved_entity


def read_source(source_root: Path) -> dict:
    root = source_root.resolve()
    def read(path):
        return load_json(root / path)
    kernel = root / "world/kernel/index.json"
    return {
        "persons": read("world/index/persons.json"),
        "places": read("world/index/places.json"),
        "events": read("world/event_graph/events.json"),
        "relations": read("world/relation_graph/relations.json"),
        "kernel": load_json(kernel) if kernel.exists() else None,
        "manifest": read("world/index/manifest.json"),
    }


def adapt(source: dict) -> dict:
    repo = "CochraneK/sanggan"
    wid = "sanggan"
    book = source.get("manifest", {}).get("book") or {}
    world = base_world(wid, book.get("title", "太阳照在桑乾河上"), book.get("author", "丁玲"), repo)
    person_ids, place_ids, kernel_refs = {}, {}, {}
    kernels = source.get("kernel") or {}
    for item in kernels.get("persons") or []:
        if item.get("id") and item.get("kernel_path"):
            kernel_refs[item["id"]] = item["kernel_path"]
    if kernels.get("count") is not None and kernels.get("count") != len(source.get("persons") or []):
        world["audit"]["warnings"].append("kernel index count differs from canonical person index")
    for person in source.get("persons") or []:
        native = person.get("id")
        if not native or not person.get("name"):
            world["audit"]["warnings"].append("incomplete person skipped")
            continue
        if native in person_ids:
            world["audit"]["warnings"].append("duplicate source person ID: " + native)
            continue
        pid = stable_id("person", wid, native)
        person_ids[native] = pid
        chapter = person.get("first_chapter")
        evid = add_evidence(world, pid, kind="BOOK" if person.get("evidence") == "observed" else "UNKNOWN",
                            repo=repo, path="world/index/persons.json", native_id=native,
                            chapters=[chapter] if chapter is not None else [])
        world["persons"].append({
            "id": pid, "source_id": native, "name": person["name"],
            "ontology_version": HUMAN_ONTOLOGY_VERSION, "ontology_ref": ONTOLOGY_URI,
            "aliases": person.get("alias") or [],
            "roles": [person["role_in_book"]] if person.get("role_in_book") else [],
            "evidence_ids": [evid],
            "extensions": {"sanggan": {
                "social_class": person.get("class"), "gender": person.get("gender"),
                "first_chapter": chapter,
                # Pointer only: never materialize private kernel text in this public repo.
                "kernel_path": kernel_refs.get(native),
            }},
        })
    for place in source.get("places") or []:
        native = place.get("id")
        if not native or not place.get("name"):
            world["audit"]["warnings"].append("incomplete place skipped")
            continue
        if native in place_ids:
            world["audit"]["warnings"].append("duplicate source place ID: " + native)
            continue
        pid = stable_id("place", wid, native)
        place_ids[native] = pid
        evid = add_evidence(world, pid, kind="BOOK" if place.get("evidence") else "UNKNOWN",
                            repo=repo, path="world/index/places.json", native_id=native)
        world["places"].append({
            "id": pid, "source_id": native, "name": place["name"],
            "kind": place.get("type") or "unknown", "evidence_ids": [evid],
            "extensions": {"sanggan": {"type": place.get("type")}},
        })
    def endpoint(native, expected_kind="person"):
        native = str(native)
        if native in person_ids:
            return person_ids[native]
        if native in place_ids:
            return place_ids[native]
        return unresolved_entity(world, native, source_path="world/relation_graph/relations.json",
                                 expected_kind=expected_kind)

    events_in = source.get("events") or {}
    events = events_in.get("events") if isinstance(events_in, dict) else events_in
    for event in events or []:
        native = event.get("id")
        if not native:
            world["audit"]["warnings"].append("event without ID skipped")
            continue
        eid = stable_id("event", wid, native)
        chapter = event.get("chapter")
        evidence_kind = "INFER" if event.get("evidence") == "inferred" else (
            "BOOK" if event.get("evidence") == "observed" else "UNKNOWN")
        evid = add_evidence(world, eid, kind=evidence_kind, repo=repo,
                            path="world/event_graph/events.json", native_id=native,
                            chapters=[chapter] if chapter is not None else [])
        world["events"].append({
            "id": eid, "source_id": native, "name": event.get("summary") or native,
            "participants": [endpoint(x) for x in event.get("actors") or [] if x],
            "time": {"year_start": None, "year_end": None,
                     "label": event.get("time") or None, "chapter": chapter},
            "evidence_ids": [evid],
            "extensions": {"sanggan": {"canonical_path": event.get("canonical_path")}},
        })
    relation_in = source.get("relations") or {}
    relations = relation_in.get("relations") if isinstance(relation_in, dict) else relation_in
    for relation in relations or []:
        native = relation.get("id")
        if not native or not relation.get("from") or not relation.get("to"):
            world["audit"]["warnings"].append("incomplete relation skipped")
            continue
        rid = stable_id("relation", wid, native)
        source_type = relation.get("source_type")
        evid = add_evidence(world, rid, kind="INFER" if source_type == "inferred" else (
                            "BOOK" if source_type == "observed" else "UNKNOWN"),
                            repo=repo, path="world/relation_graph/relations.json",
                            native_id=native, chapters=relation.get("chapters") or [])
        world["relations"].append({
            "id": rid, "source_id": native,
            "from_id": endpoint(relation["from"], relation.get("from_entity_type") or "unknown"),
            "to_id": endpoint(relation["to"], relation.get("to_entity_type") or "unknown"),
            "predicate": relation.get("sub_pred") or relation.get("source_pred") or "related_to",
            "canonical_path": relation.get("canonical_path"), "evidence_ids": [evid],
            "extensions": {"sanggan": {
                "family": relation.get("family"), "confidence": relation.get("confidence"),
                "source_predicate": relation.get("source_pred"),
            }},
        })
    world["audit"]["source_counts"] = {
        "persons": len(source.get("persons") or []),
        "places": len(source.get("places") or []),
        "events": len(events or []), "relations": len(relations or []),
    }
    if isinstance(relation_in, dict) and relation_in.get("count") is not None and relation_in["count"] != len(relations or []):
        world["audit"]["warnings"].append("source relation header count differs from records")
    world["extensions"]["sanggan"] = {
        "kernel_ontology_version": kernels.get("ontology_version"),
        "kernel_pointers": len(kernel_refs), "kernel_available_locally": bool(kernel_refs),
        "full_persona_and_original_evidence": "kept in private source; not copied",
    }
    return world
