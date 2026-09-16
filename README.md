# Topic Brain Builder

Topic Brain Builder helps an agent turn selected YouTube caption evidence into a traceable local knowledge folder. It keeps source snapshots, hashes, claim-to-cue references, known gaps and review status separate, then optionally compiles reviewed evidence into linked concept pages.

Installing this skill does not download research, train or fine-tune a model, create a knowledge base, connect an account, or publish anything. The agent still has to define the research question, acquire authorized sources, read them, synthesize the evidence and test the resulting answers.

## Requirements

- Python 3.11 or newer.
- PyYAML for registry parsing and the included offline tests.
- Optional: an existing current `yt-dlp` executable for YouTube search and caption retrieval.
- Optional: `YT_API_KEY` and available YouTube Data API quota for official metadata discovery. An API key does not grant universal caption-download access.

The skill never installs dependencies. Use the current machine's reviewed package workflow if a dependency is missing and installation has been authorized.

## Install

Open [SETUP-PROMPT.md](SETUP-PROMPT.md), copy the prompt, and give it to your AI agent. The agent clones this repository, inspects the skill, runs its offline checks and installs it using the host's supported method. Existing installations are preserved.

The repository is the shared source. The [drop page](https://drops.selrai.com.au/youtube-brain) provides the introduction, video and the same installation prompt.

## Safe first check

The setup prompt runs this local detector before installation. It does not contact a service:

```sh
python3 -B scripts/engine.py detect
```

Run the offline suite against a directory chosen only for temporary test output:

```sh
mkdir -p /absolute/path/to/test-target
PYTHON_BIN=python3 ./scripts/smoke.sh /absolute/path/to/test-target
```

The suite uses fictional fixtures. It blocks Python socket access, writes under the explicit test target, and does not perform discovery, caption fetching, package installation, paid transcription, browser access or model calls. The socket guard is test-process protection, not a general operating-system sandbox.

## What is included

- `SKILL.md`: the agent workflow and decision boundaries.
- `scripts/`: explicit discovery, scoring, local or remote caption extraction, draft creation, evidence checks, concept-wiki compilation and registry reporting.
- `references/`: execution, scoring, evidence and wiki contracts.
- `tests/`: offline functional fixtures for the active runtime.
- `NOTICE.md`: authorship, foundation and license status.

Only `discover.py --engine ...` and `extract.py --fetch` use the network. Do not run them until the user has approved the topic, source scope, engine and any cost-bearing work. Read the runtime contract before a real build.

Made by Selr AI.

<!-- Provenance marker: sk-1qd83hv --><!-- Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠ -->
