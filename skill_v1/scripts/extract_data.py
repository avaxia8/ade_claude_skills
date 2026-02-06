#!/usr/bin/env python3
"""
Data extraction examples using LandingAI ADE with schemas
"""

from pathlib import Path
from landingai_ade import LandingAIADE
from pydantic import BaseModel, Field
from typing import Optional, List
import json

def basic_extraction():
    """Basic extraction with simple schema"""
    client = LandingAIADE()
    
    # First parse the document
    parsed = client.parse(document=Path("invoice.pdf"))
    
    # Define extraction schema
    class InvoiceSchema(BaseModel):
        invoice_number: str = Field(description="Invoice number or ID")
        invoice_date: str = Field(description="Date of the invoice")
        vendor_name: str = Field(description="Name of the vendor/supplier")
        total_amount: float = Field(description="Total amount to be paid")
        tax_amount: Optional[float] = Field(description="Tax amount if present")
    
    # Extract data
    response = client.extract(
        markdown=parsed.markdown,
        schema=json.dumps(InvoiceSchema.model_json_schema()),
        model="extract-latest"
    )
    
    # Access extracted data
    data = response.extraction
    print("Extracted Invoice Data:")
    print(f"  Invoice #: {data.get('invoice_number')}")
    print(f"  Date: {data.get('invoice_date')}")
    print(f"  Vendor: {data.get('vendor_name')}")
    print(f"  Total: ${data.get('total_amount')}")
    print(f"  Tax: ${data.get('tax_amount', 'N/A')}")
    
    return response

def extract_with_grounding_references():
    """Extract data and trace back to source locations"""
    client = LandingAIADE()
    
    # Parse document
    parsed = client.parse(document=Path("paystub.pdf"))
    
    # Create chunk lookup dictionary
    chunk_lookup = {
        chunk.id: chunk for chunk in parsed.chunks
    }
    
    # Define schema
    class PayStubSchema(BaseModel):
        employee_name: str = Field(description="Employee's full name")
        gross_pay: float = Field(description="Gross pay amount")
        net_pay: float = Field(description="Net pay amount")
        pay_period: str = Field(description="Pay period dates")
        deductions: Optional[List[float]] = Field(description="List of deductions")
    
    # Extract
    response = client.extract(
        markdown=parsed.markdown,
        schema=json.dumps(PayStubSchema.model_json_schema()),
        model="extract-latest"
    )
    
    print("Extracted Data with Source Locations:")
    print("-" * 50)
    
    # Link extracted data to source locations
    for field_name, value in response.extraction.items():
        print(f"\nField: {field_name}")
        print(f"Value: {value}")
        
        # Get grounding references
        if field_name in response.extraction_metadata:
            refs = response.extraction_metadata[field_name].get("references", [])
            if refs:
                chunk_id = refs[0]  # First reference
                
                # Look up chunk details
                if chunk_id in chunk_lookup:
                    chunk = chunk_lookup[chunk_id]
                    print(f"Source: Page {chunk.grounding.page}")
                    print(f"Location: ({chunk.grounding.box.left:.3f}, {chunk.grounding.box.top:.3f})")
                    print(f"Chunk type: {chunk.type}")
                    
                    # Also check grounding dict for more details
                    if chunk_id in parsed.grounding:
                        grounding = parsed.grounding[chunk_id]
                        print(f"Grounding type: {grounding.type}")
    
    return response

def extract_complex_structure():
    """Extract complex nested data structures"""
    client = LandingAIADE()
    
    parsed = client.parse(document=Path("purchase_order.pdf"))
    
    # Define complex schema with nested structures
    class LineItem(BaseModel):
        item_number: str = Field(description="Item SKU or number")
        description: str = Field(description="Item description")
        quantity: int = Field(description="Quantity ordered")
        unit_price: float = Field(description="Price per unit")
        total: float = Field(description="Line item total")
    
    class Address(BaseModel):
        street: str = Field(description="Street address")
        city: str = Field(description="City")
        state: str = Field(description="State/Province")
        postal_code: str = Field(description="ZIP/Postal code")
        country: Optional[str] = Field(description="Country")
    
    class PurchaseOrder(BaseModel):
        po_number: str = Field(description="Purchase order number")
        order_date: str = Field(description="Order date")
        vendor_name: str = Field(description="Vendor/Supplier name")
        ship_to: Address = Field(description="Shipping address")
        bill_to: Optional[Address] = Field(description="Billing address")
        line_items: List[LineItem] = Field(description="List of ordered items")
        subtotal: float = Field(description="Subtotal before tax")
        tax: float = Field(description="Tax amount")
        shipping: Optional[float] = Field(description="Shipping cost")
        total: float = Field(description="Total amount")
        payment_terms: Optional[str] = Field(description="Payment terms")
        notes: Optional[str] = Field(description="Additional notes")
    
    # Extract complex structure
    response = client.extract(
        markdown=parsed.markdown,
        schema=json.dumps(PurchaseOrder.model_json_schema()),
        model="extract-latest",
        save_to="./extract_output"  # Save for debugging
    )
    
    # Process extracted data
    po_data = response.extraction
    print(f"Purchase Order: {po_data['po_number']}")
    print(f"Date: {po_data['order_date']}")
    print(f"Vendor: {po_data['vendor_name']}")
    
    # Process shipping address
    if 'ship_to' in po_data:
        ship = po_data['ship_to']
        print(f"\nShip To:")
        print(f"  {ship.get('street')}")
        print(f"  {ship.get('city')}, {ship.get('state')} {ship.get('postal_code')}")
    
    # Process line items
    print(f"\nLine Items:")
    for item in po_data.get('line_items', []):
        print(f"  - {item['description']}")
        print(f"    Qty: {item['quantity']} x ${item['unit_price']} = ${item['total']}")
    
    print(f"\nSubtotal: ${po_data['subtotal']}")
    print(f"Tax: ${po_data['tax']}")
    if po_data.get('shipping'):
        print(f"Shipping: ${po_data['shipping']}")
    print(f"Total: ${po_data['total']}")
    
    return response

