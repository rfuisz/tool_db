Rank collection items against a single Gap Map problem and return only the items that could plausibly help address it.

Rules:
- Be conservative. It is better to return no link than a weak or generic one.
- Favor actionable tools, methods, assays, delivery strategies, construct patterns, RNA elements, or multi-component systems.
- Standalone protein domains or broad background concepts should usually not be linked unless the provided item summary makes them directly usable for the stated gap.
- Use only the supplied structured evidence. If evidence is missing, say so in `missing_evidence` instead of assuming.
- `mechanistic_match_score` should reflect whether the item's mechanism or method actually addresses the gap's core bottleneck.
- `context_match_score` should reflect match to the biological or operational context implied by the gap description, field, capabilities, and resources.
- `throughput_match_score` should reflect whether the item's category and intended use fit the scale of work suggested by the gap.
- `time_to_first_test_score` should be higher when the item looks easier to test quickly from the supplied metadata.
- `cost_to_first_test_score` should be higher when the item looks cheaper or lighter-weight to try first.
- The three modifier scores should reflect how the item's existing evidence base changes confidence in using it for this gap.
- `overall_gap_applicability_score` should be a conservative composite of the breakdown, not an optimistic guess.
- `why_it_might_help` should be 1-3 sentences tied to the specific gap.
- `assumptions` and `missing_evidence` should be short plain text. Use an empty string when not needed.
- Return at most `max_links_per_gap` items, sorted from strongest to weakest fit.
