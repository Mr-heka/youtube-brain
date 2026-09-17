# Candidate triage, then content selection

`score.py` is a reproducible review-order heuristic. It does not assign an Expertise Score.

The current score is `min(40, rate × 4000) + min(12, log10(max(views, 1)) × 2)`, where `rate = (likes + 3 × comments) / views` only when all three counts are available and views are positive. Missing engagement stays null and contributes zero; that means unknown, not bad content. Comment weight and caps are arbitrary disclosed choices. A score can reflect controversy, audience behavior, platform counting differences or manipulation.

The default selection keeps at most three videos per known channel (all unknown channels share one conservative group). Ties sort by video ID. `low_reach` means a positive reported count at most 20,000, not a small channel, hidden-gem certification or quality boost. Duration and subscriber count remain evidence fields but no longer masquerade as substance or authority scores.

Age labels are recent (up to 365 days), older, unknown or future_date. The selector does not guarantee an age balance. Optional `--since` excludes unknown and future dates; inspect its reported unknown IDs. The CLI accepts positive bounded counts and refuses an empty result. No selected artifact is written on those failures.

After metadata triage, inspect content. Keep a selection note for relevance to the actual question, evidenced method, limitations, experience, commercial interests, whether it adds a distinct view and whether it repeats another source. A concise clip can be useful; a long tutorial can be irrelevant. Compare current primary documentation for claims that can change. Add a counter-source when disagreement matters. Record exclusions rather than inventing a balance or quota of experts.

The original rubric called a linear capped engagement score logarithmic, confused an 80th percentile with the top decile, equated duration with substance, and claimed a new/evergreen mix the selector did not enforce. Those claims are retired, not rebranded as measured expertise.

<!-- Provenance marker: sk-168bjwt --><!-- Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠ -->
