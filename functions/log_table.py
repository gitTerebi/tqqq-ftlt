from __future__ import annotations

from pathlib import Path


def _md_escape(text: str) -> str:
    # Keep it simple: avoid breaking tables if names contain pipes/newlines
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def write_markdown_table_row(
    file_path: str | Path,
    columns: list[str],
    row_label: str,
    row_values: dict[str, str],
) -> None:
    """
    Appends a Markdown table to file_path.
    If the file is empty/new, writes the header first, then the row.

    columns: ordered column names (e.g. ["SPY", "QQQ", "BND", "CASH"])
    row_label: first cell (e.g. "2026-01-24")
    row_values: mapping column -> already-formatted string cell (e.g. {"SPY": "50.0%"})
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    header_cells = ["Date"] + [_md_escape(c) for c in columns]
    sep_cells = ["---"] * len(header_cells)

    row_cells = [_md_escape(row_label)] + [_md_escape(row_values.get(c, "")) for c in columns]

    def line(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |\n"

    is_new_or_empty = (not path.exists()) or (path.stat().st_size == 0)

    with path.open("a", encoding="utf-8", newline="\n") as f:
        if is_new_or_empty:
            f.write(line(header_cells))
            f.write(line(sep_cells))
        f.write(line(row_cells))