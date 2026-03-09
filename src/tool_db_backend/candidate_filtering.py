import json
import re
from typing import Any, Dict, List, Optional

from tool_db_backend.config import Settings

_GENERIC_TOPIC_NAMES = {
    "optogenetics",
    "synthetic biology",
    "protein engineering",
    "genetic engineering",
    "cell biology",
}

_GENERIC_PLURAL_HEADS = {
    "tools",
    "proteins",
    "domains",
    "methods",
    "techniques",
    "systems",
    "applications",
    "approaches",
    "constructs",
    "switches",
    "pathways",
    "genes",
    "vectors",
}

_BACKGROUND_BIOLOGY_TOKENS = {
    "acid",
    "adipogenesis",
    "antibody",
    "antibodies",
    "bacteria",
    "cancer",
    "cell",
    "cells",
    "disease",
    "embryo",
    "embryos",
    "enzyme",
    "enzymes",
    "gene",
    "genes",
    "kinase",
    "kinases",
    "metabolism",
    "metabolite",
    "metabolites",
    "mouse",
    "mice",
    "organoid",
    "organoids",
    "pathway",
    "pathways",
    "peptide",
    "peptides",
    "plant",
    "plants",
    "primary",
    "protein",
    "proteins",
    "receptor",
    "receptors",
    "stem",
    "tissue",
    "tissues",
    "virus",
    "viruses",
    "yeast",
    "zebrafish",
}

_ENGINEERED_ENTITY_TOKENS = {
    "assay",
    "construct",
    "delivery",
    "design",
    "dimerizer",
    "display",
    "editor",
    "evolution",
    "fusion",
    "harness",
    "library",
    "method",
    "pattern",
    "promoter",
    "recombinase",
    "reporter",
    "screen",
    "sequence",
    "switch",
    "system",
    "vector",
}

_DISCRETE_ITEM_TYPES = {
    "protein_domain",
    "multi_component_switch",
    "rna_element",
    "construct_pattern",
    "engineering_method",
    "assay_method",
    "computation_method",
    "delivery_harness",
}

_TITLE_FUNCTION_WORDS = {
    "a", "an", "the", "for", "of", "in", "by", "with", "using", "via",
    "toward", "towards", "from", "between", "through", "and", "or", "to",
    "that", "which", "its", "their", "on", "into", "upon", "during",
}

_MAX_TOOL_NAME_TOKENS = 10
_TITLE_HEURISTIC_MIN_TOKENS = 6
_TITLE_HEURISTIC_MIN_FUNCTION_WORDS = 2


def load_controlled_vocabularies(settings: Settings) -> Dict[str, Any]:
    vocab_path = settings.schema_root / "canonical" / "controlled_vocabularies.v1.json"
    try:
        return json.loads(vocab_path.read_text())
    except Exception:
        return {}


def assess_toolkit_item_candidate(
    entity: Dict[str, Any],
    *,
    allowed_item_types: Optional[set[str]] = None,
) -> Dict[str, Any]:
    canonical_name = str(entity.get("canonical_name") or "").strip()
    aliases = _dedupe_strings(entity.get("aliases", []))
    external_ids = entity.get("external_ids", {}) if isinstance(entity.get("external_ids"), dict) else {}
    item_type_raw = str(entity.get("item_type") or "").strip() or None
    item_type = item_type_raw if item_type_raw in (allowed_item_types or _DISCRETE_ITEM_TYPES) else None
    tokens = _tokenize(canonical_name)

    if not canonical_name:
        return {"keep": False, "reason": "missing_canonical_name", "item_type": item_type}
    if item_type_raw and item_type is None:
        return {"keep": False, "reason": "unsupported_item_type", "item_type": None}
    if _looks_like_molecular_weight_label(canonical_name):
        return {"keep": False, "reason": "molecular_weight_label", "item_type": item_type}
    if _looks_like_placeholder_label(canonical_name) and not aliases and not external_ids:
        return {"keep": False, "reason": "placeholder_name", "item_type": item_type}
    if _looks_like_generic_class_name(canonical_name, tokens, item_type, aliases, external_ids):
        return {"keep": False, "reason": "generic_class", "item_type": item_type}
    if _looks_like_paper_title_or_description(tokens):
        return {"keep": False, "reason": "paper_title_or_description", "item_type": item_type}
    if _looks_like_background_biology_entity(tokens, item_type):
        return {"keep": False, "reason": "background_biology_entity", "item_type": item_type}
    if (
        item_type is None
        and not aliases
        and not external_ids
        and len(tokens) <= 3
        and not any(token in _ENGINEERED_ENTITY_TOKENS for token in tokens)
    ):
        return {"keep": False, "reason": "low_specificity_name", "item_type": item_type}

    return {"keep": True, "reason": None, "item_type": item_type}


def _tokenize(value: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.casefold()) if token]


def _dedupe_strings(values: List[Any]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values or []:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _looks_like_molecular_weight_label(value: str) -> bool:
    normalized = value.casefold()
    return bool(
        re.search(r"\b\d+(?:\.\d+)?\s*(?:kd|kda|mr)\b", normalized)
        or re.search(r"\b\d+\s*aa\b", normalized)
    )


def _looks_like_placeholder_label(value: str) -> bool:
    normalized = value.strip()
    return bool(re.fullmatch(r"[A-Za-z]?\d{1,3}[A-Za-z]?", normalized))


def _looks_like_generic_class_name(
    value: str,
    tokens: List[str],
    item_type: Optional[str],
    aliases: List[str],
    external_ids: Dict[str, Any],
) -> bool:
    normalized = value.casefold().strip()
    if normalized in _GENERIC_TOPIC_NAMES:
        return True
    if tokens and tokens[-1] in {"tools", "methods", "techniques", "systems"}:
        return True
    if item_type == "protein_domain" and tokens and tokens[-1] == "domain" and len(tokens) <= 2:
        return True
    if item_type == "delivery_harness" and any(
        token in {"aav", "adenovirus", "lentivirus", "vector", "vectors", "viral", "delivery", "capsid"}
        for token in tokens
    ):
        return False
    if item_type == "computation_method" and (aliases or external_ids):
        return False
    if item_type in {"construct_pattern", "assay_method"} and any(
        token in _ENGINEERED_ENTITY_TOKENS for token in tokens
    ):
        return False
    if item_type == "engineering_method" and any(
        token in {"design", "evolution", "selection", "screen", "purification"} for token in tokens
    ):
        return False
    if tokens and tokens[-1] in _GENERIC_PLURAL_HEADS:
        return True
    return False


def _looks_like_paper_title_or_description(tokens: List[str]) -> bool:
    if len(tokens) > _MAX_TOOL_NAME_TOKENS:
        return True
    if len(tokens) >= _TITLE_HEURISTIC_MIN_TOKENS:
        function_word_count = sum(1 for t in tokens if t in _TITLE_FUNCTION_WORDS)
        if function_word_count >= _TITLE_HEURISTIC_MIN_FUNCTION_WORDS:
            return True
    return False


def _looks_like_background_biology_entity(tokens: List[str], item_type: Optional[str]) -> bool:
    if item_type in {"delivery_harness", "construct_pattern", "engineering_method", "assay_method", "computation_method"}:
        return False
    if any(token in _ENGINEERED_ENTITY_TOKENS for token in tokens):
        return False
    if item_type in {"multi_component_switch", "rna_element"}:
        return False
    return any(token in _BACKGROUND_BIOLOGY_TOKENS for token in tokens)
