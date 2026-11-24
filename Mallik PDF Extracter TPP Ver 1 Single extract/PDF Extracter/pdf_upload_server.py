"""
pdf_upload_server.py
--------------------
FastAPI server that exposes POST /upload_pdf - the exact endpoint the VB.NET
client calls (http://127.0.0.1:8004/upload_pdf).

Request JSON:  {"file": "data:application/pdf;base64,<...>"}
Response JSON: {"csv": "<base64-encoded CSV string>"}

The CSV returned is the multi-line format expected by the VB.NET regex
extraction logic. See extract_pdf_data.py for the field mappings and the
VB.NET simulation that verifies correctness.

Run:
    pip install fastapi uvicorn pdfplumber
    python pdf_upload_server.py
    # or: uvicorn pdf_upload_server:app --host 0.0.0.0 --port 8004

Then point the VB.NET client at http://127.0.0.1:8004/upload_pdf (already
the default URL in Button7_Click).
"""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Reuse the parsing helpers from the standalone extractor.
# Make sure extract_pdf_data.py is in the same directory or on PYTHONPATH.
from extract_pdf_data import extract_all, build_csv, simulate_vbnet_extraction


# --------------------------------------------------------------------------- #
# Optional: write each upload to disk for debugging / audit
# --------------------------------------------------------------------------- #
DEBUG_DIR = Path(__file__).parent / "uploads"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Pydantic models for the request body
# --------------------------------------------------------------------------- #
class UploadPdfRequest(BaseModel):
    """Matches the JSON the VB.NET client sends.

    The VB.NET client builds the request body as:
        Dim json As String = "{"file":"" & base64String & "}"
    where base64String is "data:application/pdf;base64,<...>".
    """
    file: str


# --------------------------------------------------------------------------- #
# FastAPI app
# --------------------------------------------------------------------------- #
app = FastAPI(
    title="Laser-Cut Setup Plan PDF -> CSV",
    version="1.0.0",
    description="Accepts a base64-encoded PDF, returns a base64-encoded CSV "
                "with the 8 fields the VB.NET client extracts.",
)


def _decode_data_uri(data_uri: str) -> bytes:
    """Decode 'data:application/pdf;base64,<...>' -> raw PDF bytes."""
    # Strip the data URI prefix if present
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

    # 1) Decode the incoming PDF
    pdf_bytes = _decode_data_uri(req.file)
    pdf_path = _save_temp_pdf(pdf_bytes)

    try:
        # 2) Extract the 8 fields from the PDF
        fields = extract_all(pdf_path)

        # 3) Build the CSV string the VB.NET client expects
        csv_data = build_csv(fields)

        # 4) Base64-encode the CSV and return it
        csv_b64 = base64.b64encode(csv_data.encode("utf-8")).decode("ascii")

        # 5) (Optional) sanity check - simulate VB.NET extraction
        verification = simulate_vbnet_extraction(csv_data)

        return JSONResponse({
            "csv": csv_b64,
            # Optional diagnostic fields (VB.NET client ignores extras):
            "fields": fields,
            "verification": verification,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")
    finally:
        # Comment out the next line if you want to keep uploaded PDFs for audit.
        try:
            pdf_path.unlink()
        except Exception:
            pass


@app.get("/")
def root():
    """Health-check / docs landing page."""
    return {
        "service": "pdf_upload_server",
        "endpoints": {
            "POST /upload_pdf": "Send {\"file\": \"data:application/pdf;base64,...\"} -> returns {\"csv\": \"<base64>\"}",
        },
        "fields_extracted": [
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


# --------------------------------------------------------------------------- #
# Allow `python pdf_upload_server.py` to start the server directly
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)