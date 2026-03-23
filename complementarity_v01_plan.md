# Complementarity v0.1 — Build Plan

## Context

Complementarity is a thinking tool for people working at the intersection of two knowledge domains. It helps maintain peer-level expressions of design decisions in both domains simultaneously — not as a translation step applied after the work, but as a design methodology used throughout.

Neither perspective is primary. Neither is a simplification of the other. Like wave-particle duality, every output is simultaneously a faithful translation AND a validation finding. A Business perspective that says "stopping a nearly-finished initiative forfeits all value" is both a peer expression of the Academic formalization and a surfacing of a modeling disconnect — without needing an annotation to say so. The depth of the translation is what makes disconnects self-evident to a reader in that register.

The immediate user is building a Monte Carlo governance study (Primordial Soup) that must be credible to both simulation researchers and senior organizational leaders. He discovered during the project that switching between Academic and Business perspectives was his primary problem-solving tool — and that flaws hidden by technical authority in one register become obvious when expressed in the other. He has 21 design docs (~6,400 lines), currently written primarily in the Academic register.

**Why build now:** The study design is still in progress. The dual-perspective methodology is most valuable during design, not after. Waiting until the design is stable means losing the tool during the phase when it catches the most errors.

**Why keep it minimal:** The user will learn what the tool should become by using it. Overbuilding before that learning happens wastes effort and risks rework.

---

## What gets built

Four files in the `complementarity/` project directory:

| File | Purpose |
|------|---------|
| `complementarity.py` | Single-file Python script — all logic, importable functions |
| `sync_prompt.md` | Prompt template with `{{placeholders}}` |
| `.env.example` | Template for API keys and defaults |
| `complementarity.yaml.example` | Template config for new projects |

Plus a working config in the user's study repo:

| File | Location |
|------|----------|
| `complementarity.yaml` | primordial-soup repo root |
| `.env` | primordial-soup repo root (in .gitignore) |

**Not built:** No package, no pip install, no CLI framework (Click), no sidecar, no status command, no template versioning, no git integration, no editor extension. Those are all candidates for v0.2+ if the tool proves useful.

**Architecture note:** Core functions (`load_config`, `parse_sections`, `assemble_prompt`, `call_llm`, etc.) are importable, not wired directly into `main()`. The CLI is one interface; a future Claude Code slash command, VS Code keybinding, or Python script can call the same functions without rewriting anything.

---

## Document format

The user adds perspective subsections to their existing docs. The labels come from the config (e.g., "Academic" and "Business").

### Format for sections WITHOUT existing ### subsections

```markdown
## Purpose

### Academic
This note gives you enough of the model structure — latent state,
observation model, belief dynamics...

### Business
This note gives senior leadership enough context about how the study
is structured to evaluate whether its architecture...
```

### Format for sections WITH existing ### subsections

Existing ### subsections get demoted to #### under the perspective marker:

```markdown
## Policy outputs

### Academic
#### 1. ContinueStop
- `{ action: "ContinueStop", initiative_id: "X", decision: "continue" | "stop" }`
...
#### 2. SetExecAttention
...

### Business
At each decision point, leadership makes three types of choices:
#### Continue or stop
For every active initiative under review, the governance team must make
an explicit call...
#### Allocate executive attention
...
```

### Bootstrapping workflow

1. User opens a doc (e.g., `governance.md`)
2. Adds `### Academic` markers above existing content in each `##` section
3. Adds empty `### Business` markers (or vice versa)
4. Demotes any existing `###` subsections to `####` where needed
5. Runs Complementarity — tool fills in the empty perspective
6. User reviews, edits, iterates

This is done one doc at a time, starting with the highest-priority docs. The user manually reviews every output.

### Recommended sequencing (highest-value docs first)

1. `core_simulator.md` — belief updates, tick mechanics, value realization
2. `governance.md` — stop rules, attention allocation, review semantics
3. `initiative_model.md` — value channels, lifecycle, learning dynamics
4. `calibration_note.md` — empirical grounding and its limits
5. `team_and_resources.md` — team atomicity, ramp, workforce constraints

