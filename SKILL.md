# LandingAI ADE Python Claude Skill

## 1. SETUP

```python
# Install
pip install landingai-ade

# Import required modules
from pathlib import Path
from landingai_ade import LandingAIADE

# Initialize client
client = LandingAIADE()
file_path = Path("my_document.pdf")
```

## 2. PARSE

```python
# Parse a document
parsed_response = client.parse(
    document=file_path,
    split="page",  # optional
    save_to="./output_folder"  # optional: saves as {input_file}_parse_output.json
)

# View the markdown output
print(parsed_response.markdown) # The data will be returned as key-value pairs separated by line breaks (\n).
​

```

## 3. SPLIT: Separate Mixed Docs

```python
# Split documents by type
response = client.split(
    markdown=parsed_response,
    split_class=[
        {"name": "Invoice", "identifier": "ID"},
        {"name": "Receipt", "identifier": "Date"}
    ]
)
```

## 4. EXTRACT

```python
from pydantic import BaseModel
import json

# Define your schema
class InvoiceSchema(BaseModel):
    invoice_number: str
    total: float

# Get JSON schema
schema = InvoiceSchema.model_json_schema()

# Extract structured data
client.extract(
    markdown=parsed_response,
    schema=schema,
    save_to="./output_folder"  # optional: saves as {input_file}_extract_output.json
)
```

## 5. Quicker Processing (Async)

```python
import asyncio
from landingai_ade import AsyncLandingAIADE

# Use async client for better performance
async with AsyncLandingAIADE() as async_client:
    response = await async_client.parse(document=file_path)
    print(response.markdown)
```

## 6. Heavy Lifting (Parse Jobs)

```python
# 1. Create the job
job = client.parse_jobs.create(
    document=file_path,
    model="dpt-2-latest"
)

# 2. Check Status
job_status = client.parse_jobs.get(job.job_id)
print(f"Status: {job.job_status}")

# 3. List All Jobs
all_jobs = client.parse_jobs.list(status="completed")
```

## 7. Key Response Structures

### Parse Response


| Field             | Type        | Description |
|-------------------|-------------|-------------|
| `markdown`          | string      | Complete document as markdown. Uses `<a id={chunk_id}></a>` tags as anchors. |
| `chunks`            | list[dict]  | An array of individual content blocks. Each chunk includes an `id`, its own `markdown`, a `type` and a `grounding` object. |
| `splits`            | list[dict]  | Populated if `split="page"` was used. Each object includes `class` (e.g., "page"), `identifier` (e.g., "page_0"), pages (e.g. , [0]), `markdown` and `chunks`(a list of chunk IDs belonging to that split). |
| `grounding`         | dict        | Maps chunk IDs to detailed grounding information, including page number, bounding box coordinates, and a detailed classification of elements (e.g., `chunkText`, `tableCell`). Grounding enables precise mapping of content back to its location in the original document. |
| `metadata`          | dict        | Processing metadata including `filename`, organization ID (`org_id`), `page_count`, processing time (`duration_ms`), API credit usage (`credit_usage`) and model `version`. There will be a `failed_pages` array listing page numbers that failed to process. |

```python
# Each chunk has:
chunk[].id              # Unique identifier
chunk[].type           # Chunk type (text, table, figure, etc.)
chunk[].markdown        # Chunk Content
chunk[].grounding.page  # Page number (0-indexed)
chunk[].grounding.box   # Bounding box (left, top, right, bottom) normalized 0-1

# Grounding dict has:
grounding.{id}.page  # Page number
grounding.{id}.type  # Grounding type (chunkText, chunkTable, etc.)
grounding.{id}.box   # Bounding box coordinates

# Grounding object keys can be:
# - Chunk IDs: UUID format (e.g., ea3ffbfc-dce9-4d90-a259-2df8fe7f067d)
# - Table IDs: Format {page}-{id} (e.g., 0-1, 0-m)
# - Table cell IDs: Format {page}-{id} (e.g., 0-2, 0-n)

# Table cells have additional position field:
grounding.{cell_id}.position = {
    row: 0,        # Zero-indexed row
    col: 0,        # Zero-indexed column  
    rowspan: 1,    # Number of rows spanned
    colspan: 2,    # Number of columns spanned
    chunk_id: "..."  # Associated chunk ID
}
```

