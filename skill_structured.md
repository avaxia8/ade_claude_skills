# LandingAI ADE Python Reference Guide

## 1. Basic Syntax of ADE

### Installation & Setup
```python
pip install landingai-ade

from pathlib import Path
from landingai_ade import LandingAIADE, AsyncLandingAIADE
from pydantic import BaseModel
import json

# Initialize client
client = LandingAIADE()  # Uses VISION_AGENT_API_KEY env var
# OR
client = LandingAIADE(apikey="v2_...")
# For EU users
client = LandingAIADE(environment="eu")
```

### Core Workflow
```python
# Step 1: Parse document → Get markdown and chunks
parsed = client.parse(document=Path("doc.pdf"))

# Step 2: Split mixed documents (optional)
splits = client.split(
    markdown=parsed.markdown,
    split_class=[{"name": "Invoice"}, {"name": "Receipt"}]
)

# Step 3: Extract structured data
class Schema(BaseModel):
    field1: str
    field2: float

extracted = client.extract(
    markdown=parsed.markdown,
    schema=Schema.model_json_schema()
)
```

### Async Operations
```python
async with AsyncLandingAIADE() as client:
    response = await client.parse(document=Path("doc.pdf"))
```

### Parse Jobs (Large Files)
```python
job = client.parse_jobs.create(document=Path("large.pdf"))
status = client.parse_jobs.get(job.job_id)
```

## 2. Arguments of Main Functions

### Parse Function
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string \| null | No | Model version (e.g., "dpt-2-latest") |
| `document` | file \| null | One required | Local file path |
| `document_url` | string \| null | One required | Remote URL (alternative to document) |
| `split` | "page" \| null | No | Split document by pages |
| `save_to` | string \| null | No | Output folder, saves as {input_file}_parse_output.json |

```python
response = client.parse(
    document=Path("file.pdf"),     # OR document_url="https://..."
    model="dpt-2-latest",
    split="page",                   # Optional: split by pages
    save_to="./output"              # Optional: save JSON output
)
```

### Split Function
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `split_class` | list[dict] | Yes | Classification configuration |
| `markdown` | file \| string | One required | Local markdown file/content |
| `markdownUrl` | string \| null | One required | Remote URL (alternative to markdown) |
| `model` | string \| null | No | Default: "split-20251105" |

Split class structure:
```python
split_class = [
    {
        "name": "Invoice",           # Required: classification name
        "description": "Sales invoice", # Optional: description
        "identifier": "Invoice Date"    # Optional: grouping field
    }
]
```

### Extract Function
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schema` | string | Yes | JSON schema for extraction |
| `model` | string \| null | No | Version (e.g., "extract-latest") |
| `markdown` | file \| string | One required | Local markdown file/content |
| `markdown_url` | string \| null | One required | Remote URL (alternative to markdown) |
| `save_to` | string \| null | No | Output folder, saves as {input_file}_extract_output.json |

```python
response = client.extract(
    schema=json.dumps(schema),      # Required: JSON schema
    markdown=parsed.markdown,       # OR markdown_url="https://..."
    model="extract-latest",
    save_to="./output"              # Optional: save JSON output
)
```

### Parse Jobs (Async Processing)
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document` | file \| null | One required | Local file path |
| `document_url` | string \| null | One required | Remote URL (alternative to document) |
| `split` | "page" \| null | No | Split document by pages |
| `output_save_url` | string \| null | No* | URL for ZDR storage (*required if ZDR enabled) |
| `model` | string \| null | No | Model version |

```python
job = client.parse_jobs.create(
    document=Path("large.pdf"),
    model="dpt-2-latest",
    split="page",
    output_save_url="https://..."  # Required if ZDR enabled
)
```

## 3. Outputs of Main Functions

