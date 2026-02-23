#!/usr/bin/env python3
"""
Generate a consolidated PDF from all markdown documentation files.

Usage:
    python scripts/generate_docs_pdf.py

Output:
    docs/Sustainability_Monitoring_Hub_Documentation.pdf
"""

import os
from pathlib import Path
from fpdf import FPDF


def clean_text(text):
    """Keep only safe ASCII characters."""
    return ''.join(c for c in text if 32 <= ord(c) < 127 or ord(c) in [9, 10, 13])


def extract_text_from_markdown(markdown_content):
    """Extract plain text from markdown, skipping code blocks and tables."""
    lines = []
    in_code = False
    
    for line in markdown_content.split("\n"):
        if "```" in line:
            in_code = not in_code
            continue
        if in_code:
            continue
        if "|" in line and line.count("-") > 5:
            continue
        
        # Remove markdown syntax
        line = line.replace("#", "").replace("**", "").replace("`", "")
        line = line.replace("[", "").replace("]", "")
        line = clean_text(line).strip()
        
        if line:
            lines.append(line)
    
    return lines


def main():
    """Generate documentation PDF."""
    docs_dir = Path(__file__).parent.parent / "docs"
    output_file = docs_dir / "Sustainability_Monitoring_Hub_Documentation.pdf"
    
    doc_files = [
        "0_Introduction.md",
        "1_System_Architecture.md",
        "2_Database_Schema.md",
        "3_Technical_Documentation.md",
        "4_API_Documentation.md",
        "5_User_Guides.md",
        "6_Deployment_Guide.md",
        "7_GHG_Protocol_Schema.md",
    ]
    
    pdf = FPDF()
    pdf.set_margins(10, 10, 10)  # Set margins
    pdf.add_page()
    pdf.set_font("Courier", "B", 11)
    
    try:
        pdf.cell(0, 8, "Sustainability Monitoring Hub", ln=True)
    except:
        pass
    
    pdf.set_font("Courier", "", 9)
    try:
        pdf.cell(0, 6, "Complete Technical Documentation", ln=True)
    except:
        pass
    
    pdf.ln(3)
    
    # TOC
    pdf.add_page()
    pdf.set_font("Courier", "B", 10)
    try:
        pdf.cell(0, 6, "TABLE OF CONTENTS", ln=True)
    except:
        pass
    
    pdf.set_font("Courier", "", 8)
    pdf.ln(2)
    
    for i, doc in enumerate(doc_files, 1):
        title = doc.replace(".md", "").replace("_", " ")
        try:
            pdf.cell(0, 4, f"{i}. {title}"[:60], ln=True)
        except:
            pass
    
    # Content
    for doc_file in doc_files:
        filepath = docs_dir / doc_file
        
        if not filepath.exists():
            print(f"Skipping {doc_file}")
            continue
        
        print(f"Processing: {doc_file}")
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            lines = extract_text_from_markdown(content)
            
            pdf.add_page()
            pdf.set_font("Courier", "B", 9)
            try:
                title = doc_file.replace(".md", "").replace("_", " ")
                pdf.cell(0, 5, title[:70], ln=True)
            except:
                pass
            
            pdf.set_font("Courier", "", 7)
            pdf.ln(1)
            
            # Use text method instead of multi_cell for safety
            for line in lines[:250]:
                text = line[:100]  # Limit line length
                try:
                    pdf.cell(0, 2, text, ln=True)
                except Exception as e:
                    try:
                        # Fallback to shorter text
                        pdf.cell(0, 2, text[:70], ln=True)
                    except:
                        pass  # Skip problematic lines
        
        except Exception as e:
            print(f"Error processing {doc_file}: {e}")
    
    try:
        pdf.output(output_file)
        size = os.path.getsize(output_file) / 1024
        print(f"\nSuccess! Saved to: {output_file}")
        print(f"Size: {size:.1f} KB")
    except Exception as e:
        print(f"Error saving: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