### Extract Response
```python
response.extraction           # Extracted key-value pairs
response.extraction_metadata  # Contains "references" linking to chunk IDs
response.metadata            # Processing metadata
```

### Split Response
```python
response.splits              # Array of classified splits
split.classification        # Assigned class name
split.identifier           # Grouping identifier
split.markdowns           # Array of markdown content
split.pages              # Page numbers
```

# Chunk Types vs Grounding Types in ADE

## Two Type Systems

**Chunks** (`chunks[].type`) - Document structure:
- `text`, `table`, `figure`, `marginalia`, `logo`, `card`, `attestation`, `scan_code`

**Groundings** (`grounding.{id}.type`) - Precise elements with coordinates:
- `chunkText`, `chunkTable`, `chunkFigure`, `chunkMarginalia`, `chunkLogo`, `chunkCard`, `chunkAttestation`, `chunkScanCode`, `chunkForm`
- Plus exclusive types: `table`, `tableCell`

## Key Relationship

**Prefix Rule:** Remove "chunk" to map grounding → chunk type
- `chunkText` → `text` chunk
- `chunkTable` → `table` chunk

**Important Distinction:**
- Chunk `table` = "region with tabular content" (1 chunk)
- Grounding `table` = "actual table structure" (possibly multiple per chunk)
- Grounding `tableCell` = individual cells (only at grounding level)

## When to Use

**Use chunk types for:**
- Document structure analysis
- Content type counting
- High-level overview

**Use grounding types for:**
- Bounding box coordinates
- Cell-level extraction
- Precise element positioning

## Common Confusion

Users ask why both exist: **Answer** → Different granularity. Chunks = overview, groundings = precise locations with coordinates.

**Real Example:** One table chunk with 2 tables, each with 2 cells:
```python
# In chunks array - ONE chunk
chunk = {
    "id": "e59fb76c-9fad-4cfa",
    "type": "table",
    "markdown": "<table id='0-m'>...</table>\n<table id='0-u'>...</table>"
}

# In grounding dict - SEVEN entries:
grounding = {
    "e59fb76c-9fad-4cfa": {"type": "chunkTable", ...},  # The chunk
    "0-m": {"type": "table", ...},                      # First table
    "0-n": {"type": "tableCell", "position": {...}},   # Cell 1 of table 1
    "0-o": {"type": "tableCell", "position": {...}},   # Cell 2 of table 1
    "0-u": {"type": "table", ...},                      # Second table
    "0-v": {"type": "tableCell", "position": {...}},   # Cell 1 of table 2
    "0-w": {"type": "tableCell", "position": {...}}    # Cell 2 of table 2
}
```

## Visual Grounding

Visual grounding provides the exact location of content in the original document using normalized coordinates (0-1 range).

### Convert Normalized to Pixel Coordinates
```python
# For any chunk, convert normalized coordinates to pixels
x1 = int(chunk.grounding.box.left * img_width)
y1 = int(chunk.grounding.box.top * img_height)
x2 = int(chunk.grounding.box.right * img_width)
y2 = int(chunk.grounding.box.bottom * img_height)
```

### Visualize Parsed Document
```python
from PIL import Image, ImageDraw
import fitz  # PyMuPDF

# Define colors for grounding types (not chunk types!)
GROUNDING_TYPE_COLORS = {
    "chunkText": (40, 167, 69),       # Green
    "chunkTable": (0, 123, 255),      # Blue
    "chunkMarginalia": (111, 66, 193), # Purple
    "chunkFigure": (255, 0, 255),     # Magenta
    "chunkLogo": (144, 238, 144),     # Light Green
    "chunkCard": (255, 165, 0),       # Orange
    "chunkAttestation": (0, 255, 255), # Cyan
    "chunkScanCode": (255, 193, 7),   # Yellow
    "chunkForm": (220, 20, 60),       # Red
    "tableCell": (173, 216, 230),     # Light Blue
    "table": (70, 130, 180)           # Steel Blue
}

# Draw bounding boxes on image
for chunk_id, grounding in response.grounding.items():
    if grounding.page != page_num:
        continue
    
    # Convert coordinates
    x1 = int(grounding.box.left * img_width)
    y1 = int(grounding.box.top * img_height)
    x2 = int(grounding.box.right * img_width)
    y2 = int(grounding.box.bottom * img_height)
    
    # Draw box with color based on grounding type
    color = GROUNDING_TYPE_COLORS.get(grounding.type, (128, 128, 128))
    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
    
    # Add label
    label = f"{grounding.type}:{chunk_id[:8]}"
    draw.text((x1, y1-20), label, fill=color)
```

