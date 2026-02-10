# LandingAI ADE — MCP Tools Reference

MCP (Model Context Protocol) tools for direct use within Claude conversations.

> For response structures and data types see the [API Specification](API_SPEC.md).

## Cost Warning

**MCP tools return full responses into the conversation context**, increasing token usage ~100x compared to API/SDK approaches. Always use `jq_filter` to minimize context size.

| Approach | Parse 50-page PDF | Tokens Used |
|----------|-------------------|-------------|
| API/SDK | Store locally, extract specific data | ~500 tokens |
| MCP Tools | Full response in context | ~50,000+ tokens |

**Use MCP tools for**: Quick prototypes, small docs (< 5 pages), one-off analysis, exploratory work.
**Avoid for**: Large documents, production workflows, batch processing, cost-sensitive apps.

## Available Tools

### 1. Parse — `mcp__landingai-ade-mcp__parse_client`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document` | string | One required | Local file path |
| `document_url` | string | One required | Remote URL |
| `model` | string | No | Default: `dpt-2-latest` |
| `split` | string | No | `"page"` for page splitting |
| `jq_filter` | string | No | JQ filter to reduce response |

```
Parse invoice.pdf using mcp__landingai-ade-mcp__parse_client
with jq_filter=".markdown"
```

### 2. Extract — `mcp__landingai-ade-mcp__extract_client`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schema` | string | Yes | JSON Schema for extraction |
| `markdown` | string | One required | Markdown content |
| `markdown_url` | string | One required | URL to markdown |
| `model` | string | No | Default: `extract-latest` |
| `jq_filter` | string | No | JQ filter to reduce response |

```
Extract from invoice.pdf using mcp__landingai-ade-mcp__extract_client
with schema='{"type": "object", "properties": {"invoice_number": {"type": "string"}, "total": {"type": "number"}}}'
and jq_filter=".extraction"
```

### 3. Split — `mcp__landingai-ade-mcp__split_client`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `split_class` | array | Yes | Classification config |
| `markdown` | string | One required | Markdown to split |
| `markdownUrl` | string | One required | URL to markdown |
| `model` | string | No | Default: `split-latest` |
| `jq_filter` | string | No | JQ filter to reduce response |

```
Split using mcp__landingai-ade-mcp__split_client with:
- split_class: [{"name": "Invoice", "identifier": "Invoice Number"}, {"name": "Receipt"}]
- jq_filter: ".splits[] | {type: .classification, pages: .pages}"
```

### 4. Parse Jobs — `mcp__landingai-ade-mcp__create_parse_jobs`

For large files (>50MB):
```
Create parse job using mcp__landingai-ade-mcp__create_parse_jobs
with jq_filter=".job_id"
```

Check status — `mcp__landingai-ade-mcp__get_parse_jobs`:
```
Check job using mcp__landingai-ade-mcp__get_parse_jobs
with job_id="..." and jq_filter="{status: .status, progress: .progress}"
```

List jobs — `mcp__landingai-ade-mcp__list_parse_jobs`:
```
List jobs using mcp__landingai-ade-mcp__list_parse_jobs
with status="processing" and jq_filter=".jobs[] | {id: .job_id, progress: .progress}"
```

### 5. Documentation Search — `mcp__landingai-ade-mcp__search_docs`

```
Search docs using mcp__landingai-ade-mcp__search_docs
with query="table extraction" and language="python"
```

## JQ Filter Recipes

Always use `jq_filter` — never return unfiltered responses.

| Filter | Returns | Use Case |
|--------|---------|----------|
| `.markdown` | Just markdown text | Document text only |
| `.extraction` | Extracted data | Schema extraction results |
| `.extraction.field_name` | Single field | One specific value |
| `.chunks \| length` | Chunk count | Quick structure check |
| `.chunks[] \| select(.type == "table")` | Table chunks only | Table extraction |
| `.chunks[0:5]` | First 5 chunks | Preview document start |
| `.metadata` | Just metadata | Page count, credits, timing |
| `{pages: .metadata.page_count, chunks: .chunks \| length}` | Summary stats | Quick overview |
| `.splits[] \| {type: .classification, pages: .pages}` | Split summaries | Classification results |
| `.chunks[] \| select(.grounding.page == 0)` | Page 0 chunks | Specific page content |

## Optimization Strategies

### 1. Use Direct Extraction When Possible
Skip parsing if you only need structured data — extract directly from the document:
```
Extract from document.pdf with schema={...} and jq_filter=".extraction"
// ~1,000 tokens instead of 60,000+
```

### 2. Filter Arrays Early
```
// Good: first 10 chunks only
jq_filter=".chunks[0:10]"

// Bad: all chunks
jq_filter=".chunks"
```

### 3. Chain JQ Operations
```
jq_filter='.chunks[] | select(.type == "table") | select(.grounding.page < 5) | .markdown'
```

### 4. Check Metadata First
Before processing a full document, check its size:
```
Parse doc.pdf with jq_filter=".metadata"
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid schema` | Malformed JSON schema | Validate schema JSON |
| `File not found` | Invalid file path | Check file exists |
| `Rate limit exceeded` | Too many requests | Wait and retry |
| `Document too large` | File >50MB | Use `create_parse_jobs` instead |

## Token Usage Estimates

- Markdown: ~10-20 tokens per line
- Chunks: ~500-1000 tokens each
- Grounding entries: ~50 tokens each
- If tokens exceed ~10,000 per operation, consider switching to API/SDK
