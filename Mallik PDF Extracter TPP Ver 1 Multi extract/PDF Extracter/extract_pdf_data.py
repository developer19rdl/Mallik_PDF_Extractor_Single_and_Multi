"""
extract_pdf_data.py
-------------------
Standalone extractor and parser for Laser-Cut Setup Plan PDFs (e.g. TRUMPF setup plans).
Supports both single-program plans and multi-program / multi-sheet plans.
Extracts 8 key fields per NC program and formats them for the VB.NET client.
"""
from __future__ import annotations

import sys
import argparse
import re
import json
from pathlib import Path
from typing import Dict, Any, List
import pdfplumber


def _parse_program_block(block_text: str, default_machine: str = "") -> Dict[str, str]:
    """Parse the 8 setup fields from a single program's section/page."""
    fields: Dict[str, str] = {}

    # 1. Program Name (Main program)
    m_prog = re.search(r"Main program:?\s*\n?\s*([A-Za-z0-9_\-]+)", block_text, re.IGNORECASE)
    prog_name = m_prog.group(1).strip() if m_prog else ""
    fields["Program Name"] = prog_name

    # 2. Machine Name (TextBox21)
    m_machine = re.search(r"(?:Machine|Workplace):?\s*([^\r\n]+?)(?=\s+Target|\s+Number|\r|\n|$)", block_text, re.IGNORECASE)
    if m_machine:
        machine = m_machine.group(1).strip().replace(" ", "_")
    else:
        machine = default_machine
    fields["Machine Name"] = machine
    fields["Machine Name (TextBox21)"] = machine

    # 3. Material Name (TextBox16)
    m_mat = re.search(r"^Material:?\s*\n?\s*([A-Za-z0-9_\-]+)", block_text, re.MULTILINE | re.IGNORECASE)
    if not m_mat:
        m_mat = re.search(r"Material:?\s*\n?\s*([A-Za-z0-9_\-]+)", block_text, re.IGNORECASE)
    mat = m_mat.group(1).strip() if m_mat else ""
    # Guard against accidentally matching the next section header if Material is blank in PDF
    if mat.lower() in ("raw", "production", "dimensions", "minimum", "thickness", "rpt", "main", "cutting", "duration"):
        mat = ""
    fields["Material Name"] = mat
    fields["Material Name (TextBox16)"] = mat
    fields["is_material_blank"] = (mat == "")

    # 4. Laser Material Name (TextBox27)
    m_laser = re.search(r"(?:Laser material name|Raw material):?\s*\n?\s*([A-Za-z0-9_\-]+)", block_text, re.IGNORECASE)
    laser_mat = m_laser.group(1).strip() if m_laser else ""
    # Guard against next section header
    if laser_mat.lower() in ("production", "dimensions", "minimum", "thickness", "cutting", "duration", "material"):
        laser_mat = ""
    fields["Laser Material Name"] = laser_mat
    fields["Laser Material Name (TextBox27)"] = laser_mat

    # 5. Material Size (TextBox18)
    m_size = re.search(r"(?:Material size|Dimensions):?\s*\n?\s*([\d\.\s]+x[\d\.\s]+x[\d\.\s]+mm)", block_text, re.IGNORECASE)
    mat_size = m_size.group(1).strip() if m_size else ""
    fields["Material Size"] = mat_size
    fields["Material Size (TextBox18)"] = mat_size

    # 6. Thickness (TextBox22)
    m_thick = re.search(r"Thickness\s+([\d\.]+)\s*mm", block_text, re.IGNORECASE)
    if m_thick:
        thickness = m_thick.group(1).strip()
    elif mat_size:
        parts = mat_size.replace("mm", "").split("x")
        thickness = parts[2].strip() if len(parts) >= 3 else ""
    else:
        thickness = ""
    fields["Thickness"] = thickness
    fields["Thickness (TextBox22)"] = thickness

    # 7. Raw Material Weight (TextBox24)
    m_weight = re.search(r"(?:Raw material weight|Production package weight):?\s*\n?\s*([\d\.]+)\s*kg", block_text, re.IGNORECASE)
    weight = m_weight.group(1).strip() if m_weight else ""
    fields["Raw Material Weight"] = weight
    fields["Raw Material Weight (TextBox24)"] = weight

    # 8. Process Length (TextBox25) - Cutting length
    m_len = re.search(r"(?:Process length|Cutting length):?\s*\n?\s*([\d\.]+)\s*mm", block_text, re.IGNORECASE)
    length = m_len.group(1).strip() if m_len else ""
    fields["Process Length"] = length
    fields["Process Length (TextBox25)"] = length

    # 9. Process Quantity (TextBox26) - Rpt
    m_qty = re.search(r"(?:Process quantity|Rpt):?\s*\n?\s*(\d+)", block_text, re.IGNORECASE)
    qty = m_qty.group(1).strip() if m_qty else ""
    fields["Process Quantity"] = qty
    fields["Process Quantity (TextBox26)"] = qty

    return fields