### Save Chunks as Images
```python
from datetime import datetime
import os

# Create output directory structure
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"groundings/document_{timestamp}"

for chunk in response.chunks:
    # Create page directory
    page_dir = f"{output_dir}/page_{chunk.grounding.page}"
    os.makedirs(page_dir, exist_ok=True)
    
    # Crop chunk region from page image
    x1 = int(chunk.grounding.box.left * img_width)
    y1 = int(chunk.grounding.box.top * img_height)
    x2 = int(chunk.grounding.box.right * img_width)
    y2 = int(chunk.grounding.box.bottom * img_height)
    
    chunk_img = page_image.crop((x1, y1, x2, y2))
    
    # Save with descriptive filename: ChunkType.ChunkID.png
    filename = f"{page_dir}/{chunk.type}.{chunk.id}.png"
    chunk_img.save(filename)
```

Directory structure:
```
groundings/
└── document_TIMESTAMP/
    ├── page_0/
    │   ├── text.abc123.png
    │   └── table.def456.png
    └── page_1/
        └── figure.ghi789.png
```

### Link Extracted Data to Source Location
```python
# After extraction, trace data back to its source
for field_name, value in extract_response.extraction.items():
    # Get chunk reference from extraction metadata
    if field_name in extract_response.extraction_metadata:
        chunk_refs = extract_response.extraction_metadata[field_name].get("references", [])
        if chunk_refs:
            chunk_id = chunk_refs[0]
            
            # Look up grounding for this chunk
            if chunk_id in parse_response.grounding:
                grounding = parse_response.grounding[chunk_id]
                
                print(f"Field: {field_name}")
                print(f"Value: {value}")
                print(f"Found on page: {grounding.page}")
                print(f"Location: ({grounding.box.left:.3f}, {grounding.box.top:.3f})")
                print(f"Grounding type: {grounding.type}")
```

### Working with Table Cell Positions
```python
# Access table cell position data
for grounding_id, grounding in parse_response.grounding.items():
    if grounding.type == "tableCell":
        pos = grounding.position
        print(f"Cell {grounding_id}:")
        print(f"  Row: {pos.row}, Col: {pos.col}")
        print(f"  Spans: {pos.rowspan}x{pos.colspan}")
        print(f"  From chunk: {pos.chunk_id}")
        
        # Map extracted value back to specific cell
        if pos.row == 2 and pos.col == 3:  # Third row, fourth column
            print(f"  This is the total amount cell")
        
        # Identify merged cells
        if pos.colspan > 1 or pos.rowspan > 1:
            print(f"  This is a merged cell")
```

## Error Handling

```python
from landingai_ade.exceptions import (
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    APIStatusError
)

try:
    response = client.parse(document=file_path)
except RateLimitError:
    # Handle rate limiting with backoff
    time.sleep(10)
except APITimeoutError:
    # Use parse_jobs for large files
    job = client.parse_jobs.create(document=file_path)
```

## Models
- Parse: `dpt-2-latest`
- Extract: `extract-latest`
- Split: `split-latest`

## EU Support
```python
client = LandingAIADE(environment="eu")
```

---

## Claude Skill Instructions

You are an expert in LandingAI's ADE (Agentic Document Extraction) Python SDK. 

When helping users:
1. Use the exact API shown above - don't make up parameters or methods
2. Parse → Split → Extract is the typical workflow
3. Understand the distinction: `chunks[].type` vs `grounding.{id}.type`
4. Visual grounding provides normalized coordinates (0-1 range) that need conversion to pixels for visualization
5. `extraction_metadata` contains "references" that link to chunk IDs in `parse_response.grounding`
6. Use async client for multiple documents, parse_jobs for documents >50MB
7. Always include imports and proper error handling

Core capabilities:
- Parse: Convert documents to markdown with chunk identification and grounding
- Split: Classify mixed documents by type with identifiers
- Extract: Get structured data using Pydantic schemas with source tracing
- Visual Grounding: Access exact location (page, bounding box) of any content
- Visualization: Draw color-coded bounding boxes for different grounding types
- Chunk Extraction: Save individual chunks as images with proper naming

Remember: Chunks are high-level document structure, groundings are precise element locations with coordinates.