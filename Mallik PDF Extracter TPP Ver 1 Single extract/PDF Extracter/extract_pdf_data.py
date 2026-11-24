"""
extract_pdf_data.py
-------------------
Standalone extractor and parser for Laser-Cut Setup Plan PDFs (e.g. TRUMPF setup plans).
Extracts 8 key fields and formats them to match the exact regex expectations of the VB.NET client.
"""
from __future__ import annotations

import sys
import argparse
import re
from pathlib import Path
from typing import Dict, Any
import pdfplumber


def extract_all(pdf_path: str | Path) -> Dict[str, str]:
    """
    Extract 8 specific fields from a TRUMPF Setup Plan PDF.
    
    Fields extracted:
      - Machine Name (TextBox21)
      - Material Name (TextBox16)
      - Thickness (TextBox22)
      - Raw Material Weight (TextBox24)
      - Process Length (TextBox25)
      - Laser Material Name (TextBox27)
      - Material Size (TextBox18)
      - Process Quantity (TextBox26)
    """
    pdf_path = Path(pdf_path)
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"

    fields: Dict[str, str] = {}

    # 1. Machine Name (TextBox21)
    # Handles "Workplace: TruLaser_1030_L94_6KW Target..." or "Machine TruLaser 1030 L94 6KW"
    m_machine = re.search(r"(?:Machine|Workplace):?\s*([^\r\n]+?)(?=\s+Target|\s+Number|\r|\n|$)", text, re.IGNORECASE)
    if m_machine:
        raw_machine = m_machine.group(1).strip()
        fields["Machine Name (TextBox21)"] = raw_machine.replace(" ", "_")
    else:
        fields["Machine Name (TextBox21)"] = ""

    # 2. Material Name (TextBox16)
    # Handles "Material:\nHR" or "Material HR"
    m_mat = re.search(r"^Material:?\s*\n?\s*([A-Za-z0-9_\-]+)", text, re.MULTILINE | re.IGNORECASE)
    if m_mat:
        fields["Material Name (TextBox16)"] = m_mat.group(1).strip()
    else:
        fields["Material Name (TextBox16)"] = ""

    # 3. Laser Material Name (TextBox27)
    # Handles "Raw material:\nHRAM0600---" or "Laser material name HRAM0600---"
    m_laser_mat = re.search(r"(?:Laser material name|Raw material):?\s*\n?\s*([A-Za-z0-9_\-]+)", text, re.IGNORECASE)
    if m_laser_mat:
        fields["Laser Material Name (TextBox27)"] = m_laser_mat.group(1).strip()
    else:
        fields["Laser Material Name (TextBox27)"] = ""

    # 4. Material Size (TextBox18)
    # Handles "Dimensions:\n2500.00 x 1250.00 x 6.00 mm" or "Material size 2500.00 x 1250.00 x 6.00 mm"
    m_size = re.search(r"(?:Material size|Dimensions):?\s*\n?\s*([\d\.\s]+x[\d\.\s]+x[\d\.\s]+mm)", text, re.IGNORECASE)
    if m_size:
        fields["Material Size (TextBox18)"] = m_size.group(1).strip()
    else:
        fields["Material Size (TextBox18)"] = ""

    # 5. Thickness (TextBox22)
    # Handles "Thickness 6.00 mm" or derived from "2500.00 x 1250.00 x 6.00 mm"
    m_thick = re.search(r"Thickness\s+([\d\.]+)\s*mm", text, re.IGNORECASE)
    if m_thick:
        fields["Thickness (TextBox22)"] = m_thick.group(1).strip()
    elif fields["Material Size (TextBox18)"]:
        parts = fields["Material Size (TextBox18)"].replace("mm", "").split("x")
        if len(parts) >= 3:
            fields["Thickness (TextBox22)"] = parts[2].strip()
        else:
            fields["Thickness (TextBox22)"] = ""
    else:
        fields["Thickness (TextBox22)"] = ""

    # 6. Raw Material Weight (TextBox24)
    # Handles "Production package weight:\n147.19 kg" or "Raw material weight 147.19 kg"
    m_weight = re.search(r"(?:Raw material weight|Production package weight):?\s*\n?\s*([\d\.]+)\s*kg", text, re.IGNORECASE)
    if m_weight:
        fields["Raw Material Weight (TextBox24)"] = m_weight.group(1).strip()
    else:
        fields["Raw Material Weight (TextBox24)"] = ""

    # 7. Process Length (TextBox25)
    # Handles "Cutting length:\n50631.54 mm" or "Process length 50631.54 mm"
    m_length = re.search(r"(?:Process length|Cutting length):?\s*\n?\s*([\d\.]+)\s*mm", text, re.IGNORECASE)
    if m_length:
        fields["Process Length (TextBox25)"] = m_length.group(1).strip()
    else:
        fields["Process Length (TextBox25)"] = ""

    # 8. Process Quantity (TextBox26)
    # Handles "Rpt:\n5" or "Process quantity 5"
    m_qty = re.search(r"(?:Process quantity|Rpt):?\s*\n?\s*(\d+)", text, re.IGNORECASE)
    if m_qty:
        fields["Process Quantity (TextBox26)"] = m_qty.group(1).strip()
    else:
        fields["Process Quantity (TextBox26)"] = ""

    return fields


