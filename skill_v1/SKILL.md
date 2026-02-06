---
name: landingai-ade
description: Parse, extract, and analyze documents using LandingAI's ADE Python SDK. Handles PDFs and images with visual grounding, table extraction, and structured data output.
---

# LandingAI ADE (Agentic Document Extraction)

## Quick Start

Parse a document and extract structured data in 3 steps:

```python
from landingai_ade import LandingAIADE
from pydantic import BaseModel
from pathlib import Path

# 1. Initialize client (uses VISION_AGENT_API_KEY env var)
client = LandingAIADE()

# 2. Parse document to get markdown and chunks
response = client.parse(document=Path("invoice.pdf"))

# 3. Extract structured data with a schema
class Invoice(BaseModel):
    invoice_number: str
    total_amount: float

extracted = client.extract(
    markdown=response.markdown,
    schema=Invoice.model_json_schema()
)

print(f"Invoice #{extracted.extraction['invoice_number']}")
print(f"Total: ${extracted.extraction['total_amount']}")
```

## Core Workflow

ADE follows a three-step workflow:

1. **Parse** → Convert documents (PDF/images) to markdown with visual grounding
2. **Split** (optional) → Classify mixed documents by type  
3. **Extract** → Get structured data using schemas

### Visual Grounding

Every piece of content is mapped to its exact location in the original document:

```python
# Access location of any chunk
chunk = response.chunks[0]
print(f"Page: {chunk.grounding.page}")
print(f"Position: {chunk.grounding.box}")  # Normalized 0-1 coordinates
```

## Key Features

- **Document Parsing**: PDFs and images to structured markdown
- **Table Extraction**: Individual cell access with position data
- **Visual Grounding**: Precise bounding boxes for all content
- **Schema-based Extraction**: Use Pydantic models for structured output
- **Async Support**: Process multiple documents concurrently
- **Large File Handling**: Parse jobs API for documents >50MB

## Common Use Cases

### Parse with Page Splitting
```python
response = client.parse(
    document=Path("document.pdf"),
    split="page",  # Split by pages
    save_to="./output"  # Save JSON output
)
```

### Extract Tables with Cell Positions
```python
# Find specific cells in tables
for gid, grounding in response.grounding.items():
    if grounding.type == "tableCell":
        pos = grounding.position
        print(f"Cell at row {pos.row}, col {pos.col}")
```

### Handle Large Files
```python
# Use parse jobs for files >50MB
job = client.parse_jobs.create(document=Path("large.pdf"))
status = client.parse_jobs.get(job.job_id)
```

## Resources

- **[REFERENCE.md](REFERENCE.md)** - Complete API reference with all parameters
- **[scripts/](scripts/)** - Runnable examples for common tasks:
  - `parse_document.py` - Parsing examples
  - `extract_data.py` - Schema-based extraction
  - `split_documents.py` - Document classification
  - `visualize_chunks.py` - Visualization with bounding boxes
  - `handle_tables.py` - Table and cell processing

## Installation

```bash
pip install landingai-ade
export VISION_AGENT_API_KEY="v2_..."
```

## Models

- Parse: `dpt-2-latest`
- Extract: `extract-latest`
- Split: `split-latest`

## Error Handling

```python
from landingai_ade.exceptions import RateLimitError, APITimeoutError

try:
    response = client.parse(document=Path("doc.pdf"))
except RateLimitError:
    time.sleep(10)  # Backoff and retry
except APITimeoutError:
    # Use parse_jobs for large files
    job = client.parse_jobs.create(document=Path("doc.pdf"))
```