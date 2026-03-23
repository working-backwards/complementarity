#!/usr/bin/env python3
"""Complementarity — dual-perspective sync tool for design documents.

Maintains peer-level expressions of design decisions in two knowledge domains.
Neither perspective is primary. Deep translation IS validation — modeling
disconnects become self-evident in the target register.

All core functions are importable for use by future integrations
(Claude Code slash command, VS Code task, Python script).
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass
class Section:
    """A ## section from a design document."""
    heading: str
    from_content: str | None
    to_content: str | None
    raw_text: str
    start_line: int  # inclusive, 0-indexed
    end_line: int    # exclusive, 0-indexed


def load_config(path: str = "complementarity.yaml") -> dict:
    """Load and validate complementarity.yaml.

    Validates required fields, checks that perspective labels are distinct,
    resolves docs_dir relative to the config file location.
    """
    p = Path(path)
    if not p.exists():
        print(f"Error: Config file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(p) as f:
        config = yaml.safe_load(f)

    # Validate required fields
    for field in ("project", "perspectives"):
        if field not in config:
            print(f"Error: Missing required config field: {field}", file=sys.stderr)
            sys.exit(1)

    if "name" not in config["project"]:
        print("Error: project.name is required", file=sys.stderr)
        sys.exit(1)

    if len(config["perspectives"]) < 2:
        print("Error: At least two perspectives required", file=sys.stderr)
        sys.exit(1)

    labels = [p["label"] for p in config["perspectives"]]
    if len(labels) != len(set(labels)):
        print("Error: Perspective labels must be distinct", file=sys.stderr)
        sys.exit(1)

    # Resolve docs_dir relative to config file location
    if "docs_dir" in config:
        config["_docs_dir_resolved"] = str(p.parent / config["docs_dir"])

    config["_config_dir"] = str(p.parent)

    return config


def load_env(config_dir: str = ".") -> dict:
    """Load .env file. Returns dict with provider, model, API keys."""
    env_path = Path(config_dir) / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return {
        "provider": os.getenv("DEFAULT_PROVIDER", "anthropic"),
        "model": os.getenv("DEFAULT_MODEL", "claude-sonnet-4-20250514"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
    }


def _extract_perspective(section_lines: list[str], label: str) -> str | None:
    """Extract content under ### {label} within a section's lines."""
    marker = f"### {label}"
    in_perspective = False
    content_lines = []

    for line in section_lines:
        if line.strip() == marker:
            in_perspective = True
            continue
        elif in_perspective and re.match(r"^### ", line):
            break
        elif in_perspective:
            content_lines.append(line)

    if not content_lines:
        return None

    content = "\n".join(content_lines).strip()
    return content if content else None


def parse_sections(doc_text: str, from_label: str, to_label: str) -> list[Section]:
    """Split doc by ## headings. For each section, extract the
    ### {from_label} and ### {to_label} content blocks.
    """
    lines = doc_text.split("\n")
    sections = []

    # Find all ## heading line indices
    heading_indices = []
    for i, line in enumerate(lines):
        if re.match(r"^## ", line):
            heading_indices.append(i)

    for idx, start in enumerate(heading_indices):
        end = heading_indices[idx + 1] if idx + 1 < len(heading_indices) else len(lines)
        heading = lines[start][3:].strip()
        section_lines = lines[start:end]
        raw_text = "\n".join(section_lines)

        from_content = _extract_perspective(section_lines, from_label)
        to_content = _extract_perspective(section_lines, to_label)

        sections.append(Section(
            heading=heading,
            from_content=from_content,
            to_content=to_content,
            raw_text=raw_text,
            start_line=start,
            end_line=end,
        ))

    return sections


def filter_sections(sections: list[Section], section_query: str) -> list[Section]:
    """If section_query is set, return only sections whose heading contains
    the query string (case-insensitive substring match). If no match, exit
    with error listing available headings.
    """
    matches = [s for s in sections if section_query.lower() in s.heading.lower()]

    if not matches:
        available = [s.heading for s in sections]
        print(f"Error: No section matching '{section_query}'.", file=sys.stderr)
        print("Available sections:", file=sys.stderr)
        for h in available:
            print(f"  - {h}", file=sys.stderr)
        sys.exit(1)

    return matches


def detect_cross_references(doc_text: str, docs_dir: str) -> list[str]:
    """Scan for *.md filename references, return paths of files that
    exist in docs_dir.
    """
    pattern = r"\b([\w.-]+\.md)\b"
    refs = set(re.findall(pattern, doc_text))

    found = []
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        return found

    for ref in sorted(refs):
        candidate = docs_path / ref
        if candidate.exists():
            found.append(str(candidate))

    return found


def load_calibration_examples(config: dict) -> dict:
    """Read the calibration example files specified in config.
    Returns {perspective_label: content} for prompt assembly.
    """
    examples = {}
    config_dir = config.get("_config_dir", ".")

    for ex in config.get("calibration_examples", []):
        label = ex["perspective"]
        path = Path(config_dir) / ex["path"]
        if path.exists():
            examples[label] = path.read_text()
        else:
            print(f"Warning: Calibration example not found: {path}", file=sys.stderr)

    return examples


def _get_perspective(config: dict, label: str) -> dict | None:
    """Find a perspective config by label."""
    for p in config["perspectives"]:
        if p["label"] == label:
            return p
    return None


def assemble_prompt(config: dict, sections: list[Section], cross_refs: list[str],
                    calibration: dict, from_label: str, to_label: str) -> str:
    """Fill template placeholders, attach research questions, calibration
    examples, source sections, and cross-doc context.

    Builds the prompt programmatically following the structure documented
    in sync_prompt.md.
    """
    from_perspective = _get_perspective(config, from_label)
    to_perspective = _get_perspective(config, to_label)

    if not from_perspective or not to_perspective:
        labels = [p["label"] for p in config["perspectives"]]
        print(f"Error: Perspective not found. Available: {labels}", file=sys.stderr)
        sys.exit(1)

    parts = []

    # Layer 1: Role and project context
    parts.append(
        f"You are maintaining a pair of complementary documents for the "
        f"{config['project']['name']} project. The two documents express the same "
        f"content from two peer perspectives: {from_label} and {to_label}. Neither "
        f"is a simplification of the other. Both are complete and faithful expressions "
        f"of the same design decisions in their respective registers."
    )

    if config["project"].get("description"):
        parts.append(f"\nProject context: {config['project']['description'].strip()}")

    research_questions = config["project"].get("research_questions", [])
    if research_questions:
        parts.append(
            "\nThe study's research questions (use these to judge which design "
            "decisions are most consequential):"
        )
        for q in research_questions:
            parts.append(f"- {q.strip()}")

    # Layer 2: Target perspective conventions
    parts.append(f"\nThe intended reader of the {to_label} version is:")
    parts.append(to_perspective["intended_reader"].strip())
    parts.append(f"\nAnalogy conventions: {to_perspective.get('analogy_source', '').strip()}")
    parts.append(f"Notation conventions: {to_perspective.get('notation_preference', '').strip()}")
    if to_perspective.get("notation_equations"):
        parts.append(to_perspective["notation_equations"].strip())

    # Layer 3: Calibration examples (few-shot)
    if calibration:
        parts.append(
            "\nThe following are examples of what good output looks like in both "
            "registers for this project. Use them to calibrate depth, tone, and "
            "completeness — not as templates to copy."
        )
        if from_label in calibration:
            parts.append(f"\n--- Example: {from_label} register ---")
            parts.append(calibration[from_label])
        if to_label in calibration:
            parts.append(f"\n--- Example: {to_label} register ---")
            parts.append(calibration[to_label])

    # Layer 4: Cross-document context (auto-detected)
    if cross_refs:
        parts.append(
            f"\nThe following related documents are included for context only. "
            f"Use them to ensure the {to_label} version is consistent with how "
            f"concepts are described elsewhere. Do not translate these."
        )
        for ref_path in cross_refs:
            filename = Path(ref_path).name
            content = Path(ref_path).read_text()
            parts.append(f"\n--- {filename} ---")
            parts.append(content)

    # Layer 5: Source content + instructions
    parts.append(
        f"\nHere is the document organized by section. For each section, you are "
        f"given the {from_label} content."
    )

    for section in sections:
        if section.from_content:
            parts.append(f"\n## Section: {section.heading}")
            parts.append(section.from_content)

    parts.append(f"""
Produce the {to_label} version for each section following these rules:

1. Produce a peer perspective so complete and faithful that a reader \
in this register would notice any modeling choice that doesn't \
correspond to their domain reality. Do not annotate or explain \
disconnects — express each concept fully and let the reader judge.

2. Cover every section. Do not skip sections because they seem \
technical or domain-specific. Every design decision in the source \
has a target equivalent, even if expressing it requires effort.

3. Prefer completeness over brevity. If expressing a concept fully \
in the target register requires more words than the source used, \
use them. Do not compress meaning to match source length.

4. Express each decision in the language the intended reader uses to \
reason and act. Use concrete examples from {to_perspective['domain']} \
where they help the reader recognize the concept in their own experience.

5. Do not simplify or omit meaning. If a concept is important enough \
to appear in the {from_label} version, it is important enough to \
appear fully in the {to_label} version.

6. If both perspectives already exist and they factually disagree on \
a specific claim (e.g., number of inputs, direction of an effect), \
flag the disagreement:
   <!-- inconsistency: [what disagrees] -->

7. For sections where a {to_label} equivalent should exist but you \
are uncertain how to express it, include your best attempt and mark:
   <!-- needs-review: [what is uncertain] -->

8. Use the EXACT section heading text as provided above. Do not \
rephrase, abbreviate, or reformat headings. The tool matches \
your output to the source document by heading text.

Output format — return ONLY the generated content, one block per \
section, using the exact section headings:

## Section: [heading text]
[generated content]""")

    return "\n".join(parts)


def call_llm(prompt: str, provider: str, model: str, api_key: str, max_tokens: int) -> str:
    """Dispatch to Anthropic or OpenAI. Return response text.
    Raises on API error with clear message.
    """
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    elif provider == "openai":
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    else:
        print(f"Error: Unknown provider '{provider}'. Use 'anthropic' or 'openai'.",
              file=sys.stderr)
        sys.exit(1)


def parse_response(response_text: str, source_headings: list[str]) -> list[dict]:
    """Extract per-section generated content from LLM response.

    Match response sections to source sections by heading text.
    First attempts exact match; falls back to case-insensitive
    substring match with a warning.
    """
    pattern = r"^## Section:\s*(.+)$"
    parts = re.split(pattern, response_text, flags=re.MULTILINE)

    # parts[0] is preamble (before first heading), then alternating heading/content
    generated = []
    i = 1
    while i < len(parts) - 1:
        resp_heading = parts[i].strip()
        resp_content = parts[i + 1].strip()

        # Try exact match first
        matched = None
        for src_heading in source_headings:
            if resp_heading == src_heading:
                matched = src_heading
                break

        # Fall back to case-insensitive substring match
        if matched is None:
            for src_heading in source_headings:
                if (resp_heading.lower() in src_heading.lower()
                        or src_heading.lower() in resp_heading.lower()):
                    matched = src_heading
                    print(f"Warning: Fuzzy-matched response heading "
                          f"'{resp_heading}' to '{src_heading}'", file=sys.stderr)
                    break

        if matched is None:
            print(f"Warning: Could not match response heading "
                  f"'{resp_heading}' to any source section", file=sys.stderr)
        else:
            generated.append({"heading": matched, "content": resp_content})

        i += 2

    return generated


def write_updated_doc(original_path: str, sections: list[Section],
                      generated: list[dict], to_label: str) -> str:
    """Insert generated content into ### {to_label} subsections.

    Preserves all other content unchanged. Before writing, for each
    section being overwritten, prints the current content and prompts
    for confirmation (y/n/all). Returns the updated document text.
    """
    original_text = Path(original_path).read_text()
    lines = original_text.split("\n")

    gen_map = {g["heading"]: g["content"] for g in generated}

    # Confirm overwrites for sections that have existing to_label content
    confirmed_all = False
    confirmed_headings = set()

    for section in sections:
        if section.heading not in gen_map:
            continue
        if section.to_content and not confirmed_all:
            print(f"\n--- Section: {section.heading} ---")
            print(f"Current ### {to_label} content that will be replaced:")
            print(section.to_content[:500])
            if len(section.to_content) > 500:
                print(f"  ... ({len(section.to_content)} chars total)")

            while True:
                response = input("\nOverwrite? (y/n/all): ").strip().lower()
                if response in ("y", "n", "all"):
                    break
                print("Please enter y, n, or all.")

            if response == "all":
                confirmed_all = True
                confirmed_headings.add(section.heading)
            elif response == "y":
                confirmed_headings.add(section.heading)
            # 'n' means skip this section
        else:
            # No existing content to overwrite — no confirmation needed
            confirmed_headings.add(section.heading)

    # Process sections in reverse order to maintain valid line numbers
    for section in reversed(sections):
        if section.heading not in gen_map:
            continue
        if section.heading not in confirmed_headings:
            continue

        new_content = gen_map[section.heading]
        to_marker = f"### {to_label}"

        # Find ### {to_label} within this section's line range
        to_marker_line = None
        to_content_end = None

        for i in range(section.start_line, section.end_line):
            if lines[i].strip() == to_marker:
                to_marker_line = i
            elif to_marker_line is not None and re.match(r"^### ", lines[i]):
                to_content_end = i
                break
            elif to_marker_line is not None and re.match(r"^## ", lines[i]):
                to_content_end = i
                break

        if to_marker_line is not None:
            # Replace existing content
            if to_content_end is None:
                to_content_end = section.end_line
            replacement = [to_marker]
            replacement.extend(new_content.split("\n"))
            replacement.append("")
            lines[to_marker_line:to_content_end] = replacement
        else:
            # Insert new ### {to_label} at end of section
            insert_pos = section.end_line
            insertion = ["", to_marker]
            insertion.extend(new_content.split("\n"))
            insertion.append("")
            lines[insert_pos:insert_pos] = insertion

    return "\n".join(lines)


def main():
    """CLI entry point. Wires together config, parsing, prompt assembly,
    LLM dispatch, response parsing, and document update.
    """
    parser = argparse.ArgumentParser(
        description="Complementarity — dual-perspective sync for design documents",
    )
    subparsers = parser.add_subparsers(dest="command")

    sync_parser = subparsers.add_parser("sync", help="Sync perspectives in a document")
    sync_parser.add_argument("file", help="Path to the markdown document")
    sync_parser.add_argument("--from", dest="from_label", required=True,
                             help="Source perspective label")
    sync_parser.add_argument("--to", dest="to_label", required=True,
                             help="Target perspective label")
    sync_parser.add_argument("--section",
                             help="Sync only the section matching this text")
    sync_parser.add_argument("--dry-run", action="store_true",
                             help="Print prompt without calling API")
    sync_parser.add_argument("--provider",
                             help="LLM provider (anthropic or openai)")
    sync_parser.add_argument("--model", help="Model identifier")
    sync_parser.add_argument("--config", default="complementarity.yaml",
                             help="Path to config file")
    sync_parser.add_argument("--max-tokens", type=int, default=16384,
                             help="Max output tokens")

    args = parser.parse_args()

    if args.command != "sync":
        parser.print_help()
        sys.exit(1)

    # Load config and env
    config = load_config(args.config)
    env = load_env(config["_config_dir"])

    # Determine provider and model
    provider = args.provider or env["provider"]
    model = args.model or env["model"]

    # Get API key
    if provider == "anthropic":
        api_key = env["anthropic_api_key"]
    elif provider == "openai":
        api_key = env["openai_api_key"]
    else:
        print(f"Error: Unknown provider '{provider}'", file=sys.stderr)
        sys.exit(1)

    if not api_key and not args.dry_run:
        print(f"Error: No API key found for {provider}. Set it in .env.",
              file=sys.stderr)
        sys.exit(1)

    # Read and parse document
    doc_path = Path(args.file)
    if not doc_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    doc_text = doc_path.read_text()
    sections = parse_sections(doc_text, args.from_label, args.to_label)

    if not sections:
        print("Error: No ## sections found in document.", file=sys.stderr)
        sys.exit(1)

    # Filter sections if --section specified
    if args.section:
        sections = filter_sections(sections, args.section)

    # Check that at least some sections have from_content
    sections_with_content = [s for s in sections if s.from_content]
    if not sections_with_content:
        print(f"Error: No sections have ### {args.from_label} content.",
              file=sys.stderr)
        sys.exit(1)

    # Detect cross-references
    docs_dir = config.get("_docs_dir_resolved", ".")
    cross_refs = detect_cross_references(doc_text, docs_dir)

    # Remove the source file itself from cross-references
    source_abs = str(doc_path.resolve())
    cross_refs = [r for r in cross_refs if str(Path(r).resolve()) != source_abs]

    # Load calibration examples
    calibration = load_calibration_examples(config)

    # Assemble prompt
    prompt = assemble_prompt(
        config, sections_with_content, cross_refs, calibration,
        args.from_label, args.to_label,
    )

    # Token estimate warning
    estimated_tokens = len(prompt) / 3.5
    if estimated_tokens > 100_000:
        print(f"Warning: Estimated prompt size is ~{int(estimated_tokens):,} tokens.",
              file=sys.stderr)
        print("Consider using --section for a smaller, faster call.",
              file=sys.stderr)

    # Dry run mode
    if args.dry_run:
        print(prompt)
        return

    # Call LLM
    print(f"Calling {provider}/{model}...", file=sys.stderr)
    response_text = call_llm(prompt, provider, model, api_key, args.max_tokens)

    # Parse response
    source_headings = [s.heading for s in sections_with_content]
    generated = parse_response(response_text, source_headings)

    if not generated:
        print("Error: Could not parse any sections from LLM response.",
              file=sys.stderr)
        print("Raw response:", file=sys.stderr)
        print(response_text[:1000], file=sys.stderr)
        sys.exit(1)

    print(f"Generated {len(generated)} section(s).", file=sys.stderr)

    # Write updated document
    updated_text = write_updated_doc(
        str(doc_path), sections, generated, args.to_label,
    )

    doc_path.write_text(updated_text)
    print(f"Updated {args.file}", file=sys.stderr)


if __name__ == "__main__":
    main()
