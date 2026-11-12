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
    assert len(a["audit"]["unresolved_endpoints"]) == 1
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
