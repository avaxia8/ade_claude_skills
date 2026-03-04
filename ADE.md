# LandingAI ADE Python SDK Guidelines

You are an ADE (Agentic Document Extraction) coding expert. Help with writing code using the LandingAI ADE Python SDK for document parsing, data extraction, document splitting, and table cell access.

Official SDK documentation: https://docs.landing.ai/ade/ade-python

## Golden Rule: Use the Correct SDK

Always use the LandingAI ADE Python SDK, which is the standard library for all ADE API interactions.

- **Library Name:** LandingAI ADE Python SDK
- **Python Package:** `landingai-ade`
- **Installation:** `pip install landingai-ade`

**APIs and Usage:**

- **Correct:** `from landingai_ade import LandingAIADE`
- **Correct:** `from landingai_ade import AsyncLandingAIADE` (for async usage)
- **Correct:** `client = LandingAIADE()` (uses `VISION_AGENT_API_KEY` env var)
- **Correct:** `client = LandingAIADE(api_key="v2_...")`

## Initialization and API Key

```python
from landingai_ade import LandingAIADE
from pathlib import Path

# Recommended: set env var, picked up automatically
# export VISION_AGENT_API_KEY="v2_..."
client = LandingAIADE()

# Or pass key directly
client = LandingAIADE(api_key="v2_...")

# EU region
client = LandingAIADE(base_url="https://api.va.eu-west-1.landing.ai/v1/ade")
```

| Region | Base URL |
|--------|----------|
| US (default) | `https://api.va.landing.ai/v1/ade` |
| EU | `https://api.va.eu-west-1.landing.ai/v1/ade` |

## Model Versions

| Operation | Model Version | Description |
|-----------|--------------|-------------|
| Parse | `dpt-2-latest` (default) | Document parsing and OCR |
| Extract | `extract-latest` (default) | Schema-based field extraction |
| Split | `split-latest` (default) | Document classification and splitting |

## Supported File Types

| Category | Formats | Notes |
|----------|---------|-------|
| **PDF** | PDF | Up to 100 pages; no password-protected files |
| **Images** | JPEG, JPG, PNG, APNG, BMP, DCX, DDS, DIB, GD, GIF, ICNS, JP2, PCX, PPM, PSD, TGA, TIF, TIFF, WEBP | |
| **Text Documents** | DOC, DOCX, ODT | Converted to PDF server-side before parsing |
| **Presentations** | ODP, PPT, PPTX | Converted to PDF server-side before parsing |
| **Spreadsheets** | CSV, XLSX | Up to 10 MB in Playground; no sheet/column/row limits |

## Core Workflow

ADE follows a three-step pipeline: **Parse → Split (optional) → Extract**.
Parse once, then split/extract as many times as needed against the cached markdown.

## 1. Parse API

Converts documents to structured markdown with chunks and visual grounding.

### Basic Parsing

```python
response = client.parse(document=Path("invoice.pdf"))

print(response.markdown)              # Full document as markdown
print(len(response.chunks))           # Number of content blocks
print(response.metadata.page_count)   # Page count

# Filter chunks by type
tables = [c for c in response.chunks if c.type == "table"]
text = [c for c in response.chunks if c.type == "text"]
figures = [c for c in response.chunks if c.type == "figure"]
```

### Parse Options

```python
# From URL
response = client.parse(document_url="https://example.com/doc.pdf")

# With page splitting
response = client.parse(document=Path("multi_page.pdf"), split="page")
for split in response.splits:
    print(f"Page {split.pages}: {len(split.chunks)} chunks")

# Save output to directory
response = client.parse(document=Path("doc.pdf"), save_to=Path("./output"))
```

### Parse Response Structure

```python
response.markdown       # str — Complete document as markdown
response.chunks         # list — Content blocks (text, table, figure, etc.)
response.grounding      # dict — Detailed location mapping (bounding boxes, table cells)
response.splits         # list — Page splits (only if split="page")
response.metadata       # object — filename, page_count, duration_ms, credit_usage, etc.
```

Each chunk has:
```python
chunk.id                # str — Unique identifier (UUID)
chunk.type              # str — "text", "table", "marginalia", "figure", "scan_code", "logo", "card", "attestation"
chunk.markdown          # str — Chunk content (tables render as HTML)
chunk.grounding.page    # int — Zero-indexed page number
chunk.grounding.box     # object — Normalized 0-1 bounding box (left, top, right, bottom)
```

### Visual Grounding

Grounding provides **visual positioning** (bounding boxes on the page) for each chunk.

