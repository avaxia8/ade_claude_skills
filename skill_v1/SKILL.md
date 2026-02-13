---
name: landingai-ade
description: Parse, split, extract, and analyze documents using LandingAI's ADE (Agentic Document Extraction). Supports PDFs, images (JPG/PNG/TIFF/WEBP/GIF/BMP/PSD and more), Word (DOC/DOCX), PowerPoint (PPT/PPTX), spreadsheets (XLSX/CSV), and OpenDocument formats (ODT/ODP). Use when the user wants to convert documents to structured markdown, extract fields with JSON schemas, split and classify mixed document bundles, or work with table cell positions and visual grounding. Handles invoices, receipts, financial reports, contracts, purchase orders, and any structured or semi-structured document.
---

# LandingAI ADE (Agentic Document Extraction)

## Core Workflow

ADE follows a three-step pipeline:

1. **Parse** — Convert documents (PDFs, images, Word, PowerPoint, Excel/CSV) to markdown with visual grounding and bounding boxes
2. **Split** *(optional)* — Classify pages in a mixed-document bundle by type (invoice, receipt, contract, etc.)
3. **Extract** — Pull structured fields from markdown using a JSON schema

Parse once, then split/extract as many times as needed against the cached markdown.

## Choose Your Approach

| Approach | Best For | Setup |
|----------|----------|-------|
| **Direct API** (curl) | Shell scripts, CI/CD, language-agnostic | API key only |
| **Python SDK** | Data pipelines, Pydantic schemas, async batch jobs | `pip install landingai-ade` |
| **TypeScript SDK** | Web apps, Node services, Zod validation | `npm install landingai-ade` |
| **MCP Tools** | Quick prototypes, small docs | **higher token cost** |

All approaches use the same API key: `export VISION_AGENT_API_KEY="v2_..."`

## Key Features

- **Document Parsing** — PDFs, images, Word/PowerPoint/ODT, and spreadsheets to structured markdown with chunk types (text, table, marginalia, figure, scan_code, logo, card and attestation)
- **Visual Grounding** — Normalized 0-1 bounding boxes mapping every chunk to its source location
- **Table Cell Positions** — Row/col/rowspan/colspan for every cell in detected tables
- **Schema-based Extraction** — Define JSON schemas (or Pydantic/Zod models) to pull structured fields
- **Document Splitting and Classification** — Split mixed bundles by document type with custom identifiers
- **Large File Support** — Async parse jobs API for files up to 1GB

## Reference Docs

| File | Read when you need to... |
|------|--------------------------|
| **[API Specification](reference/API_SPEC.md)** | Look up request parameters, response structures, data types, error codes, or model versions — the single source of truth |
| **[API Reference](reference/API_REFERENCE.md)** | Write curl commands, shell scripts, or jq filters for document processing |
| **[Python Reference](reference/PYTHON_REFERENCE.md)** | Use the Python SDK — Pydantic schemas, async patterns, exception handling, save_to |
| **[TypeScript Reference](reference/TYPESCRIPT_REFERENCE.md)** | Use the TypeScript SDK — type definitions, Zod integration, parse jobs, error types |
| **[MCP Tools Reference](reference/MCP_REFERENCE.md)** | Call ADE directly via MCP tools — jq_filter optimization is critical |

## External Links

- [API Docs](https://docs.landing.ai/api-reference) | [Python SDK](https://docs.landing.ai/ade/ade-python) | [TypeScript SDK](https://docs.landing.ai/ade/ade-typescript)
- [Python GitHub](https://github.com/landing-ai/ade-python) | [TypeScript GitHub](https://github.com/landing-ai/ade-typescript)
