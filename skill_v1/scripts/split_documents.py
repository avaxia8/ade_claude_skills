#!/usr/bin/env python3
"""
Document splitting and classification examples using LandingAI ADE
"""

from pathlib import Path
from landingai_ade import LandingAIADE
import json

def basic_split():
    """Basic document splitting by type"""
    client = LandingAIADE()
    
    # First parse the mixed document
    parsed = client.parse(document=Path("mixed_documents.pdf"))
    
    # Define document types to classify
    split_classes = [
        {
            "name": "Invoice",
            "description": "Sales invoice or billing document",
            "identifier": "Invoice Date"  # Key field to group by
        },
        {
            "name": "Receipt",
            "description": "Payment receipt or confirmation",
            "identifier": "Receipt Number"
        },
        {
            "name": "Purchase Order",
            "description": "Purchase order document",
            "identifier": "PO Number"
        }
    ]
    
    # Split the document
    response = client.split(
        markdown=parsed.markdown,
        split_class=split_classes,
        model="split-latest"
    )
    
    print(f"Document split into {len(response.splits)} sections")
    
    # Process splits
    for split in response.splits:
        print(f"\n{split.classification}:")
        print(f"  Identifier: {split.identifier}")
        print(f"  Pages: {split.pages}")
        print(f"  Content length: {len(split.markdowns[0])} chars")
        print(f"  Preview: {split.markdowns[0][:200]}...")
        
        # Save each split to separate file
        filename = f"{split.classification}_{split.identifier}.md".replace(" ", "_").replace("/", "-")
        with open(filename, "w") as f:
            f.write("\n".join(split.markdowns))
        print(f"  Saved to: {filename}")
    
    return response

def split_financial_documents():
    """Split complex financial documents"""
    client = LandingAIADE()
    
    parsed = client.parse(document=Path("financial_package.pdf"))
    
    # Define financial document types
    split_classes = [
        {
            "name": "Balance Sheet",
            "description": "Statement of financial position showing assets, liabilities, and equity",
            "identifier": "As of Date"
        },
        {
            "name": "Income Statement",
            "description": "Profit and loss statement showing revenue and expenses",
            "identifier": "Period Ending"
        },
        {
            "name": "Cash Flow Statement",
            "description": "Statement showing cash inflows and outflows",
            "identifier": "Period"
        },
        {
            "name": "Notes",
            "description": "Explanatory notes to financial statements",
            "identifier": "Note Number"
        }
    ]
    
    response = client.split(
        markdown=parsed.markdown,
        split_class=split_classes,
        model="split-latest"
    )
    
    # Organize by document type
    organized = {}
    for split in response.splits:
        doc_type = split.classification
        if doc_type not in organized:
            organized[doc_type] = []
        organized[doc_type].append(split)
    
    print("Financial Document Organization:")
    for doc_type, splits in organized.items():
        print(f"\n{doc_type}: {len(splits)} document(s)")
        for split in splits:
            print(f"  - {split.identifier} (Pages: {split.pages})")
    
    return response

def split_legal_documents():
    """Split legal document packages"""
    client = LandingAIADE()
    
    parsed = client.parse(document=Path("legal_package.pdf"))
    
    split_classes = [
        {
            "name": "Contract",
            "description": "Legal contract or agreement",
            "identifier": "Contract Number"
        },
        {
            "name": "Amendment",
            "description": "Contract amendment or addendum",
            "identifier": "Amendment Number"
        },
        {
            "name": "Exhibit",
            "description": "Contract exhibit or attachment",
            "identifier": "Exhibit Letter"
        },
        {
            "name": "Certificate",
            "description": "Legal certificate or attestation",
            "identifier": "Certificate Type"
        }
    ]
    
    response = client.split(
        markdown=parsed.markdown,
        split_class=split_classes
    )
    
    # Create hierarchy
    print("Legal Document Structure:")
    
    contracts = [s for s in response.splits if s.classification == "Contract"]
    for contract in contracts:
        print(f"\n{contract.classification}: {contract.identifier}")
        
        # Find related amendments
        amendments = [s for s in response.splits 
                      if s.classification == "Amendment" 
                      and contract.identifier in str(s.markdowns)]
        for amendment in amendments:
            print(f"  └─ {amendment.classification}: {amendment.identifier}")
        
        # Find related exhibits
        exhibits = [s for s in response.splits 
                   if s.classification == "Exhibit"
                   and contract.identifier in str(s.markdowns)]
        for exhibit in exhibits:
            print(f"  └─ {exhibit.classification}: {exhibit.identifier}")
    
    return response

