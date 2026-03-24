# Sync Prompt Template

This is the prompt template used by `complementarity.py`. The code assembles
the prompt programmatically following this structure. Placeholders use
`{{handlebars}}` syntax for readability.

---

## Layer 1: Role and project context

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

## Layer 2: Target perspective conventions

```
The intended reader of the {{to.label}} version is:
{{to.intended_reader}}

Analogy conventions: {{to.analogy_source}}
Notation conventions: {{to.notation_preference}}
{{to.notation_equations}}
```

## Layer 3: Calibration examples (few-shot)

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

## Layer 4: Cross-document context (auto-detected)

```
The following related documents are included for context only.
Use them to ensure the {{to.label}} version is consistent with
how concepts are described elsewhere. Do not translate these.

--- interfaces.md ---
[full content]
--- core_simulator.md ---
[full content]
```

## Layer 5: Source content + instructions

```
Here is the document organized by section. For each section, you are
given the {{from.label}} source content. Some sections also include
existing {{to.label}} content that may contain original material.

## Section: [heading text]

### Source ({{from.label}}):
[source content for this section]

### Existing target ({{to.label}}):
[existing target content, if any]

## Section: [heading text]

### Source ({{from.label}}):
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

6. PRESERVING EXISTING TARGET CONTENT: Some sections include existing
   {{to.label}} content marked "Existing target." This content may
   contain original material written directly in the {{to.label}}
   register — not translated from {{from.label}}, but authored
   independently. Handle it as follows:

   a. Preserve the exact wording of existing target material. Do not
      rephrase, reorganize, compress, or "improve" it. Treat it as
      authored text that the writer chose deliberately.

   b. Identify concepts in the {{from.label}} source that are NOT
      already covered by the existing target content. Translate those
      and add them in a natural position — before, after, or
      interspersed with the existing material, wherever they fit best
      in the section's flow.

   c. If the existing target content already covers a concept from the
      source, do not duplicate it. If the source covers a concept more
      thoroughly than the existing target, add the uncovered aspects as
      new content near the existing treatment — do not modify the
      existing text.

   d. If the existing target content contradicts the source on a
      specific factual claim, preserve both and flag the disagreement:
      <!-- inconsistency: [what disagrees] -->

7. SPECIFICATION GAPS: For each concept in the {{from.label}} source,
   assess whether the {{to.label}} version provides a complete
   specification in its own register — not just whether the concept is
   mentioned. The intended reader of the {{to.label}} version expects:
   {{to.intended_reader}}
   If a concept from the source is acknowledged in the {{to.label}}
   version but not specified to the depth that reader would require,
   flag it:
   <!-- specification-gap: [what is mentioned but not fully specified
   in the {{to.label}} register] -->

8. For sections where a {{to.label}} equivalent should exist but you
   are uncertain how to express it, include your best attempt and mark:
   <!-- needs-review: [what is uncertain] -->

9. Use the EXACT section heading text as provided above. Do not
   rephrase, abbreviate, or reformat headings. The tool matches
   your output to the source document by heading text.

Output format — return ONLY the generated content, one block per
section, using the exact section headings:

## Section: [heading text]
[generated content]
```

## Marker philosophy

- **`<!-- inconsistency: ... -->`** — Factual disagreements between perspectives. These are bugs.
- **`<!-- specification-gap: ... -->`** — A concept is mentioned but not specified to the depth the target register's reader would require. Works bidirectionally: for an academic reader, this might be a missing metric or equation; for a business reader, a missing concrete example or governance implication.
- **`<!-- needs-review: ... -->`** — The LLM's own uncertainty about how to express something.
- **No `<!-- disconnect: ... -->` markers.** Modeling disconnects should be self-evident from a sufficiently deep translation.
