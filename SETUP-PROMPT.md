# Install Topic Brain Builder

Copy this into your AI agent:

```text
https://github.com/Mr-heka/youtube-brain

Install the Topic Brain Builder skill from this repository for the AI agent I am using.

1. Clone the repository into a new temporary folder. Read README.md, NOTICE.md, SKILL.md and references/runtime-contract.md. Inspect the scripts and tests before running them.
2. Check for Python 3.11+ and PyYAML. Run `python3 -B scripts/engine.py detect`. This only checks available tools; it must not start research or install software.
3. Create a fresh temporary test directory, then run the offline checks with that explicit output directory: `PYTHON_BIN=python3 bash scripts/smoke.sh /absolute/path/to/test-target`. Use a fresh test directory outside my existing skill library. If a prerequisite is missing, explain what is needed before installing it.
4. Install the inspected skill using this agent's supported skill installation method. Preserve existing skills and settings. If topic-brain-builder is already installed, compare the versions and report the proposed update instead of overwriting it.
5. Read back the installed skill and verify its files match the inspected checkout. Tell me it is ready and give me one example request, such as: build a brain on improving my offer using the YouTube creators I learn from.

Stop after installation. Start research only when I provide the topic, questions and source scope. Installation does not train or fine-tune a model.
```

Made by Selr AI.

<!-- Provenance marker: sk-ouc5ru --><!-- Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠ -->