def split_medical_records():
    """Split medical record packages"""
    client = LandingAIADE()
    
    parsed = client.parse(document=Path("medical_records.pdf"))
    
    split_classes = [
        {
            "name": "Patient Information",
            "description": "Patient demographic and contact information",
            "identifier": "Patient ID"
        },
        {
            "name": "Medical History",
            "description": "Past medical history and conditions",
            "identifier": "Date"
        },
        {
            "name": "Lab Results",
            "description": "Laboratory test results",
            "identifier": "Test Date"
        },
        {
            "name": "Prescription",
            "description": "Medication prescriptions",
            "identifier": "Rx Number"
        },
        {
            "name": "Imaging Report",
            "description": "X-ray, MRI, or other imaging reports",
            "identifier": "Study Date"
        }
    ]
    
    response = client.split(
        markdown=parsed.markdown,
        split_class=split_classes
    )
    
    # Group by patient if multiple patients
    patients = {}
    for split in response.splits:
        # Try to extract patient ID from content
        patient_id = split.identifier if "Patient" in split.classification else "Unknown"
        
        if patient_id not in patients:
            patients[patient_id] = []
        patients[patient_id].append(split)
    
    print("Medical Records Organization:")
    for patient_id, records in patients.items():
        print(f"\nPatient: {patient_id}")
        for record in records:
            print(f"  - {record.classification}: {record.identifier}")
    
    return response

def split_with_custom_identifiers():
    """Use custom identifiers for grouping"""
    client = LandingAIADE()
    
    parsed = client.parse(document=Path("correspondence.pdf"))
    
    # Use identifiers to group related documents
    split_classes = [
        {
            "name": "Email",
            "identifier": "Thread ID"  # Group by email thread
        },
        {
            "name": "Letter",
            "identifier": "Reference Number"  # Group by reference
        },
        {
            "name": "Memo",
            "identifier": "Department"  # Group by department
        }
    ]
    
    response = client.split(
        markdown=parsed.markdown,
        split_class=split_classes
    )
    
    # Group by identifier
    groups = {}
    for split in response.splits:
        key = f"{split.classification}-{split.identifier}"
        if key not in groups:
            groups[key] = []
        groups[key].append(split)
    
    print("Document Groups:")
    for key, splits in groups.items():
        print(f"\n{key}:")
        print(f"  Documents: {len(splits)}")
        print(f"  Total pages: {sum(len(s.pages) for s in splits)}")
    
    return response

def split_and_extract():
    """Split documents then extract data from each split"""
    client = LandingAIADE()
    
    # Parse mixed document
    parsed = client.parse(document=Path("mixed_invoices.pdf"))
    
    # Split by document type
    split_response = client.split(
        markdown=parsed.markdown,
        split_class=[
            {"name": "Invoice", "identifier": "Invoice Number"},
            {"name": "Credit Note", "identifier": "Credit Note Number"}
        ]
    )
    
    # Extract data from each split
    from pydantic import BaseModel, Field
    
    class InvoiceData(BaseModel):
        document_number: str = Field(description="Invoice or credit note number")
        amount: float = Field(description="Total amount")
        date: str = Field(description="Document date")
    
    results = []
    for split in split_response.splits:
        print(f"\nProcessing {split.classification}: {split.identifier}")
        
        # Extract data from this split's markdown
        extract_response = client.extract(
            markdown=split.markdowns[0],  # Use first markdown
            schema=json.dumps(InvoiceData.model_json_schema()),
            model="extract-latest"
        )
        
        data = extract_response.extraction
        data['document_type'] = split.classification
        results.append(data)
        
        print(f"  Number: {data.get('document_number')}")
        print(f"  Amount: ${data.get('amount')}")
        print(f"  Date: {data.get('date')}")
    
    return results

def handle_split_errors():
    """Handle errors during splitting"""
    client = LandingAIADE()
    
    try:
        parsed = client.parse(document=Path("document.pdf"))
        
        # Try splitting with detailed error handling
        response = client.split(
            markdown=parsed.markdown,
            split_class=[
                {"name": "Type1"},
                {"name": "Type2"}
            ]
        )
        
        # Check if any splits were found
        if not response.splits:
            print("Warning: No document splits found")
            print("The document might not match any of the specified types")
            return None
        
        # Check for unclassified content
        total_pages = set(range(parsed.metadata.page_count))
        classified_pages = set()
        for split in response.splits:
            classified_pages.update(split.pages)
        
        unclassified = total_pages - classified_pages
        if unclassified:
            print(f"Warning: Pages {unclassified} were not classified")
        
        return response
        
    except Exception as e:
        print(f"Split error: {e}")
        print("Falling back to page-based splitting")
        
        # Fallback to simple page splitting
        response = client.parse(
            document=Path("document.pdf"),
            split="page"
        )
        return response

if __name__ == "__main__":
    # Run basic split example
    print("=== Basic Document Splitting ===")
    basic_split()
    
    # Uncomment to run other examples:
    # print("\n=== Financial Documents ===")
    # split_financial_documents()
    
    # print("\n=== Legal Documents ===")
    # split_legal_documents()
    
    # print("\n=== Medical Records ===")
    # split_medical_records()
    
    # print("\n=== Custom Identifiers ===")
    # split_with_custom_identifiers()
    
    # print("\n=== Split and Extract ===")
    # split_and_extract()
    
    # print("\n=== Error Handling ===")
    # handle_split_errors()