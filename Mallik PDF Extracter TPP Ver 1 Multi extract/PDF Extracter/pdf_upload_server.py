"""
pdf_upload_server.py
--------------------
FastAPI server that exposes POST /upload_pdf - the exact endpoint the VB.NET
client calls (http://127.0.0.1:8004/upload_pdf).

Supports:
  1. Multi-Program Setup Plans: returns "programs" dictionary for VB.NET ComboBox binding.
  2. Legacy Single-Program Plans: returns "csv" and "fields" for 100% backward compatibility.

Request JSON:  {"file": "data:application/pdf;base64,<...>"}
Response JSON: {
    "total_programs": 18,
    "default_program": "VIHANG_Gaur_3MMHR_1",
    "machine_name": "TruLaser_1030_L94_6KW",
    "programs": {
        "VIHANG_Gaur_3MMHR_1": {
            "Program Name": "VIHANG_Gaur_3MMHR_1",
            "Machine Name": "TruLaser_1030_L94_6KW",
            "Material Name": "HR",
            "Thickness": "3.00",
            "Raw Material Weight": "44.16",
            "Process Length": "19722.08",
            "Laser Material Name": "HRAM0300---",
            "Material Size": "1500.00 x 1250.00 x 3.00 mm",
            "Process Quantity": "2"
        },
        ...
    },
    "csv": "<base64-encoded CSV string of default program>",
    "table_csv": "<base64-encoded tabular CSV string>",
    "fields": { ... default program fields ... },
    "verification": { ... }
}

Run:
    pip install fastapi uvicorn pdfplumber
    python pdf_upload_server.py
"""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Parsing helpers from the extractor module
from extract_pdf_data import (
    extract_all_programs,
    build_csv,
    simulate_vbnet_extraction,
)


# Optional: write each upload to disk for debugging / audit
DEBUG_DIR = Path(__file__).parent / "uploads"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


class UploadPdfRequest(BaseModel):
    """Matches the JSON the VB.NET client sends.

    The VB.NET client builds the request body as:
        Dim json As String = "{"file":"" & base64String & "}"
    where base64String is "data:application/pdf;base64,<...>".
    """
    file: str


app = FastAPI(
    title="Laser-Cut Setup Plan PDF Multi-Extract Server",
    version="2.0.0",
    description="Accepts a base64-encoded PDF, extracts all NC programs, and returns "
                "both a 'programs' dictionary for ComboBox binding and a base64 CSV "
                "for backward compatibility.",
)


def _decode_data_uri(data_uri: str) -> bytes:
    """Decode 'data:application/pdf;base64,<...>' -> raw PDF bytes."""
    if "," in data_uri and data_uri.startswith("data:"):
        b64_part = data_uri.split(",", 1)[1]
    else:
        b64_part = data_uri
    try:
        return base64.b64decode(b64_part)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 PDF: {e}")


def _save_temp_pdf(pdf_bytes: bytes) -> Path:
    """Write the PDF bytes to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix="upload_", dir=str(DEBUG_DIR))
    with open(fd, "wb") as f:
        f.write(pdf_bytes)
    return Path(path)


@app.post("/upload_pdf")
def upload_pdf(req: UploadPdfRequest):
    if not req.file:
        raise HTTPException(status_code=400, detail="Missing 'file' field in JSON body.")

    # 1) Decode incoming PDF
    pdf_bytes = _decode_data_uri(req.file)
    pdf_path = _save_temp_pdf(pdf_bytes)

    try:
        # 2) Extract all programs from the PDF
        result = extract_all_programs(pdf_path)

        # 3) Base64-encode the CSV for the default program (for legacy VB.NET client compatibility)
        csv_b64 = base64.b64encode(result["csv"].encode("utf-8")).decode("ascii")
        table_csv_b64 = base64.b64encode(result["table_csv"].encode("utf-8")).decode("ascii")

        # 4) Simulate VB.NET regex verification on the default program
        verification = simulate_vbnet_extraction(result["csv"])

        return JSONResponse({
            "total_programs": result["total_programs"],
            "default_program": result["default_program"],
            "machine_name": result["machine_name"],
            "has_missing_material": result["has_missing_material"],
            "missing_material_programs": result["missing_material_programs"],
            "warnings": result["warnings"],
            "programs": result["programs"],
            "csv": csv_b64,
            "table_csv": table_csv_b64,
            "fields": result["fields"],
            "verification": verification,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")
    finally:
        try:
            pdf_path.unlink()
        except Exception:
            pass


@app.get("/")
def root():
    """Health-check / landing page."""
    return {
        "service": "pdf_upload_server",
        "version": "2.0.0 (Multi-Extract)",
        "endpoints": {
            "POST /upload_pdf": "Send {\"file\": \"data:application/pdf;base64,...\"} -> returns multi-program JSON",
        },
        "fields_per_program": [
            "Program Name",
            "Machine Name (TextBox21)",
            "Material Name (TextBox16)",
            "Thickness (TextBox22)",
            "Raw Material Weight (TextBox24)",
            "Process Length (TextBox25)",
            "Laser Material Name (TextBox27)",
            "Material Size (TextBox18)",
            "Process Quantity (TextBox26)",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
