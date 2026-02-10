# LandingAI ADE — API (curl) Reference

Direct HTTP API implementation using curl and shell scripts.

> For request parameters, response structures, and data types see the [API Specification](API_SPEC.md).

## Authentication

```bash
export VISION_AGENT_API_KEY="v2_..."
# All requests need:
-H "Authorization: Bearer $VISION_AGENT_API_KEY"
```

## 1. Parse Examples

> See [Parse API Specification](API_SPEC.md#1-parse-api) for parameters and response structure.

### Basic Parse
```bash
curl -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@document.pdf" \
  -F "model=dpt-2-latest"
```

### Parse with Page Splitting
```bash
curl -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@multi_page.pdf" \
  -F "split=page"
```

### Parse from URL
```bash
curl -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document_url=https://example.com/document.pdf"
```

## 2. Extract Examples

> See [Extract API Specification](API_SPEC.md#2-extract-api) for parameters and response structure.

### Direct Extraction from Document
```bash
SCHEMA='{
  "type": "object",
  "properties": {
    "invoice_number": {"type": "string", "description": "Invoice number"},
    "total_amount": {"type": "number", "description": "Total amount"},
    "vendor_name": {"type": "string", "description": "Vendor name"}
  }
}'

curl -X POST https://api.landing.ai/v1/ade/extract \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@invoice.pdf" \
  -F "schema=$SCHEMA" \
  -F "model=extract-latest"
```

### Extract from Parsed Markdown (Parse Once, Extract Many)
```bash
# Parse once
MARKDOWN=$(curl -s -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@invoice.pdf" \
  | jq -r '.markdown')

# Extract with different schemas
curl -X POST https://api.landing.ai/v1/ade/extract \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "markdown=$MARKDOWN" \
  -F "schema=$SCHEMA"
```

### Complex Nested Extraction
```bash
PO_SCHEMA='{
  "type": "object",
  "properties": {
    "po_number": {"type": "string"},
    "line_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sku": {"type": "string"},
          "quantity": {"type": "integer"},
          "unit_price": {"type": "number"}
        }
      }
    },
    "total": {"type": "number"}
  }
}'

curl -X POST https://api.landing.ai/v1/ade/extract \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@purchase_order.pdf" \
  -F "schema=$PO_SCHEMA"
```

## 3. Split Examples

> See [Split API Specification](API_SPEC.md#3-split-api) for parameters and response structure.

### Basic Document Splitting
```bash
SPLIT_CLASSES='[
  {"name": "Invoice", "identifier": "Invoice Number"},
  {"name": "Receipt", "identifier": "Receipt Number"},
  {"name": "Purchase Order", "identifier": "PO Number"}
]'

# Parse first, then split
MARKDOWN=$(curl -s -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@mixed_documents.pdf" \
  | jq -r '.markdown')

curl -X POST https://api.landing.ai/v1/ade/split \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "markdown=$MARKDOWN" \
  -F "split_class=$SPLIT_CLASSES" \
  -F "model=split-latest"
```

## 4. Parse Jobs (Async, Large Files)

> See [Parse Jobs Specification](API_SPEC.md#4-parse-jobs-api-async) for parameters and response structure.

### Create and Monitor Job
```bash
#!/bin/bash

# Create job for large file
JOB_ID=$(curl -s -X POST https://api.landing.ai/v1/ade/parse/jobs \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@large_document.pdf" \
  -F "model=dpt-2-latest" \
  | jq -r '.job_id')

echo "Created job: $JOB_ID"

# Poll for completion
while true; do
  STATUS=$(curl -s -X GET "https://api.landing.ai/v1/ade/parse/jobs/$JOB_ID" \
    -H "Authorization: Bearer $VISION_AGENT_API_KEY")

  STATE=$(echo "$STATUS" | jq -r '.status')
  PROGRESS=$(echo "$STATUS" | jq -r '.progress')

  echo "Status: $STATE, Progress: $(echo "$PROGRESS * 100" | bc)%"

  if [ "$STATE" = "completed" ]; then
    echo "$STATUS" | jq '.result' > "parse_result.json"
    break
  elif [ "$STATE" = "failed" ]; then
    echo "Job failed: $(echo "$STATUS" | jq -r '.failure_reason')" >&2
    exit 1
  fi

  sleep 5
done
```

## Complete Workflows

### Parse, Split, and Extract Pipeline
```bash
#!/bin/bash

# 1. Parse mixed document
PARSED=$(curl -s -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@mixed_invoices.pdf")

MARKDOWN=$(echo "$PARSED" | jq -r '.markdown')

# 2. Split by document type
SPLIT_CLASSES='[
  {"name": "Invoice", "identifier": "Invoice Number"},
  {"name": "Credit Note", "identifier": "Credit Note Number"}
]'

SPLITS=$(curl -s -X POST https://api.landing.ai/v1/ade/split \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "markdown=$MARKDOWN" \
  -F "split_class=$SPLIT_CLASSES")

# 3. Extract from each split
SCHEMA='{"type": "object", "properties": {
  "document_number": {"type": "string"},
  "total": {"type": "number"},
  "date": {"type": "string"}
}}'

echo "$SPLITS" | jq -c '.splits[]' | while read -r split; do
  TYPE=$(echo "$split" | jq -r '.classification')
  ID=$(echo "$split" | jq -r '.identifier')
  MD=$(echo "$split" | jq -r '.markdowns[0]')

  echo "Processing $TYPE: $ID"

  curl -s -X POST https://api.landing.ai/v1/ade/extract \
    -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
    -F "markdown=$MD" \
    -F "schema=$SCHEMA" \
    | jq '.extraction'
done
```

### Table Data Extraction
```bash
#!/bin/bash

PARSED=$(curl -s -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@financial_report.pdf")

# Get first table's markdown
TABLE_MD=$(echo "$PARSED" | jq -r '
  .chunks[] | select(.type == "table") | .markdown' | head -1)

if [ -z "$TABLE_MD" ]; then
  echo "No tables found" >&2
  exit 1
fi

TABLE_SCHEMA='{"type": "object", "properties": {
  "revenue_2023": {"type": "number"},
  "revenue_2024": {"type": "number"},
  "profit_2023": {"type": "number"},
  "profit_2024": {"type": "number"}
}}'

curl -s -X POST https://api.landing.ai/v1/ade/extract \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "markdown=$TABLE_MD" \
  -F "schema=$TABLE_SCHEMA" \
  | jq '.extraction'
```

## Error Handling

### HTTP Status Check with Retry
```bash
#!/bin/bash

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST https://api.landing.ai/v1/ade/parse \
    -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
    -F "document=@document.pdf")

  HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
  BODY=$(echo "$RESPONSE" | sed '$d')

  if [ "$HTTP_CODE" -eq 200 ]; then
    echo "$BODY"
    break
  elif [ "$HTTP_CODE" -eq 429 ]; then
    WAIT_TIME=$((2 ** RETRY_COUNT * 10))
    echo "Rate limited. Waiting ${WAIT_TIME}s..." >&2
    sleep $WAIT_TIME
    RETRY_COUNT=$((RETRY_COUNT + 1))
  elif [ "$HTTP_CODE" -eq 413 ] || [ "$HTTP_CODE" -eq 504 ]; then
    echo "File too large or timeout — use parse jobs API" >&2
    exit 1
  else
    echo "Error: HTTP $HTTP_CODE" >&2
    echo "$BODY" | jq '.error' >&2
    exit 1
  fi
done
```

## jq Recipes

```bash
# Extract just markdown
curl -s ... | jq -r '.markdown'

# Get all tables
curl -s ... | jq '.chunks[] | select(.type == "table")'

# Extract table cells with positions
curl -s ... | jq '.grounding | to_entries[] | select(.value.type == "tableCell")'

# Get chunks from specific page
curl -s ... | jq '.chunks[] | select(.grounding.page == 0)'

# Group chunks by type with counts
curl -s ... | jq '.chunks | group_by(.type) | map({type: .[0].type, count: length})'

# Tables as CSV
curl -s ... | jq -r '.chunks[] | select(.type == "table") | .markdown' | sed 's/|/,/g; s/^,//; s/,$//'

# Calculate bounding box areas
curl -s ... | jq '[.chunks[] | .grounding.box | ((.right - .left) * (.bottom - .top))] | add'

# Get specific extracted field
curl -s ... | jq '.extraction.invoice_number'

# Process extracted line items
curl -s ... | jq '.extraction.line_items[] | {sku: .sku, total: (.quantity * .unit_price)}'
```

## Best Practices

### Save Intermediate Results
```bash
# Save parsed output for reuse (parse once, extract many)
curl -s -X POST https://api.landing.ai/v1/ade/parse \
  -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
  -F "document=@document.pdf" | tee parsed_output.json

# Later, extract from saved markdown
MARKDOWN=$(jq -r '.markdown' < parsed_output.json)
```

### Shell Functions for Reuse
```bash
ade_parse() {
  curl -s -X POST https://api.landing.ai/v1/ade/parse \
    -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
    -F "document=@$1"
}

ade_extract() {
  curl -s -X POST https://api.landing.ai/v1/ade/extract \
    -H "Authorization: Bearer $VISION_AGENT_API_KEY" \
    -F "document=@$1" \
    -F "schema=$2"
}
```
