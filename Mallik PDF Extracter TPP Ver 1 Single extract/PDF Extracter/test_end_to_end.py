"""
End-to-end test:
  1. Start the FastAPI server on port 8004 (background).
  2. Build the exact JSON request the VB.NET client sends:
       {"file": "data:application/pdf;base64,<...>"}
  3. POST it to http://127.0.0.1:8004/upload_pdf.
  4. Decode the returned base64 CSV and run the VB.NET regex simulation
     on it - this proves the round trip works.
"""
import base64
import subprocess
import sys
import time
from pathlib import Path

import httpx

DEFAULT_PDF = Path(r"D:\Download\My_Home_GRAVA_6MMHR_SetupPlan (1).pdf")
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from extract_pdf_data import simulate_vbnet_extraction


def main() -> int:
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}", file=sys.stderr)
        return 1

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
        csv_b64 = body["csv"]
        print(f"\nReturned base64 CSV length: {len(csv_b64)} chars")

        # 5. Decode the returned CSV
        csv_data = base64.b64decode(csv_b64).decode("utf-8")
        print("\n--- Decoded CSV returned by the server ---")
        print(csv_data)

        # 6. Run the VB.NET regex simulation on the returned CSV
        print("\n--- VB.NET TextBox values that would result ---")
        result = simulate_vbnet_extraction(csv_data)
        for k, v in result.items():
            print(f"  {k:34s} = {v!r}")

        # 7. Sanity assertions
        expected = {
            "Machine Name (TextBox21)":        "TruLaser_1030_L94_6KW",
            "Material Name (TextBox16)":       "HR",
            "Thickness (TextBox22)":           "6.00",
            "Raw Material Weight (TextBox24)": "147.19",
            "Process Length (TextBox25)":      "50631.54",
            "Laser Material Name (TextBox27)": "HRAM0600---",
            "Material Size (TextBox18)":       "2500.00 x 1250.00 x 6.00 mm",
            "Process Quantity (TextBox26)":    "5",
        }
        print("\n--- End-to-end correctness check ---")
        all_ok = True
        for k, exp in expected.items():
            got = result.get(k, "")
            ok = got == exp
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark}] {k:34s} expected={exp!r:30s} got={got!r}")
            if not ok:
                all_ok = False

        print("\nOverall:", "ALL PASS" if all_ok else "SOME FAILED")
        return 0 if all_ok else 3

    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())