```python
response = client.parse(document=Path("doc.pdf"))

# Access chunk locations
for chunk in response.chunks:
    box = chunk.grounding.box
    print(f"{chunk.type} on page {chunk.grounding.page}: "
          f"({box.left:.3f}, {box.top:.3f}) → ({box.right:.3f}, {box.bottom:.3f})")

# Find table cells with positions (PDF only — grounding is null for spreadsheets)
for gid, grounding in response.grounding.items():
    if grounding.type == "tableCell":
        pos = grounding.position
        print(f"Cell ({pos.row}, {pos.col}) span=({pos.rowspan}x{pos.colspan})")
```

### Table Chunk Formats

Table chunks render as HTML inside `chunk.markdown`. The ID format and grounding availability differ by document type.

**PDF / Image / Document tables:**
- Element IDs: `{page_number}-{sequential_number}` (e.g., `0-1`, `0-2`)
- `grounding` contains bounding boxes and `tableCell` position entries for every cell
- Cells may include `rowspan`/`colspan` attributes

```html
<table id="0-1">
<tr><td id="0-2" colspan="2">Product Summary</td></tr>
<tr><td id="0-3">Product</td><td id="0-4">Revenue</td></tr>
<tr><td id="0-5">Hardware</td><td id="0-6">15,230</td></tr>
</table>
```

**Spreadsheet tables (XLSX / CSV):**
- Element IDs: `{tab_name}-{cell_reference}` (e.g., `Sheet 1-A1`, `Sheet 1-B2`)
- Table element ID: `{tab_name}-{start_cell}:{end_cell}` (e.g., `Sheet 1-A1:B4`)
- **`grounding` is `null`** — cell positions are encoded in the IDs themselves
- Embedded images and charts become `figure` chunks

```html
<table id='Sheet 1-A1:B4'>
  <tr>
    <td id='Sheet 1-A1'>Program</td>
    <td id='Sheet 1-B1'>Interest Rate</td>
  </tr>
  <tr>
    <td id='Sheet 1-A2'>15 Year Fixed-Rate Mortgage</td>
    <td id='Sheet 1-B2'>0.05125</td>
  </tr>
</table>
```

### Extract a Cell Value by Row and Column (PDF)

Cell content should be retrieved by parsing the HTML in `chunk.markdown` — walk `<tr>`/`<td>` elements to build a (row, col) grid.

```python
import re

response = client.parse(document=Path("doc.pdf"))

# Get the first table chunk
table = next(c for c in response.chunks if c.type == "table")

# Parse HTML rows and cells into a (row, col) grid
rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table.markdown, re.DOTALL)
grid = {}
for r, row_html in enumerate(rows):
    for c, m in enumerate(re.finditer(
        r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL
    )):
        grid[(r, c)] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

# Look up a value (zero-indexed row and column)
row, col = 1, 0
value = grid[(row, col)]
print(f"Row {row}, Col {col}: {value}")
```

### Read a Spreadsheet Cell by Reference

```python
import re

response = client.parse(document=Path("report.xlsx"))

# Get the first table chunk
table = next(c for c in response.chunks if c.type == "table")

# Spreadsheet cell IDs are "{tab_name}-{cell_ref}" (e.g., "Sheet 1-B2").
# grounding is null for spreadsheets, so parse IDs directly from HTML.
cell_text = {}
for m in re.finditer(
    r'<td[^>]*\bid=["\']([^"\']+)["\'][^>]*>(.*?)</td>',
    table.markdown,
    re.DOTALL,
):
    cell_text[m.group(1)] = re.sub(r"<[^>]+>", "", m.group(2)).strip()

# Look up by tab name and cell reference
value = cell_text["Sheet 1-B2"]
print(f"Sheet 1, cell B2: {value}")
```

## 2. Extract API

Extracts structured data from documents or markdown using JSON schemas.

### Pydantic Schema Extraction

```python
from pydantic import BaseModel, Field
import json

class InvoiceData(BaseModel):
    invoice_number: str = Field(description="Invoice number or ID")
    total_amount: float = Field(description="Total amount to be paid")
    vendor_name: str = Field(description="Vendor or supplier name")
    line_items: list[dict] | None = Field(default=None, description="Line items")

# Parse then extract (recommended: parse once, extract many)
parsed = client.parse(document=Path("invoice.pdf"))

response = client.extract(
    markdown=parsed.markdown,
    schema=json.dumps(InvoiceData.model_json_schema()),
    model="extract-latest"
)

invoice = InvoiceData(**response.extraction)
print(f"Invoice {invoice.invoice_number}: ${invoice.total_amount}")
```

