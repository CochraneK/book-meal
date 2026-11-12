# -*- coding: utf-8 -*-
"""Read-only adapter for Book-Meal's existing Ming aggregate data/data.json."""
from __future__ import annotations

from world_contract import HUMAN_ONTOLOGY_VERSION, ONTOLOGY_URI, add_evidence, base_world, stable_id, unresolved_entity


def adapt(source: dict, manifest: dict) -> dict:
    wid = "ming"
    repo = "CochraneK/book-meal"
    path = "data/data.json"
    world = base_world(wid, manifest["title"], manifest.get("author", ""), repo)
    person_ids, place_ids = {}, {}
    for character in source.get("characters", []):
        name = str(character.get("name") or "").strip()
        if not name:
            world["audit"]["warnings"].append("blank person name skipped")
            continue
        if name in person_ids:
            world["audit"]["warnings"].append("duplicate person name: " + name)
            continue
        pid = stable_id("person", wid, name)
        person_ids[name] = pid
        ch = character.get("chapters") or []
        src_kind = "BOOK" if ch else "UNKNOWN"
        eid = add_evidence(world, pid, kind=src_kind, repo=repo, path=path,
                           native_id=name, chapters=ch)
        world["persons"].append({
            "id": pid, "source_id": name, "name": name,
            "ontology_version": HUMAN_ONTOLOGY_VERSION,
            "ontology_ref": ONTOLOGY_URI,
            "aliases": character.get("aliases") or [],
            "roles": ([character["role"]] if character.get("role") else []),
            "evidence_ids": [eid],
            "extensions": {"ming": {
                "faction": character.get("faction"), "birth": character.get("birth"),
                "life": character.get("life"), "chapters_derived": character.get("chapters_derived") or [],
            }},
        })
    for place in source.get("locations", []):
        name = str(place.get("ancient") or "").strip()
        if not name:
            world["audit"]["warnings"].append("blank place name skipped")
            continue
        if name in place_ids:
            world["audit"]["warnings"].append("duplicate place name: " + name)
            continue
        pid = stable_id("place", wid, name)
        place_ids[name] = pid
        eid = add_evidence(world, pid, kind="BOOK" if place.get("chapters") else "UNKNOWN",
                           repo=repo, path=path, native_id=name, chapters=place.get("chapters"))
        world["places"].append({
            "id": pid, "source_id": name, "name": name, "kind": "historical_place",
            "evidence_ids": [eid],
            "extensions": {"ming": {
                "modern_address": place.get("modern_address"), "lat": place.get("lat"),
                "lng": place.get("lng"), "geo_status": place.get("status"),
                "mentioned_as": place.get("mentioned_as") or [],
            }},
        })

    def endpoint(name, kind="unknown"):
        name = str(name)
        if name in person_ids:
            return person_ids[name]
        if name in place_ids:
            return place_ids[name]
        return unresolved_entity(world, name, source_path=path, expected_kind=kind)

    for event in source.get("events", []):
        name = str(event.get("name") or "").strip()
        if not name:
            world["audit"]["warnings"].append("blank event name skipped")
            continue
        event_id = stable_id("event", wid, name)
        chapters = event.get("chapters") or []
        evid = add_evidence(world, event_id, kind="BOOK" if chapters else "UNKNOWN",
                            repo=repo, path=path, native_id=name, chapters=chapters)
        # Explicitly corrected years may originate from memory / external references.
        # Preserve their source without upgrading them to independently verified facts.
        year = event.get("year")
        time = {"year_start": year if type(year) is int else None,
                "year_end": year if type(year) is int else None,
                "label": str(year) if year not in (None, "") else None,
                "chapter": None}
        world["events"].append({
            "id": event_id, "source_id": name, "name": name,
            "participants": [endpoint(n, "person") for n in (event.get("participants") or []) if n],
            "time": time, "evidence_ids": [evid],
            "extensions": {"ming": {
                "type": event.get("type"), "category": event.get("category"),
                "location": event.get("location"), "year_source": event.get("year_source"),
                "year_approx": bool(event.get("year_approx")),
            }},
        })
    seen_relation_keys = {}
    for rel in source.get("relations", []):
        if not rel.get("from") or not rel.get("to") or not rel.get("rel"):
            world["audit"]["warnings"].append("incomplete source relation skipped")
            continue
        native = "|".join(str(rel.get(k) or "") for k in ("from", "to", "rel", "chapter"))
        seq = seen_relation_keys.get(native, 0)
        seen_relation_keys[native] = seq + 1
        source_key = native if not seq else native + "|duplicate:" + str(seq)
        rid = stable_id("relation", wid, source_key)
        chapter = rel.get("chapter")
        derived = str(chapter or "").lower() in ("curated", "推导")
        evid = add_evidence(world, rid, kind="INFER" if derived else ("BOOK" if chapter else "UNKNOWN"),
                            repo=repo, path=path, native_id=source_key,
                            chapters=[chapter] if chapter and not derived else [],
                            note="legacy curated/derived relation" if derived else "")
        kind = rel.get("endpoint_kind") or {}
        world["relations"].append({
            "id": rid, "source_id": source_key,
            "from_id": endpoint(rel["from"], kind.get("from", "unknown")),
            "to_id": endpoint(rel["to"], kind.get("to", "unknown")),
            "predicate": str(rel["rel"]), "canonical_path": None,
            "evidence_ids": [evid],
            "extensions": {"ming": {"category": rel.get("category"), "source_chapter": chapter}},
        })
    world["audit"]["source_counts"] = {
        k: len(source.get(k) or []) for k in ("characters", "locations", "events", "relations")
    }
    world["extensions"]["ming"] = {
        "timeline_available": bool(source.get("timeline")), "reigns_count": len(source.get("reigns") or []),
        "lifespans_count": len(source.get("lifespans") or []),
        "voyages_available": bool(source.get("voyages")),
        "preserved_in_source": ["timeline", "reigns", "lifespans", "voyages"],
    }
    return world
