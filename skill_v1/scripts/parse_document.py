#!/usr/bin/env python3
"""
Document parsing examples using LandingAI ADE
"""

import os
import asyncio
from pathlib import Path
from landingai_ade import LandingAIADE, AsyncLandingAIADE
import time

def basic_parse():
    """Basic document parsing"""
    client = LandingAIADE()
    
    # Parse a local file
    response = client.parse(
        document=Path("invoice.pdf"),
        model="dpt-2-latest"
    )
    
    print(f"Document parsed successfully!")
    print(f"Pages: {response.metadata.page_count}")
    print(f"Chunks found: {len(response.chunks)}")
    print(f"Processing time: {response.metadata.duration_ms}ms")
    
    # Access markdown content
    print(f"\nFirst 500 characters of markdown:")
    print(response.markdown[:500])
    
    # Access chunks
    for i, chunk in enumerate(response.chunks[:3]):
        print(f"\nChunk {i}:")
        print(f"  Type: {chunk.type}")
        print(f"  Page: {chunk.grounding.page}")
        print(f"  Content preview: {chunk.markdown[:100]}...")
    
    return response

def parse_with_splitting():
    """Parse document with page splitting"""
    client = LandingAIADE()
    
    response = client.parse(
        document=Path("multi-page.pdf"),
        split="page",  # Split by pages
        save_to="./output"  # Save JSON output
    )
    
    print(f"Document split into {len(response.splits)} pages")
    
    # Access splits
    for split in response.splits:
        print(f"\n{split.class_}: {split.identifier}")
        print(f"  Pages: {split.pages}")
        print(f"  Chunks in split: {len(split.chunks)}")
        print(f"  Content preview: {split.markdown[:200]}...")
    
    return response

def parse_remote_document():
    """Parse document from URL"""
    client = LandingAIADE()
    
    response = client.parse(
        document_url="https://example.com/document.pdf",
        model="dpt-2-latest"
    )
    
    print(f"Remote document parsed: {response.metadata.filename}")
    return response

async def async_parse_multiple():
    """Parse multiple documents concurrently"""
    async with AsyncLandingAIADE() as client:
        files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
        
        # Create parse tasks
        tasks = [
            client.parse(document=Path(file))
            for file in files
        ]
        
        # Execute concurrently
        responses = await asyncio.gather(*tasks)
        
        for file, response in zip(files, responses):
            print(f"\n{file}:")
            print(f"  Pages: {response.metadata.page_count}")
            print(f"  Chunks: {len(response.chunks)}")
            print(f"  Processing time: {response.metadata.duration_ms}ms")
        
        return responses

def parse_large_file_with_jobs():
    """Use parse jobs for large files"""
    client = LandingAIADE()
    file_path = Path("large_document.pdf")
    
    # Check file size
    file_size = file_path.stat().st_size
    print(f"File size: {file_size / 1_000_000:.2f} MB")
    
    if file_size > 50_000_000:  # 50MB
        print("Using parse jobs for large file...")
        
        # Create job
        job = client.parse_jobs.create(
            document=file_path,
            model="dpt-2-latest",
            split="page"
        )
        
        print(f"Job created: {job.job_id}")
        
        # Monitor progress
        while True:
            status = client.parse_jobs.get(job.job_id)
            print(f"Status: {status.status}, Progress: {status.progress * 100:.1f}%")
            
            if status.status == "completed":
                print("Job completed successfully!")
                return status
            elif status.status == "failed":
                print(f"Job failed: {status.failure_reason}")
                return None
            
            time.sleep(5)  # Check every 5 seconds
    else:
        # Use regular parse for smaller files
        return client.parse(document=file_path)

def handle_parsing_errors():
    """Demonstrate error handling during parsing"""
    from landingai_ade.exceptions import (
        RateLimitError, 
        APITimeoutError,
        APIStatusError
    )
    
    client = LandingAIADE()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.parse(
                document=Path("document.pdf"),
                model="dpt-2-latest"
            )
            
            # Check for partial failures
            if response.metadata.get("failed_pages"):
                print(f"Warning: Failed pages: {response.metadata['failed_pages']}")
            
            return response
            
        except RateLimitError as e:
            print(f"Rate limit hit: {e}")
            wait_time = 2 ** attempt * 10  # Exponential backoff
            print(f"Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            
        except APITimeoutError as e:
            print(f"Request timeout: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")
                continue
            else:
                print("Using parse jobs for large file...")
                job = client.parse_jobs.create(document=Path("document.pdf"))
                return job
                
        except APIStatusError as e:
            print(f"API error {e.status_code}: {e.message}")
            raise
    
    raise Exception(f"Failed after {max_retries} attempts")

def save_parse_output():
    """Parse and save output for debugging"""
    client = LandingAIADE()
    
    response = client.parse(
        document=Path("document.pdf"),
        save_to="./parse_output"
    )
    
    print(f"Parse output saved to ./parse_output/{Path('document.pdf').stem}_parse_output.json")
    
    # Also save specific chunk types
    text_chunks = [c for c in response.chunks if c.type == "text"]
    table_chunks = [c for c in response.chunks if c.type == "table"]
    
    print(f"\nFound {len(text_chunks)} text chunks")
    print(f"Found {len(table_chunks)} table chunks")
    
    return response

if __name__ == "__main__":
    # Run basic parse example
    print("=== Basic Parse ===")
    basic_parse()
    
    # Uncomment to run other examples:
    # print("\n=== Parse with Splitting ===")
    # parse_with_splitting()
    
    # print("\n=== Async Parse Multiple ===")
    # asyncio.run(async_parse_multiple())
    
    # print("\n=== Parse Large File ===")
    # parse_large_file_with_jobs()
    
    # print("\n=== Error Handling ===")
    # handle_parsing_errors()
    
    # print("\n=== Save Output ===")
    # save_parse_output()