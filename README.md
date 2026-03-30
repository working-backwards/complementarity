# Complementarity

A thinking tool for people working at the intersection of two knowledge domains. It generates peer-level expressions of design decisions in both domains simultaneously — not as a translation step applied after the work, but as a design methodology used during it.

Neither perspective is primary. Like wave-particle duality, every output is simultaneously a faithful translation and a validation finding. A deep enough translation makes modeling disconnects self-evident to a reader in that register, without needing annotations to point them out.

## Install

```bash
pip install git+https://github.com/working-backwards/complementarity.git
```

This gives you a `complementarity` command you can run from anywhere. Requires Python 3.10+ and the [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude`), which uses your existing Max/Pro subscription — no API key needed.

To upgrade:

```bash
pip install --upgrade git+https://github.com/working-backwards/complementarity.git
```

If you want to use direct API calls instead (`--provider anthropic` or `--provider openai`), also install the relevant SDK:

```bash
pip install anthropic  # for --provider anthropic
pip install openai     # for --provider openai
```

## Setup

**1. Create a config file** in your project repo root:

```bash
cp complementarity.yaml.example /path/to/your-project/complementarity.yaml
```

Edit it to describe your project and perspectives. The perspective labels can be anything — "Academic"/"Business", "Engineering"/"Product", "Legal"/"Technical", "Clinical"/"Operational" — whatever two registers you're working between. The `intended_reader` field is the most important: it defines what "complete" means in each register and drives the specification-gap detection.

See `complementarity.yaml.example` for the full format. The key fields:

```yaml
project:
  name: "Your Project"
  description: "..."
  research_questions:
    - "Question that helps judge which design decisions matter most"

perspectives:
  - label: "Wave"          # any label — this becomes ### Wave in your docs
    domain: "The knowledge domain this perspective operates in"
    intended_reader: >
      Describe the reader fully. What do they expect? What level of
      specification satisfies them? This drives the LLM's completeness
      standard and specification-gap detection.
    analogy_source: "Where to draw analogies from (and where not to)"
    notation_preference: "How to handle notation in this register"
    notation_equations: "How to handle equations (include, omit, translate)"
  - label: "Particle"      # the complementary perspective
    domain: "..."
    intended_reader: "..."
    # ...

calibration_examples:       # optional — sample docs that show good output
  - perspective: "Wave"
    path: "path/to/example_doc.md"
  - perspective: "Particle"
    path: "path/to/example_doc.md"

docs_dir: "docs/design"
```

**2. Create a `.env` file** (optional) in the same directory as `complementarity.yaml`:

```
DEFAULT_PROVIDER=claude-code
DEFAULT_MODEL=claude-sonnet-4-20250514
```

The default provider is `claude-code`, which routes through the Claude Code CLI using your Max/Pro subscription. No API key needed. If you want to use direct API calls, set the provider and key:

```
DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

Add `.env` to your `.gitignore`.

**3. Structure your documents** with perspective subsections under each `##` section, using your label names:

```markdown
## Purpose

### Wave
Content in the first register...

### Particle
(empty — Complementarity will fill this in)
```

If a section already has `###` subsections, demote them to `####` under the perspective marker:

```markdown
## Policy outputs

### Wave
#### 1. ContinueStop
Decision details...
#### 2. SetExecAttention
Attention details...

### Particle
```

## Usage

### Sync an entire document (bootstrapping)

```bash
complementarity sync docs/design/governance.md \
  --from Academic --to Business \
  --config /path/to/complementarity.yaml
```

Generates `### Business` content for every `##` section in the doc.

### Sync a single section (daily workflow)

```bash
complementarity sync docs/design/governance.md \
  --section "Stop logic" --from Academic --to Business \
  --config /path/to/complementarity.yaml
```

Faster, cheaper, and keeps attention on the section you're working on. This is the primary daily interaction — you're stuck on a section, you want the other perspective, you get it for that section only.

### Inspect the prompt before calling the API

```bash
complementarity sync docs/design/governance.md \
  --from Academic --to Business --dry-run \
  --config /path/to/complementarity.yaml
```

Prints the fully assembled prompt to stdout. No API call, no file writes.

### Override provider or model

```bash
# Use direct Anthropic API instead of Claude Code CLI
complementarity sync docs/design/governance.md \
  --from Academic --to Business \
  --provider anthropic --model claude-sonnet-4-20250514 \
  --config /path/to/complementarity.yaml

# Use OpenAI
complementarity sync docs/design/governance.md \
  --from Academic --to Business \
  --provider openai --model gpt-4o \
  --config /path/to/complementarity.yaml
```

### CLI flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--from` | (required) | Source perspective label |
| `--to` | (required) | Target perspective label |
| `--section` | all sections | Sync only the `##` section matching this text |
| `--dry-run` | false | Print prompt, don't call API |
| `--provider` | `claude-code` | `claude-code`, `anthropic`, or `openai` |
| `--model` | from `.env` | Model identifier |
| `--config` | `./complementarity.yaml` | Path to config file |
| `--max-tokens` | 16384 | Max output tokens |

## How it works

1. Loads config and `.env`
2. Parses the document into `##` sections, extracting `### {from}` and `### {to}` content
3. If `--section` is set, filters to matching section(s)
4. Scans for cross-references to other `.md` files in `docs_dir` and includes them as context
5. Loads calibration examples for few-shot context
6. Assembles the prompt: project context + research questions + perspective conventions + calibration examples + cross-doc context + source sections + translation instructions
7. Calls the LLM API
8. Parses the response, matching generated sections back to source headings
9. Inserts generated content into `### {to}` subsections (prompts before overwriting existing content)

### Cross-document context

The tool auto-detects references to other `.md` files in the source document and includes them as read-only context. This helps the LLM maintain consistency across documents. Only one level of references is followed.

### Markers

The LLM may include three types of markers:

- `<!-- inconsistency: ... -->` — Factual disagreements between perspectives (e.g., "3 inputs" in one, "2 inputs" in the other). These are bugs to fix.
- `<!-- specification-gap: ... -->` — A concept is mentioned but not specified to the depth the target register's reader would require. What counts as "sufficient depth" is driven by the `intended_reader` field in your config — different for each perspective.
- `<!-- needs-review: ... -->` — The LLM is uncertain how to express something. Focus editing effort here.

Modeling disconnects (the interesting findings) are not annotated — they should be self-evident from a sufficiently deep translation.

## What it does NOT do

- **Resolve inconsistencies** — it surfaces them for your judgment
- **Detect which sections changed** — it regenerates `--to` sections each run; use `git diff` to track changes
- **Batch-sync multiple files** — one file per command; wrap in a shell loop if needed

## Architecture

`complementarity.py` is a single file. All core functions (`load_config`, `parse_sections`, `assemble_prompt`, `call_llm`, etc.) are importable — the CLI is one interface, but a future Claude Code slash command or Python script can call the same functions directly.