### Direct Extraction from File

```python
response = client.extract(
    document=Path("invoice.pdf"),
    schema=json.dumps(InvoiceData.model_json_schema()),
    model="extract-latest"
)
```

### Dict Schema Extraction

```python
response = client.extract(
    markdown=parsed.markdown,
    schema=json.dumps({
        "type": "object",
        "properties": {
            "revenue": {"type": "number", "description": "Total revenue"},
            "expenses": {"type": "number", "description": "Total expenses"}
        }
    })
)
print(response.extraction)
```

### Extract from Table Chunks

```python
parsed = client.parse(document=Path("financial_report.pdf"))
tables = [c for c in parsed.chunks if c.type == "table"]

if tables:
    response = client.extract(
        markdown=tables[0].markdown,
        schema=json.dumps({
            "type": "object",
            "properties": {
                "revenue": {"type": "number", "description": "Total revenue"},
                "expenses": {"type": "number", "description": "Total expenses"}
            }
        })
    )
    print(response.extraction)
```

### Grounding References (Tracing Extracted Values to Source)

```python
parsed = client.parse(document=Path("doc.pdf"))
chunk_map = {c.id: c for c in parsed.chunks}

response = client.extract(
    markdown=parsed.markdown,
    schema=json.dumps(InvoiceData.model_json_schema())
)

for field, meta in response.extraction_metadata.items():
    if meta.get("references"):
        chunk = chunk_map.get(meta["references"][0])
        if chunk:
            print(f"{field}: page {chunk.grounding.page}, type={chunk.type}")
```

### Extract Response Structure

```python
response.extraction            # dict — Extracted data matching your schema
response.extraction_metadata   # dict — References linking fields to source chunks
response.metadata              # object — credit_usage, duration_ms, schema_violation_error, etc.
```

## 3. Split API

Classifies and splits mixed-document bundles by type.

### Basic Splitting

```python
parsed = client.parse(document=Path("mixed_documents.pdf"))

response = client.split(
    markdown=parsed.markdown,
    split_class=[
        {"name": "Invoice", "description": "Sales invoice", "identifier": "Invoice Number"},
        {"name": "Receipt", "description": "Payment receipt", "identifier": "Receipt Number"},
    ],
    model="split-latest"
)

for split in response.splits:
    print(f"{split.classification}: {split.identifier} (pages {split.pages})")
```

### Split Class Structure

Each entry in `split_class` has:
- `name` (required) — Classification label
- `description` (optional) — Helps improve classification accuracy
- `identifier` (optional) — Field to group/label documents by (e.g., "Invoice Number")

### Split → Extract Pipeline

```python
import json

parsed = client.parse(document=Path("mixed_invoices.pdf"))

splits = client.split(
    markdown=parsed.markdown,
    split_class=[
        {"name": "Invoice", "identifier": "Invoice Number"},
        {"name": "Credit Note", "identifier": "Credit Note Number"},
    ]
)

schema = json.dumps({
    "type": "object",
    "properties": {
        "document_number": {"type": "string"},
        "total": {"type": "number"},
        "date": {"type": "string"}
    }
})

results = []
for split in splits.splits:
    extracted = client.extract(markdown=split.markdowns[0], schema=schema)
    results.append({
        "type": split.classification,
        "id": split.identifier,
        **extracted.extraction
    })
```

### Split Response Structure

```python
response.splits                   # list of split objects
split.classification              # str — Document type (matches split_class name)
split.identifier                  # str — Value of identifier field (e.g., "INV-001")
split.markdowns                   # list[str] — Markdown content for this section
split.pages                       # list[int] — Page numbers this split covers
split.chunks                      # list[str] — Chunk IDs in this split
```

## 4. Parse Jobs (Async, Large Files)

For large files (>50MB), use asynchronous processing.

```python
import time

# Create job
job = client.parse_jobs.create(document=Path("large.pdf"), model="dpt-2-latest")
print(f"Job ID: {job.job_id}")

# Poll for completion
while True:
    status = client.parse_jobs.get(job.job_id)
    print(f"Status: {status.status}, Progress: {status.progress * 100:.0f}%")

    if status.status == "completed":
        result = status.result  # Same structure as client.parse() response
        break
    elif status.status == "failed":
        raise RuntimeError(f"Job failed: {status.failure_reason}")

    time.sleep(5)

# List jobs
jobs = client.parse_jobs.list(status="processing")
for j in jobs.jobs:
    print(f"{j.job_id}: {j.status} ({j.progress * 100:.0f}%)")
```

