"""Get a cell value from a PDF table by row and column index.

Usage:
    python get_pdf_table_cell.py <file.pdf> <row> <col>

Example:
    python get_pdf_table_cell.py invoice.pdf 1 0
"""

import re
import sys
from pathlib import Path
from landingai_ade import LandingAIADE

def get_pdf_cell(file_path: str, row: int, col: int, table_index: int = 0) -> str:
    client = LandingAIADE()
    response = client.parse(document=Path(file_path))

    tables = [c for c in response.chunks if c.type == "table"]
    if not tables:
        raise ValueError("No tables found in document")
    if table_index >= len(tables):
        raise ValueError(f"Table index {table_index} out of range ({len(tables)} tables found)")
    table = tables[table_index]

    # Parse HTML rows and cells into a (row, col) grid
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table.markdown, re.DOTALL)
    grid = {}
    for r, row_html in enumerate(rows):
        for c, m in enumerate(re.finditer(
            r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL
        )):
            grid[(r, c)] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

    if (row, col) not in grid:
        raise KeyError(f"No cell at ({row}, {col}). Available: {sorted(grid.keys())}")

    return grid[(row, col)]

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    file_path, row, col = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    value = get_pdf_cell(file_path, row, col)
    print(f"Row {row}, Col {col}: {value}")
