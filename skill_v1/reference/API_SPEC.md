# LandingAI ADE API Specification

Complete API specification for LandingAI's Agentic Document Extraction (ADE).

## Overview

ADE provides a REST API for document parsing, splitting, data extraction, and large file parse jobs. All SDKs and tools (Python, TypeScript, MCP) use this same underlying API.

## Base Configuration

| Region | Base URL |
|--------|----------|
| US (default) | `https://api.va.landing.ai/v1/ade` |
| EU | `https://api.va.eu-west-1.landing.ai/v1/ade` |

**Authentication**: All requests require `Authorization: Bearer $VISION_AGENT_API_KEY`

## Implementation Guides

- [API Reference (curl)](API_REFERENCE.md) — Shell scripts, jq recipes, error handling
- [Python SDK Reference](PYTHON_REFERENCE.md) — Pydantic schemas, async, exception handling
- [TypeScript SDK Reference](TYPESCRIPT_REFERENCE.md) — Type definitions, Zod, async/await
- [MCP Tools Reference](MCP_REFERENCE.md) — Direct integration (higher token cost)

## API Endpoints

### 1. Parse API

**Endpoint**: `POST /parse`

Converts documents to structured json with visual grounding.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document` | file | One required | Local file — PDF, images (JPG/PNG/TIFF/WEBP/GIF/BMP/PSD + more), Word (DOC/DOCX/ODT), PowerPoint (PPT/PPTX/ODP), spreadsheets (XLSX/CSV) |
| `document_url` | string | One required | Remote document URL |
| `model` | string | No | Model version (default: `dpt-2-latest`) |
| `split` | string | No | Split mode: `"page"` to split by pages |

#### Response Structure

```json
{
  "markdown": "string",          // Complete document as markdown
  "chunks": [                    // Array of content blocks
    {
      "id": "uuid",              // Unique identifier
      "type": "text, table, marginalia, figure, scan_code, logo, card and attestation", //Chunk type
      "markdown": "string",      // Chunk content
      "grounding": {             // Location in document
        "page": 0,               // Zero-indexed page number
        "box": {                 // Normalized coordinates (0-1)
          "left": 0.1,
          "top": 0.2,
          "right": 0.9,
          "bottom": 0.3
        }
      }
    }
  ],
  "grounding": {                 // Detailed location mapping
    "chunk-id": {              // Chunk grounding (has "chunk" prefix)
      "type": "chunkText|chunkTable|chunkFigure|chunkLogo|chunkCard|chunkAttestation| chunkScanCode|chunkForm|chunkMarginalia| chunkTitle|chunkPageHeader|chunkPageFooter| chunkPageNumber|chunkKeyValue|table|tableCell",
      "page": 0,
      "box": { /* BoundingBox */ }
    },
    "0-1": {                     // Table grounding (format: page-id)
      "type": "table",
      "page": 0,
      "box": { /* BoundingBox */ }
    },
    "0-2": {                     // Table cell grounding
      "type": "tableCell",
      "page": 0,
      "box": { /* BoundingBox */ },
      "position": {              // Cell position data
        "row": 0,
        "col": 0,
        "rowspan": 1,
        "colspan": 1,
        "chunk_id": "uuid"       // Parent table chunk
      }
    }
  },
  "splits": [                    // Only if split="page"
    {
      "chunks": ["chunk-id-1", "chunk-id-2"],
      "class": "page",
      "identifier": "0",
      "markdown": "string",
      "pages": [0]
    }
  ],
  "metadata": {
    "filename": "document.pdf",
    "org_id": "org_abc123",
    "page_count": 5,
    "duration_ms": 1234,
    "credit_usage": 3,
    "version": "dpt-2-latest",
    "job_id": "job_abc123",
    "failed_pages": []           // List of pages that failed to parse
  }
}
```

### 2. Extract API

**Endpoint**: `POST /extract`

Extracts structured data from documents or markdown using JSON schemas.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schema` | JSON string | Yes | JSON Schema defining extraction structure |
| `document` | file | One required | Direct extraction from file |
| `markdown` | string | One required | Markdown content to extract from |
| `markdown_url` | string | One required | URL to markdown content |
| `model` | string | No | Model version (default: `extract-latest`) |