### Parse Response Structure
```python
response.markdown      # string - Complete document as markdown with <a id='{chunk_id}'></a> anchors
response.chunks       # list[dict] - Array of content blocks
response.grounding    # dict - Maps IDs to precise locations
response.splits       # list[dict] - If split="page" was used
response.metadata     # dict - Processing info

# Each chunk contains:
chunk = {
    "id": "uuid-string",           # Unique identifier
    "type": "text|table|figure...", # Chunk type
    "markdown": "content...",       # Chunk content
    "grounding": {
        "page": 0,                  # Zero-indexed page
        "box": {                    # Normalized 0-1 coordinates
            "left": 0.1,
            "top": 0.2,
            "right": 0.9,
            "bottom": 0.3
        }
    }
}

# Grounding dict structure:
grounding = {
    "chunk-uuid": {                 # Chunk grounding
        "type": "chunkText",        # Has "chunk" prefix
        "page": 0,
        "box": {...}
    },
    "0-1": {                       # Table grounding
        "type": "table",            # No prefix
        "page": 0,
        "box": {...}
    },
    "0-2": {                       # Table cell grounding
        "type": "tableCell",
        "page": 0,
        "box": {...},
        "position": {               # Only for table cells
            "row": 0,
            "col": 0,
            "rowspan": 1,
            "colspan": 2,
            "chunk_id": "..."
        }
    }
}

# Metadata structure:
metadata = {
    "filename": "doc.pdf",
    "org_id": "...",
    "page_count": 5,
    "duration_ms": 1234,
    "credit_usage": 3,
    "version": "dpt-2-latest",
    "job_id": "...",
    "failed_pages": []              # List of failed page numbers
}
```

### Split Response Structure
```python
response.splits       # list[dict] - Array of classified splits
response.metadata     # dict - Processing info

# Each split contains:
split = {
    "classification": "Invoice",     # Assigned class name
    "identifier": "INV-001",        # Grouping identifier
    "markdowns": ["content..."],    # Array of markdown strings
    "pages": [0, 1]                 # Page numbers
}
```

### Extract Response Structure
```python
response.extraction           # dict - Extracted key-value pairs
response.extraction_metadata  # dict - With chunk references
response.metadata            # dict - Processing info

# Extraction example:
extraction = {
    "invoice_number": "INV-001",
    "total": 1234.56
}

# Extraction metadata:
extraction_metadata = {
    "invoice_number": {
        "references": ["chunk-uuid-1", "chunk-uuid-2"]  # Chunk IDs
    }
}
```

### Parse Jobs Response
```python
# Create response:
job = {
    "job_id": "cml1kaihb08dxcn01b3mlfy5b"
}

# Status response:
status = {
    "job_id": "...",
    "status": "pending|processing|completed|failed",
    "progress": 0.75,               # 0-1 progress indicator
    "failure_reason": null,          # Error message if failed
    "received_at": 1234567890
}

# List response:
jobs_list = {
    "jobs": [...],                   # Array of job status objects
    "has_more": true,
    "org_id": "..."
}
```

## 4. Clarifying Confusions

### chunks[].type vs grounding.{id}.type

**Two different type systems:**
- `chunks[].type`: High-level document structure (`text`, `table`, `figure`, etc.)
- `grounding.{id}.type`: Precise elements with coordinates (`chunkText`, `chunkTable`, `tableCell`, etc.)

**Key differences:**
1. Chunk types have NO prefix: `text`, `table`, `figure`
2. Grounding types for chunks have "chunk" prefix: `chunkText`, `chunkTable`, `chunkFigure`
3. Grounding has exclusive types: `table` (actual table structure), `tableCell` (individual cells)

**Example:** One table chunk → Multiple groundings
```python
# 1 chunk of type "table"
chunk = {"id": "abc", "type": "table", ...}

# Multiple grounding entries:
grounding = {
    "abc": {"type": "chunkTable", ...},    # The chunk itself
    "0-1": {"type": "table", ...},         # First table structure
    "0-2": {"type": "tableCell", ...},     # Cell in first table
    "0-m": {"type": "table", ...},         # Second table structure
    "0-n": {"type": "tableCell", ...}      # Cell in second table
}
```

### Grounding Key Formats

