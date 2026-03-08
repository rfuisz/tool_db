from tool_db_backend.config import get_settings
from tool_db_backend.entity_resolution import EntityResolver


def test_entity_resolver_matches_existing_items_by_slug_or_name() -> None:
    resolver = EntityResolver(get_settings())

    resolutions = resolver.resolve_item_candidates(
        {
            "item_aslov2": {
                "candidate_key": "item/aslov2",
                "slug": "aslov2",
                "canonical_name": "AsLOV2",
                "aliases": ["Avena sativa LOV2"],
            },
            "item_new": {
                "candidate_key": "item/new-tool",
                "slug": "new-tool",
                "canonical_name": "New Tool",
                "aliases": [],
            },
        }
    )

    assert resolutions["item_aslov2"]["resolution_status"] == "matched_existing"
    assert resolutions["item_aslov2"]["matched_slug"] == "aslov2"
    assert resolutions["item_new"]["resolution_status"] == "new_candidate"
