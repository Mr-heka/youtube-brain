# Runtime and evidence contract

## Inputs and side effects

Python helpers use local standard-library file/process/HTTP operations. Registry needs PyYAML. Only `discover.py --engine ...` and `extract.py --fetch` request network access. `engine.py detect` is local inspection. Every write needs an explicit task directory; a pre-existing output artifact is refused. Existing installed brains, indexes, mirrors, services, memory and board files are never automatically changed.

The yt-dlp adapter uses `--ignore-config`, `--no-plugin-dirs`, `--no-cache-dir` and `--no-remote-components`. It never takes browser cookies from environment or enables remote challenge code. Installed yt-dlp and any local JS runtime remain external dependencies; some videos may fail without additional reviewed dependencies. Do not bypass that failure with browser-profile access or auto-install. The API adapter reads only `YT_API_KEY`; raw provider output/errors are suppressed, never echoed as credential-bearing request URLs.

Data files are UTF-8 JSON, max 16 MB per local input, no duplicate keys/NaN. Video IDs use eleven YouTube-safe characters. Record lists reject duplicate IDs and negative/nonfinite counts. Raw captions, cue JSON and readable text are hashed together. Source paths must be regular files with no symlink components; macOS's standard `/tmp` and `/var` aliases are normalized. The helper is not a security sandbox against concurrent hostile filesystem changes or malicious installed executables.

## Discovery and extraction

A run contains `candidates.json`, `selected.json`, then a new `transcripts/` directory with `_index.json` plus `<id>.vtt`, `<id>.json`, `<id>.txt`. Titles, channel, publication date, query provenance, URL and retrieval time remain metadata. Retrieval is not content review.

Extraction preserves every nonempty timed VTT cue, decodes markup/entities and keeps square-bracket content. It skips WebVTT NOTE/STYLE/REGION blocks and rejects malformed timelines. It does not deduplicate rolling captions or identify speakers. Quote matching later is against a single stored cue. Use exact language codes, such as `en` or `en-US`. Local imports associate a filename with a source ID but cannot prove the file came from that source.

Nonzero partial discovery/extraction leaves its report. Inspect that report and continue only if the remaining coverage fits the question; `--allow-partial` is required for a draft with missing selected captions. Retry in a new run directory and reconcile by source ID. No successful old artifact is overwritten. A YouTube metadata caption flag does not guarantee English caption download access.

## Evidence ledger

After reading the sources, write `evidence.json` in the draft. Example below is a fictional local fixture, not a genuine source or quotation:

```json
{
  "source_reviews": {
    "abcdefghijk": {"disposition": "used", "reason": "Read the two supplied fictional cues; limited demonstration."}
  },
  "claims": [{
    "id": "C1",
    "statement": "The fictional speaker says to keep context.",
    "kind": "source_report",
    "citations": [{"source_id": "abcdefghijk", "cue_index": 0}]
  }],
  "quotes": [{
    "source_id": "abcdefghijk",
    "cue_index": 0,
    "text": "Keep [context] & test.",
    "verification": "caption_only"
  }],
  "reviewed_at": "2026-09-05"
}
```

Every manifest source needs `used` or `excluded` plus a reason. Claims need unique IDs, a nonempty statement, kind `source_report`, `interpretation` or `contested`, and valid citations to used sources. Cue indexes are zero-based. Quotes may be an empty list; a quote must be a literal substring of its cited cue. The checker does not verify the same claim is correctly represented in prose, semantic support, audio, qualifications, independence, legality or external primary documents. Review those directly. Do not turn `caption_only` into an audio-verified label by changing the JSON.

Use source IDs/locators in the prose too. For non-video evidence, maintain a separate explicit source table and citations in the written references; this caption checker does not ingest or validate it. Do not attach an unrelated caption to make a claim pass.

The manifest remains draft until actual content review. Then its author may record `status: reviewed` and `last_synthesized: YYYY-MM-DD` with the review limitations. `verify.py` never writes those values. A schema pass cannot grant that status by itself.

## Refresh and legacy migration

`--update-from` copies prior files into a new destination; the old brain stays byte-identical. It merges new caption IDs and refuses changed bytes under an existing ID until explicitly reconciled. It does not append a misleading “refreshed knowledge” date. Fill and review the new evidence ledger for all used sources, including retained ones.

For original brains lacking `brain-manifest.json`, `--legacy-copy` preserves every UTF-8 file, including synthesis and old source text, while recording a `legacy_unverified` hash manifest. No previous records are invented. The checker refuses that unresolved legacy state. Reconcile each inherited claim and source against actual evidence: capture a real URL/identity and timed source where available, or remove that claim from the active synthesis while preserving it as history. Keep non-caption primary sources explicitly outside caption-checker coverage. Record this disposition and its review date before clearing the legacy marker. Missing source history must remain a limitation, not a fabricated retrieval record.

If an imported legacy filename collides with a newly captured source, the snapshot refuses overwrite. Resolve the conflict in a separate prepared copy with explicit historical naming; retain both versions and provenance. No automatic consolidation/deletion is implemented. `registry.py consolidate` reports candidates only.

## Interface migration

| Old call or behavior | Current replacement |
| --- | --- |
| `engine.py detect` installs, `update` runs package managers | `detect` only reports; package changes use the host's existing reviewed workflow |
| Implicit engine / detected Apify token | Explicit `--engine yt-dlp` or `youtube_api`; Apify was never implemented |
| `extract.py OUT` | Explicit `--fetch` or `--vtt-dir DIR` |
| `build_brain.py OUT TOPIC` writes global skills | Required new `--destination DIR` |
| `--update --into SLUG` mutates installed brain | `--update-from PATH --destination NEW_PATH`; legacy adds `--legacy-copy` |
| Implicit real library and default Obsidian mirror | Explicit `--library`, new `--output`, optional exact new-file `--mirror` |
| Monthly maintenance overwrites/deletes board/memory | `maintain.sh LIBRARY` prints reports; nonzero on failure; no scheduler installed |
| Filled counters imply expertise/currentness | Actual source counts, draft/review status and separate local evidence checks |

Any old installed launchd job calling maintenance without its explicit library will now fail with usage text rather than mutate a guessed library. Updating that job is a separately scoped integration task, not performed by this skill rebuild.

## Primary technical sources checked 2026-09-05

- [yt-dlp official README](https://github.com/yt-dlp/yt-dlp): configuration/plugin/remote-component suppression and subtitle flags. No bundled upstream code or license was copied.
- [YouTube video resource](https://developers.google.com/youtube/v3/docs/videos): duration and caption availability fields. Missing fields are not invented.
- [YouTube caption download](https://developers.google.com/youtube/v3/docs/captions/download): authenticated permission requirements; an API key is not a universal transcript route.

Local fixtures verify the adapters' behavior under mocked providers. They do not establish live availability, quota, transcript rights or current yt-dlp compatibility with every video.

## Concept-wiki extension (2026-09-12)

`build_wiki.py BRAIN PLAN` validates without writing; `--destination NEW` compiles a new wiki snapshot after the existing evidence verifier passes. See [wiki-contract.md](wiki-contract.md). It does not replace caption ingestion or grant non-caption evidence verification. It never changes the original brain or review date, and does not certify semantic support, question-test results or installation. Existing `build_brain.py`, registry, discovery and refresh interfaces remain compatible.

<!-- Provenance marker: sk-sdt8cm --><!-- Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠ -->