Lower priority: `index.md`, `architecture.md`, `engineering_standards.md` — structural/implementation docs where perspective-switching adds less.

### Perspective split granularity

The split happens at the `##` section level. Each `##` section gets one `### Academic` and one `### Business` subsection. The user chooses which `##` sections to include — not every section needs both perspectives (e.g., a purely structural section like an index might be skipped).

---

## Config format (`complementarity.yaml`)

```yaml
schema_version: "0.1"

project:
  name: "Primordial Soup"
  description: >
    A discrete-time Monte Carlo study of how governance regimes affect
    long-run organizational value creation.
  research_questions:
    - >
      How does governance patience affect major-win discovery rates
      across different initiative portfolio compositions?
    - >
      Do governance regimes that invest in enablers produce materially
      different long-run capability trajectories?
    - >
      What is the relationship between executive attention allocation
      strategy and the quality of stop/continue decisions?

perspectives:
  - label: "Academic"
    domain: "Formal simulation modeling, operations research, stochastic optimization"
    intended_reader: >
      A professor or researcher in Operations Research or simulation who
      expects precise definitions, formal notation, explicit assumptions,
      and complete technical specification. They do not need motivation or
      analogy. They need precision, completeness, and honest acknowledgment
      of modeling limitations.
    analogy_source: >
      Formal analogues from simulation, stochastic optimization, and decision
      theory only. Do not use organizational or business analogies.
    notation_preference: >
      Use standard OR and simulation notation. Prefer descriptive variable
      names in prose, reserve compact symbols for equations. Define symbols
      on first use.
    notation_equations: >
      Include equations when they are the most precise way to express a
      relationship. Format in code blocks. State domain, range, and
      boundary conditions explicitly.

  - label: "Business"
    domain: "Organizational decision-making, resource allocation, governance design"
    intended_reader: >
      A senior executive or sophisticated organizational practitioner who is
      intellectually serious and analytically capable, but who reasons in
      terms of organizational decisions, resource tradeoffs, and long-run
      value rather than formal models. They do not need things simplified.
      They need every design decision expressed completely and faithfully in
      the language they use to think and act.
    analogy_source: >
      Concrete examples drawn from organizational reality and executive
      experience. Do not use analogies that require knowledge of simulation
      or formal optimization.
    notation_preference: >
      Avoid formal notation entirely. Express relationships in plain language
      that preserves the meaning of the formal version.
    notation_equations: >
      Do not reproduce equations. Express what each equation governs in terms
      of observable organizational consequences.

calibration_examples:
  - perspective: "Academic"
    path: "docs/study/brief_wave.md"
  - perspective: "Business"
    path: "docs/study/brief_particle.md"

docs_dir: "docs/design"
```

**Key design choices:**
- `perspectives` is a list (not `source`/`target`) because neither perspective has primacy. The `--from`/`--to` flags determine direction at runtime.
- `research_questions` are included as context in every prompt so the LLM can reason about whether modeling choices are load-bearing for the study's conclusions.
- `calibration_examples` point to existing briefs that demonstrate what good output looks like in both registers. These are included as few-shot examples in the prompt to calibrate depth and tone.
- `docs_dir` points at a directory. Every `.md` file in it is a candidate for sync.
- The config lives in the study repo root, not in the Complementarity project.

---

## `.env` format

```
DEFAULT_PROVIDER=anthropic
DEFAULT_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Added to `.gitignore`. The tool reads this via `python-dotenv`.

---

## Usage

### Sync an entire document (bootstrapping)

```bash
python complementarity.py sync docs/design/governance.md \
  --from Academic --to Business
```

Generates `### Business` content for every `##` section in the doc. Use this when bootstrapping a doc that doesn't have the target perspective yet, or when regenerating all sections.

### Sync a single section (daily thinking workflow)

```bash
python complementarity.py sync docs/design/governance.md \
  --section "Stop logic" --from Academic --to Business
```