Job statuses: `pending` → `processing` → `completed` | `failed` | `cancelled`

## Error Handling

```python
from landingai_ade.exceptions import (
    RateLimitError,
    APITimeoutError,
    APIStatusError,
    APIConnectionError,
)
import time

try:
    response = client.parse(document=Path("doc.pdf"))
except RateLimitError:
    print("Rate limit exceeded — implement exponential backoff")
except APITimeoutError:
    print("Request timed out — use parse jobs for large files")
except APIConnectionError:
    print("Network error — retry with backoff")
except APIStatusError as e:
    if e.status_code == 413:
        print("File too large — use parse jobs API")
    elif e.status_code == 401:
        print("Invalid API key — check VISION_AGENT_API_KEY")
    else:
        print(f"API error: {e.status_code}")
```

### Retry with Fallback to Parse Jobs

```python
def parse_with_retry(client, file_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.parse(document=Path(file_path))
        except RateLimitError:
            wait = 2 ** attempt * 10
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except APITimeoutError:
            print("Timeout — switching to parse jobs")
            job = client.parse_jobs.create(document=Path(file_path))
            return poll_job(client, job.job_id)
        except APIConnectionError:
            print(f"Network error, attempt {attempt + 1}/{max_retries}")
            time.sleep(2)
        except APIStatusError as e:
            if e.status_code == 413:
                print("File too large — use parse jobs")
                job = client.parse_jobs.create(document=Path(file_path))
                return poll_job(client, job.job_id)
            raise
    raise RuntimeError("Failed after retries")

def poll_job(client, job_id, timeout=300):
    import time as t
    start = t.time()
    while t.time() - start < timeout:
        status = client.parse_jobs.get(job_id)
        if status.status == "completed":
            return status.result
        if status.status == "failed":
            raise RuntimeError(f"Job failed: {status.failure_reason}")
        t.sleep(5)
    raise TimeoutError("Job did not complete in time")
```

### HTTP Status Codes

| Status | Error Type | Description | Solution |
|--------|------------|-------------|----------|
| 400 | `validation_error` | Invalid parameters | Check request format |
| 401 | `authentication_error` | Invalid API key | Check `VISION_AGENT_API_KEY` |
| 413 | `payload_too_large` | File too large | Use Parse Jobs API |
| 429 | `rate_limit_error` | Too many requests | Exponential backoff |
| 500 | `internal_error` | Server error | Retry with backoff |
| 504 | `timeout_error` | Request timeout | Use Parse Jobs API |

## Async / Concurrent Processing

```python
import asyncio
from landingai_ade import AsyncLandingAIADE
from pathlib import Path

async def parse_multiple(files: list[str]):
    client = AsyncLandingAIADE()

    tasks = [client.parse(document=Path(f)) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for file, result in zip(files, results):
        if isinstance(result, Exception):
            print(f"Failed {file}: {result}")
        else:
            print(f"Parsed {file}: {result.metadata.page_count} pages")

    return [r for r in results if not isinstance(r, Exception)]
```

## Best Practices

1. **Parse once, extract many** — Cache `response.markdown` and reuse it for multiple extract/split calls.
2. **Use specific schemas** — Extract only the fields you need; avoid extracting everything.
3. **File size routing** — Use synchronous `client.parse()` for files < 50MB, `client.parse_jobs` for larger files.
4. **Rate limiting** — Implement exponential backoff starting at 1 second, doubling on each retry, max 5 retries.
5. **Table cell access** — Parse HTML `<tr>`/`<td>` from `chunk.markdown` to get cell content. Do not use grounding for cell content extraction; grounding is for visual positioning only.
6. **Spreadsheet grounding** — `grounding` is `null` for spreadsheet table chunks. Cell positions are encoded in the HTML element IDs (e.g., `Sheet 1-B2`).
7. **Schema design** — Keep schemas simple and flat when possible. Use clear field descriptions. Mark optional fields appropriately.

## Useful Links

- **Python SDK Docs:** https://docs.landing.ai/ade/ade-python
- **API Reference:** https://docs.landing.ai/api-reference
- **Python SDK Repository:** https://github.com/landing-ai/ade-python
- **TypeScript SDK:** https://docs.landing.ai/ade/ade-typescript
- **Supported File Types:** https://docs.landing.ai/ade/ade-file-types
