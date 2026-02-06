#!/usr/bin/env python3
"""
Visualization examples for LandingAI ADE parsed documents
"""

from pathlib import Path
from landingai_ade import LandingAIADE
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF for PDF rendering
from datetime import datetime
import os

# Define colors for different chunk/grounding types
GROUNDING_TYPE_COLORS = {
    "chunkText": (40, 167, 69),       # Green
    "chunkTable": (0, 123, 255),      # Blue
    "chunkMarginalia": (111, 66, 193), # Purple
    "chunkFigure": (255, 0, 255),     # Magenta
    "chunkLogo": (144, 238, 144),     # Light Green
    "chunkCard": (255, 165, 0),       # Orange
    "chunkAttestation": (0, 255, 255), # Cyan
    "chunkScanCode": (255, 193, 7),   # Yellow
    "chunkForm": (220, 20, 60),       # Red
    "tableCell": (173, 216, 230),     # Light Blue
    "table": (70, 130, 180)           # Steel Blue
}

def visualize_all_chunks():
    """Draw bounding boxes for all chunks on document pages"""
    client = LandingAIADE()
    
    # Parse document
    document_path = "document.pdf"
    response = client.parse(document=Path(document_path))
    
    print(f"Visualizing {len(response.chunks)} chunks across {response.metadata.page_count} pages")
    
    # Open PDF
    pdf_document = fitz.open(document_path)
    
    for page_num in range(response.metadata.page_count):
        # Render page to image (2x scale for better quality)
        page = pdf_document[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Draw bounding boxes for chunks on this page
        chunks_on_page = 0
        for chunk in response.chunks:
            if chunk.grounding.page != page_num:
                continue
            
            chunks_on_page += 1
            
            # Convert normalized coordinates to pixels
            box = chunk.grounding.box
            x1 = int(box.left * img.width)
            y1 = int(box.top * img.height)
            x2 = int(box.right * img.width)
            y2 = int(box.bottom * img.height)
            
            # Get color based on chunk type (with "chunk" prefix for grounding)
            grounding_type = f"chunk{chunk.type.capitalize()}"
            color = GROUNDING_TYPE_COLORS.get(grounding_type, (128, 128, 128))
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # Add label with chunk type and ID
            label = f"{chunk.type}:{chunk.id[:8]}"
            label_height = 20
            draw.rectangle([x1, y1-label_height, x1 + len(label) * 8, y1], 
                          fill=color)
            draw.text((x1 + 2, y1-label_height + 2), label, fill=(255, 255, 255))
        
        # Save annotated page
        output_file = f"page_{page_num}_annotated.png"
        img.save(output_file)
        print(f"Page {page_num}: {chunks_on_page} chunks -> {output_file}")
    
    pdf_document.close()

def visualize_grounding_details():
    """Visualize all grounding information including tables and cells"""
    client = LandingAIADE()
    
    document_path = "document.pdf"
    response = client.parse(document=Path(document_path))
    
    print(f"Visualizing {len(response.grounding)} grounding entries")
    
    # Count grounding types
    grounding_types = {}
    for gid, grounding in response.grounding.items():
        gtype = grounding.type
        grounding_types[gtype] = grounding_types.get(gtype, 0) + 1
    
    print("Grounding types found:")
    for gtype, count in grounding_types.items():
        print(f"  {gtype}: {count}")
    
    # Open PDF
    pdf_document = fitz.open(document_path)
    
    for page_num in range(response.metadata.page_count):
        page = pdf_document[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)
        
        # Draw all groundings on this page
        for gid, grounding in response.grounding.items():
            if grounding.page != page_num:
                continue
            
            # Convert coordinates
            box = grounding.box
            x1 = int(box.left * img.width)
            y1 = int(box.top * img.height)
            x2 = int(box.right * img.width)
            y2 = int(box.bottom * img.height)
            
            # Get color based on grounding type
            color = GROUNDING_TYPE_COLORS.get(grounding.type, (128, 128, 128))
            
            # Different line styles for different types
            if grounding.type == "tableCell":
                # Dotted line for cells
                draw.rectangle([x1, y1, x2, y2], outline=color, width=1)
            elif grounding.type == "table":
                # Thick line for tables
                draw.rectangle([x1, y1, x2, y2], outline=color, width=4)
            else:
                # Normal line for chunks
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Add label for non-cell groundings
            if grounding.type != "tableCell":
                label = f"{grounding.type}:{gid[:8]}"
                draw.text((x1, y1-20), label, fill=color)
        
        # Save detailed visualization
        output_file = f"page_{page_num}_grounding_details.png"
        img.save(output_file)
        print(f"Page {page_num} grounding details -> {output_file}")
    
    pdf_document.close()

def save_individual_chunks():
    """Extract and save each chunk as a separate image"""
    client = LandingAIADE()
    
    document_path = "document.pdf"
    response = client.parse(document=Path(document_path))
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"groundings/document_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Saving chunks to {output_dir}")
    
    # Open document
    if document_path.endswith('.pdf'):
        pdf_document = fitz.open(document_path)
        
        for chunk in response.chunks:
            # Get page
            page = pdf_document[chunk.grounding.page]
            mat = fitz.Matrix(2, 2)  # 2x scale for better quality
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Crop to chunk bounds
            box = chunk.grounding.box
            x1 = int(box.left * img.width)
            y1 = int(box.top * img.height)
            x2 = int(box.right * img.width)
            y2 = int(box.bottom * img.height)
            
            chunk_img = img.crop((x1, y1, x2, y2))
            
            # Create page subdirectory
            page_dir = f"{output_dir}/page_{chunk.grounding.page}"
            os.makedirs(page_dir, exist_ok=True)
            
            # Save with descriptive filename
            filename = f"{page_dir}/{chunk.type}.{chunk.id}.png"
            chunk_img.save(filename)
            print(f"  Saved: {filename} ({chunk_img.width}x{chunk_img.height})")
        
        pdf_document.close()
    else:
        # Handle image files
        img = Image.open(document_path)
        
        for chunk in response.chunks:
            box = chunk.grounding.box
            x1 = int(box.left * img.width)
            y1 = int(box.top * img.height)
            x2 = int(box.right * img.width)
            y2 = int(box.bottom * img.height)
            
            chunk_img = img.crop((x1, y1, x2, y2))
            
            page_dir = f"{output_dir}/page_{chunk.grounding.page}"
            os.makedirs(page_dir, exist_ok=True)
            
            filename = f"{page_dir}/{chunk.type}.{chunk.id}.png"
            chunk_img.save(filename)
            print(f"  Saved: {filename}")
    
    print(f"Total chunks saved: {len(response.chunks)}")