Generates `### Business` content for only the `##` section whose heading contains "Stop logic." Faster (5-10 seconds vs. 30-60 seconds), cheaper (fewer tokens), and keeps attention focused on the section you're working on.

This is the primary daily interaction. You're stuck on a section, you want the other perspective, you get it for that section only.

### What happens (both modes)

1. Loads `complementarity.yaml` and `.env`
2. Reads the doc and parses it into `##` sections
3. If `--section` is set, filters to the matching section(s)
4. For each section, extracts the `### {from}` content
5. Scans the doc for cross-references to other `.md` files in `docs_dir` and reads them as context
6. Loads calibration examples (briefs) for few-shot context
7. Assembles the prompt: template + config values + research questions + calibration examples + source sections + cross-doc context
8. Calls the LLM API (provider and model from `.env` or CLI flags)
9. Parses the LLM response
10. Inserts the generated content into the `### {to}` subsection(s), preserving all `### {from}` content unchanged
11. Writes the updated file

### Dry run (inspect the prompt)

```bash
python complementarity.py sync docs/design/governance.md \
  --from Academic --to Business --dry-run
```

Prints the fully assembled prompt to stdout. No API call, no file writes. Use this to inspect exactly what the LLM will see before spending API credits.

### Override provider/model

```bash
python complementarity.py sync docs/design/governance.md \
  --from Academic --to Business \
  --provider openai --model gpt-4o
```

### CLI flags summary

| Flag | Default | Purpose |
|------|---------|---------|
| `--from` | (required) | Source perspective label |
| `--to` | (required) | Target perspective label |
| `--section` | (all sections) | Sync only the `##` section matching this text |
| `--dry-run` | false | Print prompt, don't call API |
| `--provider` | from .env | `anthropic` or `openai` |
| `--model` | from .env | Model identifier |
| `--config` | `./complementarity.yaml` | Path to config |
| `--max-tokens` | 16384 | Max output tokens |

---

## Prompt design

The prompt has one job: produce a peer perspective so complete and faithful that modeling disconnects become self-evident to a reader in the target register. Validation is not an annotation layer on top of translation — it is what translation does when done at sufficient depth.

The prompt template (`sync_prompt.md`) assembles five layers:

### Layer 1: Role and project context

```
You are maintaining a pair of complementary documents for the
{{project.name}} project. The two documents express the same content
from two peer perspectives: {{from.label}} and {{to.label}}. Neither
is a simplification of the other. Both are complete and faithful
expressions of the same design decisions in their respective registers.

{{#if project.description}}
Project context: {{project.description}}
{{/if}}

{{#if project.research_questions}}
The study's research questions (use these to judge which design
decisions are most consequential):
{{#each project.research_questions}}
- {{this}}
{{/each}}
{{/if}}
```

### Layer 2: Target perspective conventions

```
The intended reader of the {{to.label}} version is:
{{to.intended_reader}}

Analogy conventions: {{to.analogy_source}}
Notation conventions: {{to.notation_preference}}
{{to.notation_equations}}
```

### Layer 3: Calibration examples (few-shot)

```
{{#if calibration_examples}}
The following are examples of what good output looks like in both
registers for this project. Use them to calibrate depth, tone, and
completeness — not as templates to copy.

--- Example: {{from.label}} register ---
[excerpt from the from-perspective brief]

--- Example: {{to.label}} register ---
[excerpt from the to-perspective brief]
{{/if}}
```

### Layer 4: Cross-document context (auto-detected)

```
The following related documents are included for context only.
Use them to ensure the {{to.label}} version is consistent with
how concepts are described elsewhere. Do not translate these.

--- interfaces.md ---
[full content]
--- core_simulator.md ---
[full content]
```

### Layer 5: Source content + instructions

