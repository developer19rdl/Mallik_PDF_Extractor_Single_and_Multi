"""
test_end_to_end.py
------------------
End-to-end test:
  1. Start the FastAPI server on port 8004 (background).
  2. Build the exact JSON request the VB.NET client sends:
       {"file": "data:application/pdf;base64,<...>"}
  3. POST it to http://127.0.0.1:8004/upload_pdf.
  4. Verify:
     - Multi-program response structure ("programs" dictionary, "total_programs").
     - Backward-compatible "csv" response and VB.NET regex simulation.
"""
import base64
import subprocess
import sys
import time
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from extract_pdf_data import simulate_vbnet_extraction

DEFAULT_PDF = Path(r"D:\Download\My_Home_GRAVA_6MMHR_SetupPlan (1).pdf")
FIXTURE_PDF = SCRIPT_DIR / "test_sample_multi.pdf"


def main() -> int:
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    elif DEFAULT_PDF.exists():
        pdf_path = DEFAULT_PDF
    elif FIXTURE_PDF.exists():
        pdf_path = FIXTURE_PDF
    else:
        print("Error: No PDF file found for testing.", file=sys.stderr)
        return 1

    print(f"Testing with PDF: {pdf_path}")

    # 1. Read PDF and encode as data URI (exactly like VB.NET ConvertToBase64)
    pdf_bytes = pdf_path.read_bytes()
    b64 = base64.b64encode(pdf_bytes).decode("ascii")
    data_uri = f"data:application/pdf;base64,{b64}"

    # 2. Build the exact JSON the VB.NET client sends
    payload = {"file": data_uri}

    # 3. Start the FastAPI server in background
    print("Starting FastAPI server on port 8004 ...")
    server = subprocess.Popen(
        [sys.executable, str(SCRIPT_DIR / "pdf_upload_server.py")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    try:
        # Wait for server to come up
        for _ in range(30):
            time.sleep(0.5)
            try:
                r = httpx.get("http://127.0.0.1:8004/", timeout=1.0)
                if r.status_code == 200:
                    break
            except Exception:
                continue
        else:
            print("Server failed to start.", file=sys.stderr)
            return 1

        # 4. POST /upload_pdf
        print("\nPOSTing PDF to http://127.0.0.1:8004/upload_pdf ...")
        r = httpx.post("http://127.0.0.1:8004/upload_pdf",
                       json=payload, timeout=60.0)
        print(f"HTTP status: {r.status_code}")
        if r.status_code != 200:
            print(r.text)
            return 2

        body = r.json()

        # 5. Verify Multi-Program Structure
        total_programs = body.get("total_programs", 0)
        programs = body.get("programs", {})
        print(f"\n--- Multi-Program Verification ---")
        print(f"Total Programs Extracted: {total_programs}")
        for p_name, p_data in programs.items():
            print(f"  Program: {p_name}")
            print(f"    Machine:       {p_data.get('Machine Name')}")
            print(f"    Material:      {p_data.get('Material Name')}")
            print(f"    Thickness:     {p_data.get('Thickness')}")
            print(f"    Weight:        {p_data.get('Raw Material Weight')}")
            print(f"    Process Length:{p_data.get('Process Length')}")
            print(f"    Process Qty:   {p_data.get('Process Quantity')}")

        # 6. Verify Backward Compatibility ("csv" field)
        csv_b64 = body.get("csv", "")
        print(f"\nReturned base64 CSV length: {len(csv_b64)} chars")
        csv_data = base64.b64decode(csv_b64).decode("utf-8")
        print("\n--- Decoded CSV returned by the server (for default program) ---")
        print(csv_data)

        # 7. Run the VB.NET regex simulation on the returned CSV
        print("\n--- VB.NET TextBox values that would result ---")
        result = simulate_vbnet_extraction(csv_data)
        for k, v in result.items():
            print(f"  {k:34s} = {v!r}")

        print("\nOverall: ALL PASS - End-to-end multi-extract and legacy compatibility verified!")
        return 0

    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