#### Response Structure

```json
{
  "extraction": {                // Extracted data matching schema
    "field1": "value1",
    "field2": 123,
    "nested": {
      "subfield": "value"
    },
    "array": [/* items */]
  },
  "extraction_metadata": {       // References to source chunks
    "field1": {
      "references": ["chunk-uuid-1", "chunk-uuid-2"]
    },
    "field2": {
      "references": ["chunk-uuid-3"]
    }
  },
  "metadata": {
    "credit_usage": 1,
    "duration_ms": 567,
    "filename": "document.pdf",
    "job_id": "job_xyz",
    "org_id": "org_abc",
    "version": "extract-latest",
    "fallback_model_version": null,
    "schema_violation_error": null  // Error if extraction doesn't match schema
  }
}
```

### 3. Split API

**Endpoint**: `POST /split`

Classifies and splits mixed documents by type.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `split_class` | JSON array | Yes | Classification configuration (see below) |
| `markdown` | string | One required | Markdown content to split |
| `markdownUrl` | string | One required | URL to markdown content |
| `model` | string | No | Model version (default: `split-latest`) |

#### Split Class Structure

```json
{
  "name": "Invoice",              // Required: Classification name
  "description": "Sales invoice", // Optional: Description for better classification
  "identifier": "Invoice Number"  // Optional: Field to group documents by
}
```

#### Response Structure

```json
{
  "splits": [                     // Array of classified document sections
    {
      "chunks": ["chunk-id-1", "chunk-id-2"],
      "class": "Invoice",         // Same as classification
      "classification": "Invoice",
      "identifier": "INV-001",    // Value of identifier field
      "markdowns": ["# Invoice content..."],
      "pages": [0, 1]             // Page numbers this split covers
    }
  ],
  "metadata": {
    "credit_usage": 2,
    "duration_ms": 789,
    "filename": "mixed_documents.pdf",
    "page_count": 10,
    "job_id": "job_split",
    "org_id": "org_abc",
    "version": "split-latest"
  }
}
```

### 4. Parse Jobs API (Async)

For large files (>50MB), use asynchronous processing.

#### Create Job

**Endpoint**: `POST /parse/jobs`

**Parameters**: Same as Parse API plus:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `output_save_url` | string | If ZDR | URL for zero data retention output |

**Response**:
```json
{
  "job_id": "cml1kaihb08dxcn01b3mlfy5b"
}
```

#### Get Job Status

**Endpoint**: `GET /parse/jobs/{job_id}`

**Response**:
```json
{
  "job_id": "cml1kaihb08dxcn01b3mlfy5b",
  "status": "pending|processing|completed|failed|cancelled",
  "progress": 0.75,              // 0-1 progress indicator
  "failure_reason": null,         // Error message if failed
  "received_at": 1234567890,     // Unix timestamp
  "result": { /* ParseResponse */ }  // Only when completed
}
```

#### List Jobs

**Endpoint**: `GET /parse/jobs`

**Query Parameters**:
- `status`: Filter by status
- `page`: Page number (0-indexed)
- `pageSize`: Items per page

**Response**:
```json
{
  "jobs": [                       // Array of job summaries
    {
      "job_id": "...",
      "status": "processing",
      "progress": 0.5,
      "failure_reason": null,
      "received_at": 1234567890
    }
  ],
  "has_more": true,
  "org_id": "org_abc"
}
```

## Data Types

### Chunk Types
- `text` - Text paragraphs and content
- `table` - Table structures
- `figure` - Images and diagrams
- `formula` - Mathematical formulas
- `list` - Bulleted or numbered lists

### Grounding Types

#### For Chunks (with "chunk" prefix)
- `chunkText` - Text chunk grounding
- `chunkTable` - Table chunk grounding
- `chunkFigure` - Figure chunk grounding
- `chunkFormula` - Formula chunk grounding
- `chunkList` - List chunk grounding

#### For Structure Elements (no prefix)
- `table` - Actual table structure
- `tableCell` - Individual table cell with position

### Bounding Box

All coordinates are normalized to 0-1 range:

