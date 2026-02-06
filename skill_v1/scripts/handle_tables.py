#!/usr/bin/env python3
"""
Table handling examples for LandingAI ADE
Working with table cells, positions, and merged cells
"""

from pathlib import Path
from landingai_ade import LandingAIADE
import pandas as pd
import json

def analyze_table_structure():
    """Analyze table structure in a document"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("document_with_tables.pdf"))
    
    # Find all table-related groundings
    tables = {}
    cells = {}
    
    for gid, grounding in response.grounding.items():
        if grounding.type == "table":
            tables[gid] = grounding
        elif grounding.type == "tableCell":
            cells[gid] = grounding
    
    print(f"Document contains {len(tables)} tables")
    
    # Analyze each table
    for table_id, table in tables.items():
        print(f"\nTable {table_id}:")
        print(f"  Page: {table.page}")
        print(f"  Position: ({table.box.left:.2f}, {table.box.top:.2f})")
        
        # Find cells belonging to this table
        table_cells = []
        for cell_id, cell in cells.items():
            if hasattr(cell, 'position') and cell.page == table.page:
                # Check if cell is within table bounds
                if (cell.box.left >= table.box.left - 0.01 and
                    cell.box.right <= table.box.right + 0.01 and
                    cell.box.top >= table.box.top - 0.01 and
                    cell.box.bottom <= table.box.bottom + 0.01):
                    table_cells.append((cell_id, cell))
        
        print(f"  Cells: {len(table_cells)}")
        
        if table_cells:
            # Find table dimensions
            max_row = max(c[1].position.row + c[1].position.rowspan - 1 
                         for c in table_cells if hasattr(c[1], 'position'))
            max_col = max(c[1].position.col + c[1].position.colspan - 1 
                         for c in table_cells if hasattr(c[1], 'position'))
            print(f"  Dimensions: {max_row + 1} rows x {max_col + 1} columns")
    
    return response

def extract_table_to_dataframe():
    """Convert table to pandas DataFrame"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("table_document.pdf"))
    
    # Find table chunks
    table_chunks = [c for c in response.chunks if c.type == "table"]
    
    if not table_chunks:
        print("No tables found in document")
        return None
    
    # Process first table
    table_chunk = table_chunks[0]
    print(f"Processing table {table_chunk.id}")
    
    # Find cells for this table
    table_cells = []
    for gid, grounding in response.grounding.items():
        if grounding.type == "tableCell" and hasattr(grounding, 'position'):
            if grounding.position.chunk_id == table_chunk.id:
                table_cells.append((gid, grounding))
    
    if not table_cells:
        print("No cells found for table")
        return None
    
    # Determine table dimensions
    max_row = max(c[1].position.row for c in table_cells)
    max_col = max(c[1].position.col for c in table_cells)
    
    # Create empty DataFrame
    df = pd.DataFrame(index=range(max_row + 1), 
                     columns=range(max_col + 1))
    
    # Fill DataFrame with cell content
    for cell_id, cell in table_cells:
        pos = cell.position
        # Get cell content from chunk if available
        # Note: This is simplified - actual content extraction may vary
        content = f"Cell R{pos.row}C{pos.col}"
        
        # Handle merged cells
        for r in range(pos.row, pos.row + pos.rowspan):
            for c in range(pos.col, pos.col + pos.colspan):
                if r <= max_row and c <= max_col:
                    df.loc[r, c] = content
    
    print("\nTable as DataFrame:")
    print(df)
    
    # Save to CSV
    df.to_csv("extracted_table.csv", index=False, header=False)
    print("Saved to extracted_table.csv")
    
    return df