```
Here is the document organized by section. For each section, you are
given the {{from.label}} content.

## Section: [heading text]
[source content for this section]

## Section: [heading text]
[source content for this section]

...

Produce the {{to.label}} version for each section following these rules:

1. Produce a peer perspective so complete and faithful that a reader
   in this register would notice any modeling choice that doesn't
   correspond to their domain reality. Do not annotate or explain
   disconnects — express each concept fully and let the reader judge.

2. Cover every section. Do not skip sections because they seem
   technical or domain-specific. Every design decision in the source
   has a target equivalent, even if expressing it requires effort.

3. Prefer completeness over brevity. If expressing a concept fully
   in the target register requires more words than the source used,
   use them. Do not compress meaning to match source length.

4. Express each decision in the language the intended reader uses to
   reason and act. Use concrete examples from {{to.domain}} where they
   help the reader recognize the concept in their own experience.

5. Do not simplify or omit meaning. If a concept is important enough
   to appear in the {{from.label}} version, it is important enough to
   appear fully in the {{to.label}} version.

6. If both perspectives already exist and they factually disagree on
   a specific claim (e.g., number of inputs, direction of an effect),
   flag the disagreement:
   <!-- inconsistency: [what disagrees] -->

7. For sections where a {{to.label}} equivalent should exist but you
   are uncertain how to express it, include your best attempt and mark:
   <!-- needs-review: [what is uncertain] -->

8. Use the EXACT section heading text as provided above. Do not
   rephrase, abbreviate, or reformat headings. The tool matches
   your output to the source document by heading text.

Output format — return ONLY the generated content, one block per
section, using the exact section headings:

## Section: [heading text]
[generated content]
```

### Marker philosophy

- **`<!-- inconsistency: ... -->`** — Factual disagreements between perspectives (3 inputs vs. 2 inputs). These are bugs. A deep translation doesn't make a factual error self-evident — it faithfully translates the wrong number. Markers are necessary here.
- **`<!-- needs-review: ... -->`** — The LLM's own uncertainty. "I'm not sure how to express this in business terms" tells the user where to focus editing effort.
- **No `<!-- disconnect: ... -->` or `<!-- load-bearing: ... -->` markers.** Modeling disconnects (completion-gated value, attention-modulated execution, etc.) should be self-evident from a sufficiently deep translation. If the reader can't see the disconnect, the translation isn't deep enough — adding a marker doesn't fix the real problem.

---

## Cross-document context

The tool scans the source document for references to other `.md` files (regex pattern: word characters + `.md`). For each match that corresponds to a file in `docs_dir`, the tool reads that file and includes it as read-only context in the prompt.

For governance.md, this would auto-include: `interfaces.md`, `core_simulator.md`, `review_and_reporting.md`, `design_decisions.md`, `architecture.md`.

**Token budget:** The referenced docs for governance.md total ~2,200 lines. Combined with governance.md itself (~640 lines), calibration examples (~1,000 lines), and the prompt template, the total input for a full-doc sync is roughly 4,000-5,000 lines — well within 200K token context windows. For `--section` mode (the daily workflow), the input is much smaller.

**Token budget safeguard:** Before calling the LLM, the tool estimates the assembled prompt's token count (approximate: characters / 3.5). If the estimate exceeds 100,000 tokens, the tool prints a warning suggesting the user use `--section` mode for smaller, faster calls. This is a warning, not a hard block — the user can proceed if they want the full-doc sync. If token limits become a recurring problem, the first thing to reduce is calibration examples (excerpt rather than include in full).

**Limitation:** Only one level of reference is followed. Transitive references not explicitly mentioned in the source doc are not included. This is acceptable for v0.1.

---

## Scope and limitations

### What Complementarity v0.1 does
- Generates one perspective from the other, for a single document or single section
- Translates bidirectionally — `--from Academic --to Business` and `--from Business --to Academic` are equally valid
- Produces peer perspectives deep enough that modeling disconnects are self-evident to the reader
- Includes cross-referenced docs as context automatically
- Uses calibration examples (existing briefs) for output quality
- Includes research questions as context for evaluating consequence
- Flags factual inconsistencies between perspectives (`<!-- inconsistency: ... -->`)
- Marks uncertain translations (`<!-- needs-review: ... -->`)
- Shows the exact prompt via `--dry-run` before spending API credits
- Supports both Anthropic and OpenAI APIs
- Supports section-level sync (`--section`) for the daily thinking workflow

