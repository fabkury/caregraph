"""
Editorial output validator.

Checks AI-generated methodology markdown files for:
  - Required sections: Overview, Join Strategy, Known Limitations, Data Quality Notes
  - Minimum section length (50 characters each)
  - Forbidden phrases that indicate AI refusal or hedging
  - Valid markdown structure

Usage:
    from etl.editorial.validate import validate_methodology
    ok, errors = validate_methodology("path/to/file.md")
"""

from __future__ import annotations

import re
from pathlib import Path

REQUIRED_SECTIONS = [
    "Overview",
    "Join Strategy",
    "Known Limitations",
    "Data Quality Notes",
]

MIN_SECTION_LENGTH = 50

FORBIDDEN_PHRASES = [
    "I cannot",
    "As an AI",
    "I'm sorry",
    "I don't have",
    "I am unable",
]


def validate_methodology(file_path: str | Path) -> tuple[bool, list[str]]:
    """Validate a methodology markdown file.

    Returns (True, []) if valid, or (False, [list of error strings]) if invalid.
    """
    file_path = Path(file_path)
    errors: list[str] = []

    # Check file exists
    if not file_path.exists():
        return False, [f"File does not exist: {file_path}"]

    # Read content
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, [f"Cannot read file: {e}"]

    if not content.strip():
        return False, ["File is empty"]

    # Check for forbidden phrases
    content_lower = content.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in content_lower:
            errors.append(f"Forbidden phrase found: \"{phrase}\"")

    # Parse sections: find all ## headings and their content
    # Pattern: ## Heading\n...content until next ## or EOF
    section_pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(section_pattern.finditer(content))

    found_sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        found_sections[heading] = body

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in found_sections:
            errors.append(f"Missing required section: ## {section}")
        else:
            body = found_sections[section]
            if len(body) < MIN_SECTION_LENGTH:
                errors.append(
                    f"Section \"{section}\" is too short "
                    f"({len(body)} chars, minimum {MIN_SECTION_LENGTH})"
                )

    # Check that file doesn't start with a # title heading (the template adds it)
    first_line = content.strip().split("\n")[0].strip()
    if first_line.startswith("# ") and not first_line.startswith("## "):
        errors.append(
            "File starts with a top-level heading (# ...). "
            "The page template adds the title; use only ## headings."
        )

    return (len(errors) == 0, errors)


def validate_all(output_dir: str | Path) -> dict[str, tuple[bool, list[str]]]:
    """Validate all .md files in the output directory.

    Returns {filename: (ok, errors)} for each file.
    """
    output_dir = Path(output_dir)
    results: dict[str, tuple[bool, list[str]]] = {}

    if not output_dir.exists():
        return results

    for md_file in sorted(output_dir.glob("*.md")):
        results[md_file.name] = validate_methodology(md_file)

    return results


if __name__ == "__main__":
    import sys

    output_dir = Path(__file__).resolve().parent / "output"
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])

    results = validate_all(output_dir)
    if not results:
        print(f"No .md files found in {output_dir}")
        sys.exit(1)

    all_ok = True
    for filename, (ok, errs) in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {filename}")
        if errs:
            for e in errs:
                print(f"         - {e}")
            all_ok = False

    sys.exit(0 if all_ok else 1)
