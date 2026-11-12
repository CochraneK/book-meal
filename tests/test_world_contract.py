# -*- coding: utf-8 -*-
"""Zero-dependency contract checks; discovered by tests/run_tests.py."""
from __future__ import annotations

import copy
from pathlib import Path

from world_contract import base_world, stable_id, validate_world
from world_adapters import ming, sanggan
from export_world import ROOT, assert_safe_output, build


def synthetic_sanggan():
    return {
        "manifest": {"book": {"title": "Synthetic Sanggan Test", "author": "Test"}},
        "kernel": {"count": 3, "ontology_version": "2.0.0",
                   "persons": [{"id": "person:A", "kernel_path": "kernel/persons/A.json"}]},
        "persons": [
            {"id": "person:A", "name": "A", "first_chapter": 11,
             "alias": [], "evidence": "observed", "role_in_book": "worker"},
            {"id": "person:B", "name": "B", "first_chapter": 12,
             "evidence": "observed"},
        ],
        "places": [{"id": "place:X", "name": "X", "type": "village"}],
        "events": {"count": 1, "events": [
            {"id": "event:E1", "chapter": 12, "time": "fictional",
             "summary": "A meets B", "actors": ["person:A", "person:B", "person:UNKNOWN"],
             "evidence": "observed", "canonical_path": "life_events::experienced_event"}
        ]},
        "relations": {"count": 2, "relations": [
            {"id": "rel:R1", "from": "person:A", "to": "person:B",
             "sub_pred": "colleague", "family": "related_to_person",
             "source_type": "observed", "chapters": [12],
             "canonical_path": "related_to_person::colleague"},
            {"id": "rel:R2", "from": "person:A", "to": "person:UNKNOWN",
             "sub_pred": "unknown", "source_type": "inferred", "chapters": [],
             "canonical_path": "related_to_person::unknown"}
        ]},
    }


def test_sanggan_adapter_synthetic_roundtrip():
    source = synthetic_sanggan()
    a = sanggan.adapt(source)
    b = sanggan.adapt(copy.deepcopy(source))
    assert a == b, "repeat conversion must be deterministic"
    assert not validate_world(a), validate_world(a)[:10]
    assert (len(a["persons"]), len(a["events"]), len(a["relations"])) == (2, 1, 2)
    assert len(a["entities"]) == 1  # unresolved reference is NOT an invented person
    assert a["entities"][0]["status"] == "unresolved"
    assert len(a["audit"]["unresolved_endpoints"]) == 2
    assert {x["source_path"] for x in a["audit"]["unresolved_endpoints"]} == {
        "world/event_graph/events.json", "world/relation_graph/relations.json"
    }
    assert len(a["entities"][0]["evidence_ids"]) == 2
    assert a["persons"][0]["extensions"]["sanggan"]["kernel_path"] == "kernel/persons/A.json"
    assert any(e["kind"] == "INFER" for e in a["evidence"])


def test_sanggan_requires_private_source_path():
    try:
        build("sanggan")
    except ValueError as exc:
        assert "--source-root" in str(exc)
    else:
        raise AssertionError("private source must be explicit")


def test_private_export_inside_public_checkout_is_rejected():
    try:
        assert_safe_output("sanggan", ROOT / "data" / "private-export.json")
    except ValueError:
        pass
    else:
        raise AssertionError("must refuse private export under public checkout")


def test_ming_synthetic_preserves_nonperson_endpoints():
    source = {
        "characters": [{"name": "A", "role": "ruler", "chapters": ["p1-c1"]},
                       {"name": "B", "chapters": ["p1-c2"]}],
        "locations": [{"ancient": "City", "chapters": ["p1-c1"]}],
        "events": [{"name": "Event", "year": 1370, "chapters": ["p1-c2"],
                    "participants": ["A", "unknown actor"]}],
        "relations": [{"from": "A", "to": "Office", "rel": "member of",
                       "chapter": "p1-c2", "endpoint_kind": {"from": "person", "to": "org"}}],
        "reigns": [{"name": "A"}],
    }
    a = ming.adapt(source, {"title": "Ming", "author": "Test"})
    b = ming.adapt(copy.deepcopy(source), {"title": "Ming", "author": "Test"})
    assert a == b
    assert not validate_world(a), validate_world(a)
    assert len(a["persons"]) == 2
    assert len(a["places"]) == 1
    assert len(a["entities"]) == 2
    assert a["events"][0]["time"]["year_start"] == 1370
    assert a["extensions"]["ming"]["reigns_count"] == 1