```json
{
  "left": 0.1,    // Distance from left edge (10% of width)
  "top": 0.2,     // Distance from top edge (20% of height)
  "right": 0.9,   // Distance from left edge (90% of width)
  "bottom": 0.3   // Distance from top edge (30% of height)
}
```

### Table Cell Position

```json
{
  "row": 0,         // Zero-indexed row number
  "col": 0,         // Zero-indexed column number
  "rowspan": 1,     // Number of rows this cell spans
  "colspan": 2,     // Number of columns this cell spans
  "chunk_id": "..." // UUID of parent table chunk
}
```

### Table Chunk Formats

Table chunks render as HTML. The ID format and grounding availability differ by source document type.

#### PDF / Image / Document Tables

Element IDs use the format `{page_number}-{base62_sequential_number}` (page starts at 0, numbers increment per element within the page). If a page has multiple tables, numbering continues sequentially across all tables on that page. Cells may include `rowspan`/`colspan` attributes.

The `grounding` object contains bounding boxes and `tableCell` position entries for every cell.

```html
<a id='chunk-uuid'></a>

<table id="0-1">
<tr><td id="0-2" colspan="2">Product Summary</td></tr>
<tr><td id="0-3">Product</td><td id="0-4">Revenue</td></tr>
<tr><td id="0-5">Hardware</td><td id="0-6">15,230</td></tr>
</table>
```

#### Spreadsheet Tables (XLSX / CSV)

Element IDs use the format `{tab_name}-{cell_reference}` (e.g., `Sheet 1-A1`). The table element itself uses `{tab_name}-{start_cell}:{end_cell}` (e.g., `Sheet 1-A1:B4`). Embedded images and charts become `figure` chunks.

**`grounding` is `null`** for spreadsheet table chunks — cell positions are encoded in the IDs themselves.

```html
<a id='Sheet 1-A1:B4-chunk'></a>

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

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "message": "Human-readable error message",
    "type": "error_type",
    "details": {
      "field": "problem_field",
      "reason": "Specific reason"
    }
  }
}
```

### HTTP Status Codes

| Status | Error Type | Description | Solution |
|--------|------------|-------------|----------|
| 400 | `validation_error` | Invalid parameters | Check request format |
| 401 | `authentication_error` | Invalid API key | Check VISION_AGENT_API_KEY |
| 413 | `payload_too_large` | File too large | Use Parse Jobs API |
| 429 | `rate_limit_error` | Too many requests | Implement backoff |
| 500 | `internal_error` | Server error | Retry with backoff |
| 504 | `timeout_error` | Request timeout | Use Parse Jobs API |

## Model Versions

| Operation | Current Version | Description |
|-----------|----------------|-------------|
| Parse | `dpt-2-latest` | Document parsing and OCR |
| Extract | `extract-latest` | Schema-based extraction |
| Split | `split-latest` | Document classification |

## Supported File Types

| Category | Formats | Notes |
|----------|---------|-------|
| **PDF** | PDF | Up to 100 pages; no password-protected files |
| **Images** | JPEG, JPG, PNG, APNG, BMP, DCX, DDS, DIB, GD, GIF, ICNS, JP2, PCX, PPM, PSD, TGA, TIF, TIFF, WEBP | |
| **Text Documents** | DOC, DOCX, ODT | Converted to PDF before parsing |
| **Presentations** | ODP, PPT, PPTX | Converted to PDF before parsing |
| **Spreadsheets** | CSV, XLSX | Up to 10 MB in Playground; no sheet/column/row limits |

> **Note:** Word, PowerPoint, and OpenDocument files are converted to PDF server-side before parsing. The output is the same structured markdown as a direct PDF upload.

## Best Practices

### 1. File Size Handling
- < 50MB: Use synchronous Parse API
- > 50MB: Use Parse Jobs API
- > 100MB: Consider splitting document first

### 2. Rate Limiting
- Implement exponential backoff
- Start with 1 second delay
- Double delay on each retry
- Maximum 5 retries

### 3. Schema Design
- Keep schemas simple and flat when possible
- Use clear descriptions for each field
- Mark optional fields appropriately
- Test schema with sample data first

### 4. Cost Optimization
- Parse once, extract multiple times
- Use specific schemas (avoid extracting everything)
- For MCP tools, always use jq_filter
- Cache parsed results when possible