def extract_tables_specifically():
    """Extract data specifically from tables"""
    client = LandingAIADE()
    
    parsed = client.parse(document=Path("financial_report.pdf"))
    
    # Find table chunks
    table_chunks = [c for c in parsed.chunks if c.type == "table"]
    print(f"Found {len(table_chunks)} tables")
    
    # Define schema for financial data
    class FinancialData(BaseModel):
        revenue_2023: float = Field(description="Revenue for 2023")
        revenue_2024: float = Field(description="Revenue for 2024")
        expenses_2023: float = Field(description="Expenses for 2023")
        expenses_2024: float = Field(description="Expenses for 2024")
        profit_2023: float = Field(description="Profit for 2023")
        profit_2024: float = Field(description="Profit for 2024")
    
    # Extract from table content
    if table_chunks:
        # Use first table's markdown
        table_markdown = table_chunks[0].markdown
        
        response = client.extract(
            markdown=table_markdown,  # Extract from specific table
            schema=json.dumps(FinancialData.model_json_schema()),
            model="extract-latest"
        )
        
        data = response.extraction
        print("\nExtracted Financial Data:")
        print(f"  2023 Revenue: ${data.get('revenue_2023', 0):,.2f}")
        print(f"  2024 Revenue: ${data.get('revenue_2024', 0):,.2f}")
        print(f"  2023 Profit: ${data.get('profit_2023', 0):,.2f}")
        print(f"  2024 Profit: ${data.get('profit_2024', 0):,.2f}")
        
        return response

def validate_and_extract():
    """Validate schema before extraction"""
    from pydantic import ValidationError
    
    client = LandingAIADE()
    parsed = client.parse(document=Path("document.pdf"))
    
    # Define schema with validation
    class ValidatedInvoice(BaseModel):
        invoice_number: str = Field(min_length=1, max_length=50)
        total_amount: float = Field(gt=0, le=1000000)
        tax_rate: float = Field(ge=0, le=1)  # 0-100%
        items_count: int = Field(ge=1)
    
    # Test schema with sample data first
    try:
        test_data = {
            "invoice_number": "INV-001",
            "total_amount": 1000.00,
            "tax_rate": 0.08,
            "items_count": 5
        }
        ValidatedInvoice(**test_data)
        print("Schema validation passed")
    except ValidationError as e:
        print(f"Schema validation error: {e}")
        return None
    
    # Extract with validated schema
    response = client.extract(
        markdown=parsed.markdown,
        schema=json.dumps(ValidatedInvoice.model_json_schema()),
        model="extract-latest"
    )
    
    # Validate extracted data
    try:
        validated = ValidatedInvoice(**response.extraction)
        print(f"Extracted and validated: {validated}")
        return validated
    except ValidationError as e:
        print(f"Extracted data validation failed: {e}")
        return None

def extract_from_url():
    """Extract data from remote document"""
    client = LandingAIADE()
    
    # Parse from URL
    parsed = client.parse(
        document_url="https://example.com/invoice.pdf"
    )
    
    # Define simple schema
    class SimpleInvoice(BaseModel):
        invoice_number: str
        total: float
    
    # Extract from URL's markdown
    response = client.extract(
        markdown=parsed.markdown,
        schema=json.dumps(SimpleInvoice.model_json_schema())
    )
    
    print(f"Extracted from URL: {response.extraction}")
    return response

def batch_extract_multiple_schemas():
    """Extract multiple schemas from same document"""
    client = LandingAIADE()
    parsed = client.parse(document=Path("complex_document.pdf"))
    
    # Define multiple schemas for different aspects
    schemas = {
        "header": {
            "document_title": "string",
            "document_date": "string",
            "document_id": "string"
        },
        "financial": {
            "total_amount": "number",
            "tax_amount": "number",
            "discount": "number"
        },
        "parties": {
            "vendor_name": "string",
            "customer_name": "string",
            "vendor_address": "string",
            "customer_address": "string"
        }
    }
    
    results = {}
    
    # Extract each schema
    for name, schema in schemas.items():
        response = client.extract(
            markdown=parsed.markdown,
            schema=json.dumps({"properties": schema, "type": "object"}),
            model="extract-latest"
        )
        results[name] = response.extraction
        print(f"\n{name.upper()} Data:")
        for key, value in response.extraction.items():
            print(f"  {key}: {value}")
    
    return results

if __name__ == "__main__":
    # Run basic extraction example
    print("=== Basic Extraction ===")
    basic_extraction()
    
    # Uncomment to run other examples:
    # print("\n=== Extraction with Grounding ===")
    # extract_with_grounding_references()
    
    # print("\n=== Complex Structure Extraction ===")
    # extract_complex_structure()
    
    # print("\n=== Table-Specific Extraction ===")
    # extract_tables_specifically()
    
    # print("\n=== Validated Extraction ===")
    # validate_and_extract()
    
    # print("\n=== Batch Extraction ===")
    # batch_extract_multiple_schemas()