def visualize_tables_and_cells():
    """Specifically visualize table structures and cells"""
    client = LandingAIADE()
    
    document_path = "document_with_tables.pdf"
    response = client.parse(document=Path(document_path))
    
    # Find table-related groundings
    tables = {}
    cells = {}
    
    for gid, grounding in response.grounding.items():
        if grounding.type == "table":
            tables[gid] = grounding
        elif grounding.type == "tableCell":
            cells[gid] = grounding
    
    print(f"Found {len(tables)} tables and {len(cells)} cells")
    
    # Open PDF
    pdf_document = fitz.open(document_path)
    
    for page_num in range(response.metadata.page_count):
        page = pdf_document[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)
        
        # Draw tables first (thicker lines)
        for tid, table in tables.items():
            if table.page != page_num:
                continue
            
            box = table.box
            x1 = int(box.left * img.width)
            y1 = int(box.top * img.height)
            x2 = int(box.right * img.width)
            y2 = int(box.bottom * img.height)
            
            # Draw table outline
            draw.rectangle([x1, y1, x2, y2], 
                          outline=GROUNDING_TYPE_COLORS["table"], 
                          width=4)
            
            # Add table label
            draw.text((x1, y1-25), f"Table: {tid}", 
                     fill=GROUNDING_TYPE_COLORS["table"])
        
        # Draw cells (thinner lines)
        for cid, cell in cells.items():
            if cell.page != page_num:
                continue
            
            box = cell.box
            x1 = int(box.left * img.width)
            y1 = int(box.top * img.height)
            x2 = int(box.right * img.width)
            y2 = int(box.bottom * img.height)
            
            # Draw cell outline
            draw.rectangle([x1, y1, x2, y2], 
                          outline=GROUNDING_TYPE_COLORS["tableCell"], 
                          width=1)
            
            # Add position info if available
            if hasattr(cell, 'position'):
                pos = cell.position
                label = f"R{pos.row}C{pos.col}"
                if pos.rowspan > 1 or pos.colspan > 1:
                    label += f" ({pos.rowspan}x{pos.colspan})"
                draw.text((x1+2, y1+2), label, 
                         fill=GROUNDING_TYPE_COLORS["tableCell"])
        
        # Save table visualization
        output_file = f"page_{page_num}_tables.png"
        img.save(output_file)
        print(f"Page {page_num} tables -> {output_file}")
    
    pdf_document.close()