def build_csv(fields: Dict[str, str]) -> str:
    """
    Format extracted fields into the exact string format expected by VB.NET regexes:
        Machine Name <value>,
        Material Name <value>
        Laser Material Name <value>,
        Material Size <value>
        Thickness <value>
        Raw Material Weight <value>
        Process Length <value>
        Process Quantity <value>
    """
    return (
        f"Machine Name {fields.get('Machine Name (TextBox21)', '')},\n"
        f"Material Name {fields.get('Material Name (TextBox16)', '')}\n"
        f"Laser Material Name {fields.get('Laser Material Name (TextBox27)', '')},\n"
        f"Material Size {fields.get('Material Size (TextBox18)', '')}\n"
        f"Thickness {fields.get('Thickness (TextBox22)', '')}\n"
        f"Raw Material Weight {fields.get('Raw Material Weight (TextBox24)', '')}\n"
        f"Process Length {fields.get('Process Length (TextBox25)', '')}\n"
        f"Process Quantity {fields.get('Process Quantity (TextBox26)', '')}"
    )


def simulate_vbnet_extraction(csv_data: str) -> Dict[str, str]:
    """
    Simulate the exact VB.NET application client regex extraction logic.
    """
    def ExtractWord(data: str, pattern: str) -> str:
        m = re.search(pattern, data)
        if m:
            return m.group(1).split(" ")[0]
        return ""

    def ExtractWordmaterialSize(data: str, pattern: str) -> str:
        m = re.search(pattern, data, re.MULTILINE)
        if m:
            res = m.group(1)
            res = re.sub(r"Thickness.*", "", res).strip()
            return res
        return ""

    def ExtractWordProcessQty(data: str, pattern: str) -> str:
        m = re.search(pattern, data)
        if m:
            num = m.group(1)
            fw = num.split(" ")[0]
            try:
                return str(int(fw.split(".")[0]))
            except Exception:
                return ""
        return ""

    return {
        "Machine Name (TextBox21)": ExtractWord(csv_data, r"Machine Name\s*(.*),"),
        "Material Name (TextBox16)": ExtractWord(csv_data, r"Material Name\s*(.*)"),
        "Thickness (TextBox22)": ExtractWord(csv_data, r"Thickness\s*(.*)"),
        "Raw Material Weight (TextBox24)": ExtractWord(csv_data, r"Raw Material Weight\s*(.*)"),
        "Laser Material Name (TextBox27)": ExtractWord(csv_data, r"Laser Material Name\s*(.*),"),
        "Process Length (TextBox25)": ExtractWord(csv_data, r"Process Length\s*(.*)"),
        "Material Size (TextBox18)": ExtractWordmaterialSize(csv_data, r"Material Size\s*(.*?)$"),
        "Process Quantity (TextBox26)": ExtractWordProcessQty(csv_data, r"Process Quantity\s*(\d+(\.\d+)?)"),
    }


def main():
    parser = argparse.ArgumentParser(description="Extract setup plan data from PDF")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--out", "-o", help="Output text path", default=None)
    args = parser.parse_args()

    fields = extract_all(args.pdf)
    csv_str = build_csv(fields)

    print("Extracted fields:")
    for k, v in fields.items():
        print(f"  {k:34s} = {v}")

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(csv_str, encoding="utf-8")
        print(f"\nWrote CSV output to {out_path.resolve()}")


if __name__ == "__main__":
    main()
