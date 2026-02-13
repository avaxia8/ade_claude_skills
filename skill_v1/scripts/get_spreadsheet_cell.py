"""Get a cell value from a spreadsheet by cell reference.

Usage:
    python get_spreadsheet_cell.py <file.xlsx> <cell_id>

Example:
    python get_spreadsheet_cell.py report.xlsx "Sheet 1-B2"
"""

import re
import sys
from pathlib import Path
from landingai_ade import LandingAIADE

def get_spreadsheet_cell(file_path: str, cell_id: str) -> str:
    client = LandingAIADE()
    response = client.parse(document=Path(file_path))

    tables = [c for c in response.chunks if c.type == "table"]
    if not tables:
        raise ValueError("No tables found in spreadsheet")

    # Search all table chunks for the cell ID
    for table in tables:
        cell_text = {}
        for m in re.finditer(
            r'<td[^>]*\bid=["\']([^"\']+)["\'][^>]*>(.*?)</td>',
            table.markdown,
            re.DOTALL,
        ):
            cell_text[m.group(1)] = re.sub(r"<[^>]+>", "", m.group(2)).strip()

        if cell_id in cell_text:
            return cell_text[cell_id]

    available = []
    for table in tables:
        for m in re.finditer(r'<td[^>]*\bid=["\']([^"\']+)["\']', table.markdown):
            available.append(m.group(1))
    raise KeyError(f"Cell '{cell_id}' not found. Available IDs: {available[:10]}...")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    file_path, cell_id = sys.argv[1], sys.argv[2]
    value = get_spreadsheet_cell(file_path, cell_id)
    print(f"{cell_id}: {value}")