### What it does NOT do
- **Resolve inconsistencies** — it surfaces them for user judgment
- **Detect which sections changed since last sync** — it regenerates the `--to` section(s) each run. Git diff is the user's tool for tracking changes.
- **Preserve manual edits to --to sections** — a sync overwrites the targeted `--to` content. If you edited Business sections you want to keep, sync the other direction first or back up the file.
- **Batch-sync multiple files** — one file per command. Wrap in a shell loop if needed.
- **Guarantee correctness** — the LLM produces a first draft. The user must review every output. "Competent" is not "peer-level" without human editing.
- **Handle conflicts when both perspectives were edited** — the user specifies direction; the `--from` side wins.
- **Provide editor integration** — v0.1 is CLI only. The importable architecture supports future Claude Code or VS Code integration.
- **Template versioning, sidecar metadata, status reporting** — all deferred to v0.2+.

### Known risks
1. **Overwriting --to edits:** The tool replaces the targeted `--to` subsection(s) on every run. Mitigation: the tool prints the current content of each `--to` subsection it's about to overwrite, so the user sees what they'll lose before confirming (y/n/all). With `--section`, the blast radius is limited to one section. The user can also use `git diff` after to review changes.
2. **LLM quality variance:** Different models produce different depth. The calibration examples and `--dry-run` flag help iterate on quality before committing to a full doc sync.
3. **Cross-reference completeness:** Auto-detection catches explicit filename references but misses conceptual dependencies not mentioned in the source doc.
4. **Translation depth:** The prompt asks for depth sufficient that disconnects are self-evident. Whether the LLM achieves this depends on the model and the complexity of the source material. The user must evaluate: "would a practitioner in the target register notice the same things an expert would?" If not, the translation needs editing or the model needs upgrading.

---

## Implementation details

### Dependencies

```
anthropic>=0.25.0
openai>=1.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

No CLI framework (argparse only). No package structure. Single file with importable functions.

### Core functions (complementarity.py)

All functions are importable — `main()` is the CLI entry point, but every function below can be called independently by future integrations (Claude Code slash command, VS Code task, Python script).

```
load_config(path) -> dict
    Load and validate complementarity.yaml. Validates required fields,
    checks that perspective labels are distinct, resolves docs_dir.

load_env() -> dict
    Load .env file. Returns dict with provider, model, API keys.

parse_sections(doc_text, from_label, to_label) -> list[Section]
    Split doc by ## headings. For each section, extract the
    ### {from_label} and ### {to_label} content blocks.
    Section = {heading, from_content, to_content, raw_text, start_line, end_line}

filter_sections(sections, section_query) -> list[Section]
    If section_query is set, return only sections whose heading
    contains the query string (case-insensitive substring match).
    If no match, exit with error listing available headings.

detect_cross_references(doc_text, docs_dir) -> list[path]
    Scan for *.md filename references, return paths of files that
    exist in docs_dir.

load_calibration_examples(config) -> dict
    Read the calibration example files specified in config.
    Returns {perspective_label: content} for prompt assembly.

assemble_prompt(config, sections, cross_refs, calibration,
                from_label, to_label) -> str
    Fill template placeholders, attach research questions,
    calibration examples, source sections, and cross-doc context.

call_llm(prompt, provider, model, api_key, max_tokens) -> str
    Dispatch to Anthropic or OpenAI. Return response text.
    Raises on API error with clear message.

parse_response(response_text, source_headings) -> list[{heading, content}]
    Extract per-section generated content from LLM response.
    Match response sections to source sections by heading text.
    First attempts exact match; falls back to case-insensitive
    substring match with a warning. Unmatched response sections
    are reported as errors (the LLM rephrased a heading).