def create_chunk_type_legend():
    """Create a legend showing all chunk/grounding types and their colors"""
    # Create legend image
    img_width = 400
    img_height = len(GROUNDING_TYPE_COLORS) * 40 + 60
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.text((10, 10), "ADE Grounding Type Colors", fill='black')
    
    # Draw each type with its color
    y_offset = 40
    for gtype, color in GROUNDING_TYPE_COLORS.items():
        # Color box
        draw.rectangle([10, y_offset, 40, y_offset + 25], 
                      fill=color, outline='black')
        
        # Type name
        draw.text((50, y_offset + 5), gtype, fill='black')
        
        y_offset += 35
    
    # Save legend
    img.save("chunk_type_legend.png")
    print("Created chunk_type_legend.png")

def visualize_specific_types():
    """Visualize only specific chunk types"""
    client = LandingAIADE()
    
    document_path = "document.pdf"
    response = client.parse(document=Path(document_path))
    
    # Types to visualize
    target_types = ["table", "figure"]
    
    print(f"Visualizing only: {target_types}")
    
    # Filter chunks
    filtered_chunks = [c for c in response.chunks if c.type in target_types]
    print(f"Found {len(filtered_chunks)} chunks of target types")
    
    # Open PDF
    pdf_document = fitz.open(document_path)
    
    for page_num in range(response.metadata.page_count):
        page = pdf_document[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)
        
        # Draw only filtered chunks
        for chunk in filtered_chunks:
            if chunk.grounding.page != page_num:
                continue
            
            box = chunk.grounding.box
            x1 = int(box.left * img.width)
            y1 = int(box.top * img.height)
            x2 = int(box.right * img.width)
            y2 = int(box.bottom * img.height)
            
            # Get color
            grounding_type = f"chunk{chunk.type.capitalize()}"
            color = GROUNDING_TYPE_COLORS.get(grounding_type, (255, 0, 0))
            
            # Draw with thicker line for emphasis
            draw.rectangle([x1, y1, x2, y2], outline=color, width=5)
            
            # Add label
            label = f"{chunk.type.upper()}"
            draw.rectangle([x1, y1-30, x1 + len(label) * 12, y1], fill=color)
            draw.text((x1 + 2, y1-28), label, fill=(255, 255, 255))
        
        # Save filtered visualization
        output_file = f"page_{page_num}_{'_'.join(target_types)}.png"
        img.save(output_file)
        print(f"Page {page_num} filtered -> {output_file}")
    
    pdf_document.close()

def create_chunk_summary_image():
    """Create a summary image showing chunk distribution"""
    client = LandingAIADE()
    
    response = client.parse(document=Path("document.pdf"))
    
    # Count chunk types
    chunk_counts = {}
    for chunk in response.chunks:
        chunk_type = chunk.type
        chunk_counts[chunk_type] = chunk_counts.get(chunk_type, 0) + 1
    
    # Create summary image
    img_width = 600
    bar_height = 30
    img_height = len(chunk_counts) * (bar_height + 10) + 100
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Title
    draw.text((10, 10), f"Document Chunk Analysis", fill='black')
    draw.text((10, 30), f"Total chunks: {len(response.chunks)}", fill='gray')
    draw.text((10, 50), f"Pages: {response.metadata.page_count}", fill='gray')
    
    # Draw bars
    y_offset = 80
    max_count = max(chunk_counts.values())
    
    for chunk_type, count in sorted(chunk_counts.items(), 
                                   key=lambda x: x[1], reverse=True):
        # Calculate bar width
        bar_width = int((count / max_count) * 400)
        
        # Get color
        grounding_type = f"chunk{chunk_type.capitalize()}"
        color = GROUNDING_TYPE_COLORS.get(grounding_type, (128, 128, 128))
        
        # Draw bar
        draw.rectangle([10, y_offset, 10 + bar_width, y_offset + bar_height],
                      fill=color, outline='black')
        
        # Add label
        label = f"{chunk_type}: {count}"
        draw.text((20 + bar_width, y_offset + 5), label, fill='black')
        
        y_offset += bar_height + 10
    
    # Save summary
    img.save("chunk_summary.png")
    print("Created chunk_summary.png")

if __name__ == "__main__":
    # Run visualization examples
    print("=== Visualize All Chunks ===")
    visualize_all_chunks()
    
    # Uncomment to run other examples:
    # print("\n=== Grounding Details ===")
    # visualize_grounding_details()
    
    # print("\n=== Save Individual Chunks ===")
    # save_individual_chunks()
    
    # print("\n=== Visualize Tables ===")
    # visualize_tables_and_cells()
    
    # print("\n=== Create Legend ===")
    # create_chunk_type_legend()
    
    # print("\n=== Visualize Specific Types ===")
    # visualize_specific_types()
    
    # print("\n=== Create Summary ===")
    # create_chunk_summary_image()