Three types of keys in grounding dict:
1. **Chunk IDs**: UUID format (e.g., `ea3ffbfc-dce9-4d90-a259-2df8fe7f067d`)
2. **Table IDs**: Format `{page}-{id}` (e.g., `0-1`, `0-m`)
3. **Table cell IDs**: Format `{page}-{id}` (e.g., `0-2`, `0-n`)

### When to Use Parse vs Parse Jobs

| Use Parse | Use Parse Jobs |
|-----------|---------------|
| Files < 50MB | Files > 50MB |
| Need immediate results | Can wait for processing |
| Simple documents | Complex/large documents |
| Synchronous workflow | Batch processing |

### File Input Methods

Each function accepts EITHER local file OR URL, not both:
```python
# Option 1: Local file
client.parse(document=Path("file.pdf"))

# Option 2: Remote URL
client.parse(document_url="https://example.com/file.pdf")

# NOT both - will error!
client.parse(document=Path("file.pdf"), document_url="https://...")
```

## 5. Debugging Tips

### Check Failed Pages
```python
if response.metadata.get("failed_pages"):
    print(f"Warning: Failed pages: {response.metadata['failed_pages']}")
    # Retry or handle failed pages
```

### Handle Rate Limits
```python
from landingai_ade.exceptions import RateLimitError
import time

for attempt in range(3):
    try:
        response = client.parse(document=Path("file.pdf"))
        break
    except RateLimitError:
        wait_time = 2 ** attempt * 10  # Exponential backoff
        time.sleep(wait_time)
```

### Enable Detailed Logging
```python
import os
os.environ["LANDINGAI_ADE_LOG"] = "debug"
```

### Validate Extraction Schema
```python
# Always test schema before extraction
from pydantic import ValidationError

try:
    schema = MySchema.model_json_schema()
    # Test with sample data
    MySchema(**{"field1": "test", "field2": 123})
except ValidationError as e:
    print(f"Schema validation error: {e}")
```

### Handle Large Files
```python
from pathlib import Path

file_size = Path("document.pdf").stat().st_size
if file_size > 50_000_000:  # 50MB
    # Use parse_jobs for large files
    job = client.parse_jobs.create(document=Path("document.pdf"))
else:
    response = client.parse(document=Path("document.pdf"))
```

### Debug Table Cell Positions
```python
# Find specific cells in tables
for gid, grounding in response.grounding.items():
    if grounding.type == "tableCell":
        pos = grounding.position
        if pos.row == 0 and pos.col == 0:
            print(f"Found header cell: {gid}")
        if pos.colspan > 1 or pos.rowspan > 1:
            print(f"Found merged cell: {gid}")
```

### Common Error Patterns

| Error | Cause | Solution |
|-------|-------|----------|
| `APITimeoutError` | Large file or slow network | Use parse_jobs instead |
| `APIStatusError` 400 | Invalid parameters | Check required params |
| `APIStatusError` 413 | File too large | Use parse_jobs |
| `schema_violation_error` | Extract schema mismatch | Validate schema fields |
| Empty chunks | PDF parsing failed | Check PDF isn't corrupted |
| Missing grounding | Old model version | Use latest model version |

### Save Outputs for Debugging
```python
# Always save outputs when debugging
response = client.parse(
    document=Path("problematic.pdf"),
    save_to="./debug_output"
)
# Check ./debug_output/problematic_parse_output.json
```

---

## Quick Reference Card

```python
# Parse
parsed = client.parse(document=Path("doc.pdf"), model="dpt-2-latest")

# Split  
splits = client.split(markdown=parsed.markdown, 
                     split_class=[{"name": "Type1"}])

# Extract
extracted = client.extract(markdown=parsed.markdown,
                          schema=json.dumps(schema))

# Parse Job
job = client.parse_jobs.create(document=Path("large.pdf"))
status = client.parse_jobs.get(job.job_id)

# Access Results
parsed.markdown           # Full text
parsed.chunks[0].type    # Chunk type
parsed.grounding["id"]   # Precise location
extracted.extraction     # Extracted data
```