def extract_all_programs(pdf_path: str | Path) -> Dict[str, Any]:
    """
    Extract all NC programs from a TRUMPF Setup Plan PDF.
    Supports both single-program and multi-program / multi-sheet PDFs.
    
    Returns:
      {
        "total_programs": int,
        "default_program": str,
        "machine_name": str,
        "programs": { "<program_name>": { ... 8 fields ... } },
        "fields": { ... default program fields ... },
        "csv": "<formatted multi-line CSV for default program>",
        "table_csv": "<full CSV table for all programs>"
      }
    """
    pdf_path = Path(pdf_path)
    pages_text: List[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            pages_text.append(t)

    full_text = "\n".join(pages_text)

    # Global Machine Name (usually from Workplace / Machine on Page 1)
    m_machine = re.search(
        r"(?:Machine|Workplace):?\s*([^\r\n]+?)(?=\s+Target|\s+Number|\r|\n|$)",
        full_text,
        re.IGNORECASE,
    )
    global_machine = m_machine.group(1).strip().replace(" ", "_") if m_machine else ""

    programs: Dict[str, Dict[str, str]] = {}

    # Scan page-by-page for NC programs
    for page_text in pages_text:
        # Match 'Main program:' or 'Main program\n'
        m_prog = re.search(r"Main program:?\s*\n?\s*([A-Za-z0-9_\-]+)", page_text, re.IGNORECASE)
        if m_prog:
            prog_name = m_prog.group(1).strip()
            # Ignore table column headers such as 'Main program Rpt...'
            if prog_name.lower() in ("rpt", "production", "dimensions", "batch", "duration", "scrap", "raw"):
                continue

            prog_data = _parse_program_block(page_text, default_machine=global_machine)

            # A valid program page must have at least Material Name or Material Size
            if not prog_data.get("Material Name") and not prog_data.get("Material Size"):
                continue

            if prog_name not in programs:
                programs[prog_name] = prog_data
            else:
                # Merge any missing fields if this program spans multiple pages
                for k, v in prog_data.items():
                    if v and not programs[prog_name].get(k):
                        programs[prog_name][k] = v

    # Fallback for single-sheet or non-standard plans where "Main program:" wasn't found
    if not programs:
        fallback_data = _parse_program_block(full_text, default_machine=global_machine)
        prog_name = fallback_data.get("Program Name") or "Program_1"
        fallback_data["Program Name"] = prog_name
        programs[prog_name] = fallback_data

    # Generate CSV per program
    for prog_name, data in programs.items():
        data["csv"] = build_csv(data)

    default_prog_name = next(iter(programs.keys()))
    default_fields = programs[default_prog_name]
    default_csv = default_fields.get("csv", "")
    table_csv = build_table_csv(programs)

    missing_material_programs = [
        prog_name for prog_name, data in programs.items() if data.get("is_material_blank")
    ]
    has_missing_material = len(missing_material_programs) > 0
    warnings = []
    if has_missing_material:
        for p in missing_material_programs:
            warnings.append(f"Material Name is blank in PDF for program '{p}'")

    return {
        "total_programs": len(programs),
        "default_program": default_prog_name,
        "machine_name": global_machine or default_fields.get("Machine Name", ""),
        "has_missing_material": has_missing_material,
        "missing_material_programs": missing_material_programs,
        "warnings": warnings,
        "programs": programs,
        "fields": default_fields,
        "csv": default_csv,
        "table_csv": table_csv,
    }


def extract_all(pdf_path: str | Path) -> Dict[str, str]:
    """
    Backward-compatible extractor returning the 8 fields of the primary program.
    """
    res = extract_all_programs(pdf_path)
    return res["fields"]


def build_csv(fields: Dict[str, Any]) -> str:
    """
    Format extracted fields into the multi-line string format expected by VB.NET regexes:
        Machine Name <value>,
        Material Name <value>
        Laser Material Name <value>,
        Material Size <value>
        Thickness <value>
        Raw Material Weight <value>
        Process Length <value>
        Process Quantity <value>
    """
    machine = fields.get("Machine Name") or fields.get("Machine Name (TextBox21)", "")
    mat = fields.get("Material Name") or fields.get("Material Name (TextBox16)", "")
    laser_mat = fields.get("Laser Material Name") or fields.get("Laser Material Name (TextBox27)", "")
    size = fields.get("Material Size") or fields.get("Material Size (TextBox18)", "")
    thickness = fields.get("Thickness") or fields.get("Thickness (TextBox22)", "")
    weight = fields.get("Raw Material Weight") or fields.get("Raw Material Weight (TextBox24)", "")
    length = fields.get("Process Length") or fields.get("Process Length (TextBox25)", "")
    qty = fields.get("Process Quantity") or fields.get("Process Quantity (TextBox26)", "")

    return (
        f"Machine Name {machine},\n"
        f"Material Name {mat}\n"
        f"Laser Material Name {laser_mat},\n"
        f"Material Size {size}\n"
        f"Thickness {thickness}\n"
        f"Raw Material Weight {weight}\n"
        f"Process Length {length}\n"
        f"Process Quantity {qty}"
    )


def build_table_csv(programs: Dict[str, Dict[str, Any]]) -> str:
    """Build a standard tabular CSV string for all extracted programs."""
    headers = [
        "Program Name",
        "Machine Name",
        "Material Name",
        "Laser Material Name",
        "Material Size",
        "Thickness",
        "Raw Material Weight",
        "Process Length",
        "Process Quantity",
    ]
    rows = [",".join(headers)]
    for prog_name, data in programs.items():
        row = [
            f'"{prog_name}"',
            f'"{data.get("Machine Name", "")}"',
            f'"{data.get("Material Name", "")}"',
            f'"{data.get("Laser Material Name", "")}"',
            f'"{data.get("Material Size", "")}"',
            f'"{data.get("Thickness", "")}"',
            f'"{data.get("Raw Material Weight", "")}"',
            f'"{data.get("Process Length", "")}"',
            f'"{data.get("Process Quantity", "")}"',
        ]
        rows.append(",".join(row))
    return "\n".join(rows)


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
    parser = argparse.ArgumentParser(description="Extract setup plan data from PDF (single or multi-program)")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--out", "-o", help="Output text path (CSV)", default=None)
    parser.add_argument("--json", "-j", help="Output JSON path", default=None)
    args = parser.parse_args()

    result = extract_all_programs(args.pdf)

    print(f"Total Programs Extracted: {result['total_programs']}")
    print(f"Machine Name: {result['machine_name']}")
    print("\nPrograms:")
    for name, prog in result["programs"].items():
        print(f"  - {name}: Mat={prog.get('Material Name')}, Thk={prog.get('Thickness')}, Qty={prog.get('Process Quantity')}, CutLen={prog.get('Process Length')}")

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(result["table_csv"], encoding="utf-8")
        print(f"\nWrote Tabular CSV output to {out_path.resolve()}")

    if args.json:
        json_path = Path(args.json)
        json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote JSON output to {json_path.resolve()}")


if __name__ == "__main__":
    main()