def test_validator_rejects_dangling_and_reversed_time():
    world = sanggan.adapt(synthetic_sanggan())
    bad = copy.deepcopy(world)
    bad["relations"][0]["from_id"] = "person:sanggan:missing"
    bad["events"][0]["time"]["year_start"] = 2020
    bad["events"][0]["time"]["year_end"] = 1910
    failures = validate_world(bad)
    assert any("dangling endpoint" in msg for msg in failures)
    assert any("reversed year" in msg for msg in failures)


def test_validator_rejects_missing_evidence_and_duplicate_ids():
    world = sanggan.adapt(synthetic_sanggan())
    bad = copy.deepcopy(world)
    bad["persons"][0]["evidence_ids"] = ["evidence:missing"]
    bad["persons"][1]["id"] = bad["persons"][0]["id"]
    messages = validate_world(bad)
    assert any("duplicate" in msg for msg in messages)
    assert any("evidence" in msg for msg in messages)


def test_id_is_namespaced_and_order_independent():
    assert stable_id("person", "ming", "A") == stable_id("person", "ming", "A")
    assert stable_id("person", "ming", "A") != stable_id("person", "sanggan", "A")
    assert stable_id("event", "ming", "A") != stable_id("person", "ming", "A")


def test_real_ming_contract_against_read_only_source():
    # Run against the public canonical aggregate already checked into Book-Meal.
    world = build("ming")
    errors = validate_world(world)
    assert not errors, errors[:12]
    assert len(world["persons"]) >= 1200
    assert len(world["events"]) >= 1000
    assert len(world["relations"]) >= 2000
    assert all(x["ontology_version"] == "2.0.0" for x in world["persons"])
    assert len({x["id"] for x in world["evidence"]}) == len(world["evidence"])



def test_sanggan_real_shape_chapter_annotations_do_not_disappear():
    """In the real private source, evidence may be a chapter note, not a flag."""
    s = synthetic_sanggan()
    s["persons"][0]["evidence"] = "chapter note with source context"
    s["events"]["events"][0]["evidence"] = "chapter reference"
    s["places"][0]["evidence"] = "another source annotation"
    result = sanggan.adapt(s)
    target_ids = {
        result["persons"][0]["id"], result["events"][0]["id"], result["places"][0]["id"]
    }
    annotations = [x for x in result["evidence"] if x["for_id"] in target_ids]
    assert len(annotations) == 3
    assert all(x["kind"] == "BOOK" for x in annotations)
    assert all(x["verification"] == "source_record_only" for x in annotations)
    assert all("source chapter annotation only" in x.get("note", "") for x in annotations)
    assert "chapter note with source context" not in str(result)


def test_sanggan_declared_counts_are_not_mistaken_for_actual():
    s = synthetic_sanggan()
    s["kernel"]["count"] = 3  # actual kernel entries: 1, person index: 2
    s["relations"]["count"] = 99  # actual: 2
    s["events"]["count"] = 88  # actual: 1
    s["manifest"]["counts"] = {"persons": 42, "relations": 99}
    result = sanggan.adapt(s)
    assert not validate_world(result)
    warnings = result["audit"]["warnings"]
    assert any("kernel header count" in x for x in warnings)
    assert any("kernel entry count" in x for x in warnings)
    assert any("relation header count" in x for x in warnings)
    assert any("event header count" in x for x in warnings)
    assert any("manifest persons" in x for x in warnings)
    assert result["audit"]["source_counts"]["persons"] == 2
    assert result["audit"]["source_counts"]["relations"] == 2


def test_unresolved_records_keep_each_distinct_origin_and_deduplicate_repeats():
    s = synthetic_sanggan()
    s["events"]["events"][0]["actors"].append("person:UNKNOWN")
    s["relations"]["relations"][1]["to"] = "person:UNKNOWN"
    result = sanggan.adapt(s)
    unresolved = result["entities"]
    assert len(unresolved) == 1
    assert len(unresolved[0]["evidence_ids"]) == 2
    assert len(result["audit"]["unresolved_endpoints"]) == 2
    assert len(set(x["id"] for x in result["evidence"])) == len(result["evidence"])
    assert not validate_world(result)


def test_sanggan_no_evidence_source_falls_back_to_unknown():
    s = synthetic_sanggan()
    s["persons"][0].pop("evidence")
    result = sanggan.adapt(s)
    link = result["persons"][0]["evidence_ids"][0]
    record = next(x for x in result["evidence"] if x["id"] == link)
    assert record["kind"] == "UNKNOWN"