def find_specific_cells():
    """Find specific cells in tables based on position"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("table_document.pdf"))
    
    # Find all table cells
    cells = {}
    for gid, grounding in response.grounding.items():
        if grounding.type == "tableCell":
            cells[gid] = grounding
    
    print(f"Total cells found: {len(cells)}")
    
    # Find specific cell types
    header_cells = []  # First row
    first_column = []  # First column
    merged_cells = []  # Cells spanning multiple rows/columns
    corner_cells = []  # Corner cells (0,0)
    
    for cell_id, cell in cells.items():
        if hasattr(cell, 'position'):
            pos = cell.position
            
            # Header cells (row 0)
            if pos.row == 0:
                header_cells.append((cell_id, cell))
            
            # First column (col 0)
            if pos.col == 0:
                first_column.append((cell_id, cell))
            
            # Merged cells
            if pos.rowspan > 1 or pos.colspan > 1:
                merged_cells.append((cell_id, cell))
                
            # Corner cell
            if pos.row == 0 and pos.col == 0:
                corner_cells.append((cell_id, cell))
    
    print(f"\nHeader cells: {len(header_cells)}")
    for cell_id, cell in header_cells[:5]:  # Show first 5
        print(f"  {cell_id}: Col {cell.position.col}")
    
    print(f"\nFirst column cells: {len(first_column)}")
    for cell_id, cell in first_column[:5]:
        print(f"  {cell_id}: Row {cell.position.row}")
    
    print(f"\nMerged cells: {len(merged_cells)}")
    for cell_id, cell in merged_cells:
        pos = cell.position
        print(f"  {cell_id}: {pos.rowspan}x{pos.colspan} at R{pos.row}C{pos.col}")
    
    return cells

def reconstruct_table_markdown():
    """Reconstruct table in markdown format from cells"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("table_document.pdf"))
    
    # Find first table chunk
    table_chunk = next((c for c in response.chunks if c.type == "table"), None)
    if not table_chunk:
        print("No table found")
        return None
    
    # Get cells for this table
    cells_data = {}
    for gid, grounding in response.grounding.items():
        if grounding.type == "tableCell" and hasattr(grounding, 'position'):
            if grounding.position.chunk_id == table_chunk.id:
                pos = grounding.position
                # Store by position
                cells_data[(pos.row, pos.col)] = {
                    'id': gid,
                    'rowspan': pos.rowspan,
                    'colspan': pos.colspan,
                    'content': f"Cell{pos.row}{pos.col}"  # Simplified
                }
    
    if not cells_data:
        print("No cells found")
        return None
    
    # Determine dimensions
    max_row = max(key[0] for key in cells_data.keys())
    max_col = max(key[1] for key in cells_data.keys())
    
    # Build markdown table
    markdown_lines = []
    
    for row in range(max_row + 1):
        row_cells = []
        for col in range(max_col + 1):
            if (row, col) in cells_data:
                cell = cells_data[(row, col)]
                content = cell['content']
                
                # Handle merged cells (simplified)
                if cell['colspan'] > 1:
                    content += f" (spans {cell['colspan']} cols)"
                if cell['rowspan'] > 1:
                    content += f" (spans {cell['rowspan']} rows)"
                
                row_cells.append(content)
            else:
                # Check if this position is covered by a merged cell
                covered = False
                for (r, c), cell in cells_data.items():
                    if (r <= row < r + cell['rowspan'] and
                        c <= col < c + cell['colspan'] and
                        (r != row or c != col)):
                        row_cells.append("^^")  # Merged cell indicator
                        covered = True
                        break
                
                if not covered:
                    row_cells.append("")
        
        # Create markdown row
        markdown_lines.append("| " + " | ".join(row_cells) + " |")
        
        # Add separator after header row
        if row == 0:
            separator = "|" + "|".join([" --- " for _ in range(max_col + 1)]) + "|"
            markdown_lines.append(separator)
    
    markdown_table = "\n".join(markdown_lines)
    print("\nReconstructed Markdown Table:")
    print(markdown_table)
    
    # Save to file
    with open("reconstructed_table.md", "w") as f:
        f.write(markdown_table)
    
    return markdown_table

