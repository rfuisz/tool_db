"""Central version constants and staleness detection for the extraction and materialization pipeline.

Bump EXTRACTION_VERSION when prompts, extraction schemas, or extraction pipeline
code changes in a way that would produce meaningfully different output for the
same source document.

Bump MATERIALIZATION_VERSION when the ItemMaterializer derivation logic, scoring
formulas, or explainer templates change so that re-materializing the same
extracted evidence would produce different derived content.

Rows stamped with a version lower than the current constant are considered stale
and eligible for re-processing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Current pipeline versions — bump these when the corresponding layer changes
# ---------------------------------------------------------------------------

EXTRACTION_VERSION = "extract_v2"
"""Covers prompt templates, extraction schemas, and the first-pass loader
normalization logic.  ``extract_v1`` rows lack freeform_explainers and
structured evidence fields in raw_payload."""

MATERIALIZATION_VERSION = "mat_v2"
"""Covers ItemMaterializer derivation: explainers, facets, replication summary,
problem links, comparisons, and summary promotion logic."""

LEGACY_EXTRACTION_VERSION = "extract_v1"
"""Assigned to rows created before versioning was introduced."""

LEGACY_MATERIALIZATION_VERSION = "v1"
"""The derived_version value used by the original materialization code."""


def extraction_is_stale(row_version: Optional[str]) -> bool:
    """Return True if *row_version* differs from EXTRACTION_VERSION."""
    if not row_version:
        return True
    return row_version != EXTRACTION_VERSION


def materialization_is_stale(row_version: Optional[str]) -> bool:
    """Return True if *row_version* differs from MATERIALIZATION_VERSION."""
    if not row_version:
        return True
    return row_version != MATERIALIZATION_VERSION


# ---------------------------------------------------------------------------
# Database-level staleness queries
# ---------------------------------------------------------------------------

def find_stale_extraction_items(
    cursor: Any,
    *,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return toolkit items whose best extracted evidence is below the current
    extraction version.

    An item is stale if:
    - It has no extracted_item_candidate rows at all, OR
    - All of its extracted_item_candidate rows have extraction_version < current

    Returns a list of dicts with ``item_id``, ``slug``, ``canonical_name``,
    and ``best_extraction_version``.
    """
    query = """
        SELECT
          ti.id AS item_id,
          ti.slug,
          ti.canonical_name,
          max(eic.extraction_version) AS best_extraction_version
        FROM toolkit_item ti
        LEFT JOIN extracted_item_candidate eic ON (
          eic.matched_item_id = ti.id
          OR eic.matched_slug = ti.slug
          OR (eic.slug = ti.slug
              AND eic.matched_item_id IS NULL
              AND coalesce(eic.matched_slug, '') = '')
        )
        GROUP BY ti.id
        HAVING max(eic.extraction_version) IS NULL
           OR max(eic.extraction_version) != %s
        ORDER BY ti.slug
    """
    params: list = [EXTRACTION_VERSION]
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)
    cursor.execute(query, params)
    return [
        {
            "item_id": row[0],
            "slug": row[1],
            "canonical_name": row[2],
            "best_extraction_version": row[3],
        }
        for row in cursor.fetchall()
    ]


def find_stale_materialization_items(
    cursor: Any,
    *,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return toolkit items whose derived content (explainers) is below
    the current materialization version.

    An item is stale if:
    - It has no item_explainer rows at all, OR
    - Its best explainer derived_version < current

    Returns a list of dicts with ``item_id``, ``slug``, ``canonical_name``,
    and ``best_derived_version``.
    """
    query = """
        SELECT
          ti.id AS item_id,
          ti.slug,
          ti.canonical_name,
          max(ie.derived_version) AS best_derived_version
        FROM toolkit_item ti
        LEFT JOIN item_explainer ie ON ie.item_id = ti.id
        GROUP BY ti.id
        HAVING max(ie.derived_version) IS NULL
           OR max(ie.derived_version) != %s
        ORDER BY ti.slug
    """
    params: list = [MATERIALIZATION_VERSION]
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)
    cursor.execute(query, params)
    return [
        {
            "item_id": row[0],
            "slug": row[1],
            "canonical_name": row[2],
            "best_derived_version": row[3],
        }
        for row in cursor.fetchall()
    ]


def staleness_report(cursor: Any) -> Dict[str, Any]:
    """Return a summary report of extraction and materialization staleness."""
    stale_extraction = find_stale_extraction_items(cursor)
    stale_materialization = find_stale_materialization_items(cursor)

    cursor.execute("SELECT count(*) FROM toolkit_item")
    total_items = cursor.fetchone()[0]

    cursor.execute(
        "SELECT count(DISTINCT coalesce(matched_item_id::text, matched_slug, slug)) "
        "FROM extracted_item_candidate "
        "WHERE extraction_version = %s",
        (EXTRACTION_VERSION,),
    )
    current_extraction_items = cursor.fetchone()[0]

    cursor.execute(
        "SELECT count(DISTINCT item_id) FROM item_explainer WHERE derived_version = %s",
        (MATERIALIZATION_VERSION,),
    )
    current_materialization_items = cursor.fetchone()[0]

    return {
        "current_extraction_version": EXTRACTION_VERSION,
        "current_materialization_version": MATERIALIZATION_VERSION,
        "total_items": total_items,
        "items_with_current_extraction": current_extraction_items,
        "items_needing_re_extraction": len(stale_extraction),
        "items_with_current_materialization": current_materialization_items,
        "items_needing_re_materialization": len(stale_materialization),
    }
