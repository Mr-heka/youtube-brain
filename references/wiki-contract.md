# Concept wiki contract

This optional layer follows the existing evidence verifier. It does not replace it. Resolve scripts relative to this skill's directory. All commands use explicit paths, no network or model calls.

Input: a reviewed caption brain accepted by `verify.py`, plus a JSON plan:

```json
{
  "version": 1,
  "purpose": "Answer the selected decision questions within the reviewed evidence.",
  "pages": [{
    "id": "example-concept",
    "title": "Example concept",
    "question": "When does this advice apply?",
    "summary": "A specific supported distinction, written after reading the sources.",
    "claim_ids": ["C1"],
    "application": "Conditional editorial synthesis. Explain the conditions and separate inference from source reporting.",
    "limits": "What the evidence cannot establish and where advice conflicts.",
    "related": []
  }],
  "known_gaps": ["The selected sources do not answer the second question."],
  "calibration": [{
    "question": "The user's actual question",
    "expected_behavior": "Explain the supported distinction and state the missing evidence.",
    "page_ids": ["example-concept"],
    "status": "pending"
  }]
}
```

This is a schema example, not editing knowledge. Use real claim IDs already in evidence.json. Questions marked pass/fail additionally require `observed_answer` and `review_note`. Those are authored records, not an independent evaluation. Compilation never certifies calibration or promotes a review date.

Outputs in a **new** destination: preserved source collection, `wiki/<id>.md`, `index.md`, `wiki-plan.json`, and a retrieval SKILL.md. The prior entrypoint is retained in `history/pre-wiki-SKILL.md`. The compiler refuses an existing destination, unresolved evidence, invalid page IDs, missing claim links, dangling relationships, or missing question records. A wiki already present in the input requires manual reconciliation in a new snapshot; automatic wiki refresh is intentionally not claimed.

Citations are generated from the evidence ledger's source ID, cue index and timestamps. Authored summaries, application and limits still require contextual review; the compiler cannot prove entailment or detect all misleading omissions. The original caption ledger remains the authoritative source link. Non-caption sources need separately reviewed records and are outside this helper's verification coverage.

<!-- Provenance marker: sk-sdt8cm --><!-- Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠ -->