def extract_table_with_headers():
    """Extract table data using headers as keys"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("table_with_headers.pdf"))
    
    # Find table chunk
    table_chunk = next((c for c in response.chunks if c.type == "table"), None)
    if not table_chunk:
        print("No table found")
        return None
    
    # Get cells
    cells = {}
    for gid, grounding in response.grounding.items():
        if grounding.type == "tableCell" and hasattr(grounding, 'position'):
            if grounding.position.chunk_id == table_chunk.id:
                pos = grounding.position
                cells[(pos.row, pos.col)] = {
                    'id': gid,
                    'content': f"Cell_{pos.row}_{pos.col}"  # Simplified
                }
    
    # Extract headers (row 0)
    headers = []
    for col in range(10):  # Assume max 10 columns
        if (0, col) in cells:
            headers.append(cells[(0, col)]['content'])
    
    if not headers:
        print("No headers found")
        return None
    
    print(f"Headers: {headers}")
    
    # Extract data rows
    data_rows = []
    for row in range(1, 100):  # Check up to 100 rows
        row_data = {}
        has_data = False
        
        for col, header in enumerate(headers):
            if (row, col) in cells:
                row_data[header] = cells[(row, col)]['content']
                has_data = True
        
        if has_data:
            data_rows.append(row_data)
        else:
            break  # No more rows
    
    print(f"\nExtracted {len(data_rows)} data rows")
    
    # Convert to DataFrame for easier manipulation
    if data_rows:
        df = pd.DataFrame(data_rows)
        print("\nData as DataFrame:")
        print(df.head())
        
        # Save to JSON
        with open("table_data.json", "w") as f:
            json.dump(data_rows, f, indent=2)
        print("Saved to table_data.json")
        
        return df
    
    return None

def compare_tables():
    """Compare tables across different pages or documents"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("multi_table_document.pdf"))
    
    # Find all table chunks
    table_chunks = [c for c in response.chunks if c.type == "table"]
    print(f"Found {len(table_chunks)} tables")
    
    table_info = []
    
    for table_chunk in table_chunks:
        # Count cells for this table
        cell_count = 0
        rows = set()
        cols = set()
        
        for gid, grounding in response.grounding.items():
            if grounding.type == "tableCell" and hasattr(grounding, 'position'):
                if grounding.position.chunk_id == table_chunk.id:
                    cell_count += 1
                    rows.add(grounding.position.row)
                    cols.add(grounding.position.col)
        
        table_info.append({
            'id': table_chunk.id,
            'page': table_chunk.grounding.page,
            'cells': cell_count,
            'rows': len(rows),
            'cols': len(cols),
            'area': (table_chunk.grounding.box.right - table_chunk.grounding.box.left) * 
                   (table_chunk.grounding.box.bottom - table_chunk.grounding.box.top)
        })
    
    # Compare tables
    print("\nTable Comparison:")
    print("-" * 60)
    for i, info in enumerate(table_info):
        print(f"Table {i+1}:")
        print(f"  Page: {info['page']}")
        print(f"  Size: {info['rows']}x{info['cols']} ({info['cells']} cells)")
        print(f"  Area: {info['area']:.4f} (normalized)")
    
    # Find similar tables
    if len(table_info) > 1:
        print("\nSimilarity Analysis:")
        for i in range(len(table_info)):
            for j in range(i+1, len(table_info)):
                t1, t2 = table_info[i], table_info[j]
                if t1['rows'] == t2['rows'] and t1['cols'] == t2['cols']:
                    print(f"  Tables {i+1} and {j+1} have same dimensions")
    
    return table_info

def extract_nested_tables():
    """Handle documents with nested tables"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("nested_tables.pdf"))
    
    # Find all table groundings
    tables = []
    for gid, grounding in response.grounding.items():
        if grounding.type == "table":
            tables.append((gid, grounding))
    
    # Check for nesting by comparing bounding boxes
    nested_pairs = []
    for i, (id1, table1) in enumerate(tables):
        for j, (id2, table2) in enumerate(tables):
            if i >= j:
                continue
            
            # Check if table2 is inside table1
            if (table2.box.left >= table1.box.left and
                table2.box.right <= table1.box.right and
                table2.box.top >= table1.box.top and
                table2.box.bottom <= table1.box.bottom):
                nested_pairs.append((id1, id2))
                print(f"Table {id2} is nested inside table {id1}")
            # Check if table1 is inside table2
            elif (table1.box.left >= table2.box.left and
                  table1.box.right <= table2.box.right and
                  table1.box.top >= table2.box.top and
                  table1.box.bottom <= table2.box.bottom):
                nested_pairs.append((id2, id1))
                print(f"Table {id1} is nested inside table {id2}")
    
    if nested_pairs:
        print(f"\nFound {len(nested_pairs)} nested table relationships")
    else:
        print("\nNo nested tables found")
    
    return nested_pairs

if __name__ == "__main__":
    # Run table analysis examples
    print("=== Analyze Table Structure ===")
    analyze_table_structure()
    
    # Uncomment to run other examples:
    # print("\n=== Extract to DataFrame ===")
    # extract_table_to_dataframe()
    
    # print("\n=== Find Specific Cells ===")
    # find_specific_cells()
    
    # print("\n=== Reconstruct Markdown ===")
    # reconstruct_table_markdown()
    
    # print("\n=== Extract with Headers ===")
    # extract_table_with_headers()
    
    # print("\n=== Compare Tables ===")
    # compare_tables()
    
    # print("\n=== Nested Tables ===")
    # extract_nested_tables()