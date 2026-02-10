---
name: landingai-ade
description: Parse, extract, and analyze documents using LandingAI's ADE (Agentic Document Extraction). Use when the user wants to process PDFs, images, invoices, receipts, financial reports, contracts, or any document — converting them to structured data, extracting fields with schemas, classifying mixed document bundles, or working with table cell positions and visual grounding.
---

# LandingAI ADE (Agentic Document Extraction)

## Core Workflow

ADE follows a three-step pipeline:

1. **Parse** — Convert documents (PDF/images) to markdown with visual grounding and bounding boxes
2. **Split** *(optional)* — Classify pages in a mixed-document bundle by type (invoice, receipt, contract, etc.)
3. **Extract** — Pull structured fields from markdown using a JSON schema

Parse once, then split/extract as many times as needed against the cached markdown.

## Choose Your Approach

| Approach | Best For | Setup |
|----------|----------|-------|
| **Direct API** (curl) | Shell scripts, CI/CD, language-agnostic | API key only |
| **Python SDK** | Data pipelines, Pydantic schemas, async batch jobs | `pip install landingai-ade` |
| **TypeScript SDK** | Web apps, Node services, Zod validation | `npm install landingai-ade` |
| **MCP Tools** | Quick prototypes, small docs (< 5 pages) | Built into Claude — **100x higher token cost** |

All approaches use the same API key: `export VISION_AGENT_API_KEY="v2_..."`

## Key Features

- **Document Parsing** — PDFs and images to structured markdown with chunk types (text, table, figure, formula, list)
- **Visual Grounding** — Normalized 0-1 bounding boxes mapping every chunk to its source location
- **Table Cell Positions** — Row/col/rowspan/colspan for every cell in detected tables
- **Schema-based Extraction** — Define JSON schemas (or Pydantic/Zod models) to pull structured fields
- **Document Classification** — Split mixed bundles by document type with custom identifiers
- **Large File Support** — Async parse jobs API for files > 50MB

## Reference Docs

| File | Read when you need to... |
|------|--------------------------|
| **[API Specification](reference/API_SPEC.md)** | Look up request parameters, response structures, data types, error codes, or model versions — the single source of truth |
| **[API Reference](reference/API_REFERENCE.md)** | Write curl commands, shell scripts, or jq filters for document processing |
| **[Python Reference](reference/PYTHON_REFERENCE.md)** | Use the Python SDK — Pydantic schemas, async patterns, exception handling, save_to |
| **[TypeScript Reference](reference/TYPESCRIPT_REFERENCE.md)** | Use the TypeScript SDK — type definitions, Zod integration, parse jobs, error types |
| **[MCP Tools Reference](reference/MCP_REFERENCE.md)** | Call ADE directly from Claude via MCP tools — jq_filter optimization is critical |

## External Links

- [API Docs](https://docs.landing.ai/api-reference) | [Python SDK](https://docs.landing.ai/ade/ade-python) | [TypeScript SDK](https://docs.landing.ai/ade/ade-typescript)
- [Python GitHub](https://github.com/landing-ai/ade-python) | [TypeScript GitHub](https://github.com/landing-ai/ade-typescript)