write_updated_doc(original_path, sections, generated, to_label) -> str
    Insert generated content into ### {to_label} subsections.
    Preserve all other content unchanged. Returns the updated text.
    Before writing, for each section being overwritten:
      - Prints the section heading
      - Prints the CURRENT content of the ### {to_label} subsection
        that will be replaced (so the user sees what they're about
        to lose)
      - Prompts for confirmation (y/n/all)
    "all" confirms remaining sections without further prompts.

main()
    Argparse CLI. Wires everything together.
```

### Markdown parsing approach

- Split on lines matching `^## ` (level-2 headings)
- Within each section, find `### {label}` boundaries
- Content between `### {label}` and the next `### ` (or end of section) is that perspective's content
- This is simple string splitting, not a full markdown parser
- Edge cases: sections with no perspective markers are passed through unchanged
- `--section` filtering happens after parsing, before prompt assembly

### LLM dispatch

```python
def call_llm(prompt, provider, model, api_key, max_tokens):
    if provider == "anthropic":
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    elif provider == "openai":
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

---

## Verification

### Test 1: Dry run on governance.md
```bash
python complementarity.py sync docs/design/governance.md \
  --from Academic --to Business --dry-run
```
**Expected:** Prints the full assembled prompt including:
- Research questions from config
- Perspective definitions from config
- Calibration examples (excerpts from briefs)
- All Academic sections from governance.md
- Cross-referenced docs (interfaces.md, core_simulator.md, etc.)
- Translation instructions

**Check:** The prompt is coherent, complete, and contains no placeholder artifacts.

### Test 2: Section-level sync on a small doc
```bash
python complementarity.py sync docs/design/canonical_core.md \
  --section "invariants" --from Academic --to Business
```
**Expected:** Only the matching section gets a `### Business` subsection. Academic content unchanged. Other sections untouched.

**Check:** `git diff` shows additions only in the targeted section.

### Test 3: Full-doc sync (bootstrapping)
```bash
python complementarity.py sync docs/design/canonical_core.md \
  --from Academic --to Business
```
**Expected:** All `##` sections get `### Business` content. Academic content unchanged.

**Check:** `git diff` shows only additions (Business subsections) and no modifications to Academic content.

### Test 4: Reverse direction
After Test 3, edit a Business subsection, then:
```bash
python complementarity.py sync docs/design/canonical_core.md \
  --from Business --to Academic
```
**Expected:** Academic subsections are regenerated from the (edited) Business content.

### Test 5: Inconsistency detection
Deliberately introduce a factual disagreement between perspectives in a test doc (e.g., "3 inputs" in Business, "2 inputs" in Academic). Run sync. Verify the LLM flags it with `<!-- inconsistency: ... -->`.

### Test 6: Translation depth
Run sync on a section containing a known modeling simplification (e.g., completion-gated value). Read the Business output. Does a reader in the business register notice the disconnect without any annotation? If yes, the translation is deep enough. If no, iterate on the prompt or model.

---

## What the user needs to do before running

1. Create `.env` in primordial-soup repo root with API key(s)
2. Create `complementarity.yaml` in primordial-soup repo root (based on the config example above)
3. Verify the calibration example paths point to the existing Academic and Business briefs
4. Pick one doc to start with (recommend `canonical_core.md` — shortest at 87 lines)
5. Add `### Academic` markers above existing content in each `##` section
6. Add empty `### Business` markers after each Academic block
7. Demote any existing `###` subsections to `####` where needed
8. Commit the restructured doc (so you can `git diff` after sync)
9. Run `--dry-run` first to inspect the prompt
10. Run the sync
11. Review, edit, iterate

---

## Future directions (out of scope, noted for reference)

- **Claude Code integration:** Slash command like `/perspective "Stop logic" to Business` that calls the core functions directly. Most natural v0.2 path given the user's existing workflow.
- **Change detection:** Use git diff to identify which sections changed since last sync, enabling selective re-sync.
- **Conflict handling:** Warn when both perspectives of a section have been edited since last sync.
- **Batch sync:** Process multiple files in one command.
- **Sidecar metadata:** Track provider, model, template version per sync.
- **Template versioning:** Version the prompt template and record which version produced each output.
