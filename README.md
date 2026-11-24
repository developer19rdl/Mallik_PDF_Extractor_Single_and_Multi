# Mallik_PDF_Extractor_Single_and_Multi

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![VB.NET Integration](https://img.shields.io/badge/Integration-VB.NET%20WinForms-purple.svg)](https://learn.microsoft.com/dotnet/visual-basic/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)
[![PDF Engine](https://img.shields.io/badge/Engine-pdfplumber-ff69b4.svg)](https://github.com/jsvine/pdfplumber)

**Mallik PDF Extractor** is an industrial-grade PDF parsing solution tailored for sheet metal manufacturing and CNC laser cutting operations. It automatically reads and extracts technical parameters from **TRUMPF Laser-Cut Setup Plans (TruLaser)** and makes them immediately accessible to desktop ERP / MES software (such as VB.NET Windows Forms applications) via a high-performance local REST API or direct CLI execution.

---

## Repository Overview

This repository hosts two editions of the extractor to suit different manufacturing shop floor requirements:

```
Mallik_PDF_Extractor_Single_and_Multi/
│
├── Mallik PDF Extracter TPP Ver 1 Single extract/
│   └── PDF Extracter/
│       ├── extract_pdf_data.py          # Single-program parser engine & CLI
│       ├── pdf_upload_server.py         # FastAPI local server (Port 8004)
│       ├── pdf_upload_server.spec       # PyInstaller build specification
│       ├── test_end_to_end.py           # Integration test script
│       ├── extracted.csv                # Sample extracted output
│       ├── command.txt                  # Quick command reference
│       ├── vbnet_integration_guide.html # Legacy single-plan VB.NET guide
│       ├── vbnet_integration_guide.pdf  # Printable single-plan documentation
│       └── dist/
│           └── pdf_upload_server.exe    # Standalone zero-install Windows binary
│
├── Mallik PDF Extracter TPP Ver 1 Multi extract/
│   └── PDF Extracter/
│       ├── extract_pdf_data.py          # Multi-program parser engine (Single + Multi)
│       ├── pdf_upload_server.py         # FastAPI multi-program REST server
│       ├── pdf_upload_server.spec       # PyInstaller build configuration
│       ├── test_end_to_end.py           # Comprehensive multi-program test suite
│       ├── test_sample_multi.pdf        # Test fixture with multiple NC jobs
│       ├── vbnet_multi_extract_guide.html # Complete Form5 integration manual
│       └── dist/
│           └── pdf_upload_server.exe    # Standalone multi-extract executable
│
├── .gitignore                           # Excludes intermediate build caches & temp files
└── README.md                            # Comprehensive manual (Non-Dev & Dev)
```

---

## Table of Contents

- [SECTION 1: NON-DEVELOPER GUIDE (Operators, Shop Floor & Production Users)](#section-1-non-developer-guide)
  - [1. What is this tool and why is it used?](#1-what-is-this-tool-and-why-is-it-used)
  - [2. Single Extract vs. Multi Extract: Which one to use?](#2-single-extract-vs-multi-extract-which-one-to-use)
  - [3. The 8 Extracted Parameters Explained](#3-the-8-extracted-parameters-explained)
  - [4. Step-by-Step Operator Guide (No Coding Required)](#4-step-by-step-operator-guide-no-coding-required)
  - [5. Troubleshooting & FAQ for Non-Developers](#5-troubleshooting--faq-for-non-developers)
- [SECTION 2: DEVELOPER & TECHNICAL INTEGRATION GUIDE](#section-2-developer--technical-integration-guide)
  - [1. Architecture & Data Flow](#1-architecture--data-flow)
  - [2. Prerequisites & Environment Setup](#2-prerequisites--environment-setup)
  - [3. Standalone CLI Usage](#3-standalone-cli-usage)
  - [4. Local REST API Specification](#4-local-rest-api-specification)
  - [5. VB.NET Windows Forms Integration (Form5)](#5-vbnet-windows-forms-integration-form5)
  - [6. Building the Standalone Executable (.exe)](#6-building-the-standalone-executable-exe)
  - [7. Automated Testing & Verification](#7-automated-testing--verification)
  - [8. Edge Cases & Parser Robustness](#8-edge-cases--parser-robustness)

---

# SECTION 1: NON-DEVELOPER GUIDE
> **Audience:** Laser Machine Operators, Production Supervisors, Quality Assurance (QA) Personnel, and Non-Technical Office Staff.

---

### 1. What is this tool and why is it used?

When nesting jobs are created for CNC Laser Cutting machines (specifically **TRUMPF TruLaser** systems), the CAM software outputs a Setup Plan PDF. This document contains vital manufacturing specifications: which machine to use, raw sheet dimensions, sheet thickness, material code, cutting length, cutting duration, and repeating part quantities.

- **Without this tool:** Operators or data entry staff must manually read the PDF and type numbers into 8 to 10 different boxes in the company's desktop software (`Form5`). This is slow, tedious, and prone to typing mistakes (such as misreading 3.00 mm vs 8.00 mm thickness).
- **With this tool:** You click **"Browse / Upload PDF"**, and within 1 second, all fields are **automatically detected, cleaned, and filled** directly into the desktop program.

---

### 2. Single Extract vs. Multi Extract: Which one to use?

| Feature | Single Extract (`Ver 1 Single extract`) | Multi Extract (`Ver 1 Multi extract`) ⭐ **Recommended** |
| :--- | :--- | :--- |
| **Best suited for** | Setup plan PDFs containing **only 1 program / sheet** | PDFs containing **multiple programs / sheets** (e.g., 2 to 25+ nesting layouts in one PDF) |
| **User Interface** | Directly fills textboxes on the screen | Adds a dropdown list (`ComboBox`) of all program names; selecting any program auto-populates the textboxes |
| **Backward Compatible** | Yes | Yes (also works with 1-program PDFs seamlessly) |

> **Recommendation:** Use **`Ver 1 Multi extract`** as your standard. It handles both single-sheet and multi-sheet PDFs automatically.

---

### 3. The 8 Extracted Parameters Explained

Here is a plain-English explanation of what values are extracted from the TRUMPF PDF and where they land in your desktop software:

| # | Parameter Name | Example Value | Description | Desktop Screen Field |
|---|---|---|---|---|
| **1** | **Program Name** | `VIHANG_Gaur_3MMHR_1` | The NC program filename loaded into the TRUMPF laser controller. | `ComboBoxProgramCode` |
| **2** | **Machine Name** | `TruLaser_1030_L94_6KW` | The physical laser machine designated for cutting this sheet. | `TextBox21` |
| **3** | **Material Name** | `HR` | Standard commercial material grade (e.g., HR, CR, SS, AL). | `TextBox16` |
| **4** | **Laser Material Name** | `HRAM0300---` | Raw material stock code used in CAM software database. | `TextBox27` |
| **5** | **Material Dimensions** | `1500.00 x 1250.00 x 3.00 mm` | Full physical dimensions (Length x Width x Thickness) of raw sheet. | `TextBox18` |
| **6** | **Thickness** | `3.00` | Sheet metal thickness in millimeters (mm). | `TextBox22` |
| **7** | **Raw Material Weight** | `44.16` | Total weight of the sheet in kilograms (kg). | `TextBox24` |
| **8** | **Process Length** | `19722.08` | Total laser cutting path length in millimeters (mm). | `TextBox25` |
| **9** | **Process Quantity (Rpt)** | `2` | Number of times this sheet layout needs to be repeated / cut. | `TextBox26` |

---

### 4. Step-by-Step Operator Guide (No Coding Required)

You do **not** need Python, Git, or command-line experience to use this tool on a Windows workstation.

#### Step 1: Start the Background Server
1. Navigate to:
   ```
   Mallik PDF Extracter TPP Ver 1 Multi extract\PDF Extracter\dist\
   ```
2. Double-click **`pdf_upload_server.exe`**.
3. A black console window will open displaying:
   ```text
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8004 (Press CTRL+C to quit)
   ```
4. **Leave this window open.** You can minimize it to your taskbar while you work.

> [!TIP]
> You can create a desktop shortcut to `pdf_upload_server.exe` for one-click access every morning.

#### Step 2: Use Your Desktop Application
1. Launch your company manufacturing desktop software (`Form5`).
2. Click the **"Browse"** or **"Upload PDF"** button.
3. Select your TRUMPF Setup Plan PDF.
4. The system will contact the local server and populate the **Program Code** dropdown.
5. If the PDF has multiple programs, choose the program code you wish to process from the dropdown. All 8 textboxes will instantly update with that program's data!

#### Step 3: Shutting Down
When your work shift is finished:
- Click the `X` button on the black console window, or select the window and press `Ctrl + C`.

---

### 5. Troubleshooting & FAQ for Non-Developers

- **Q: The black window opens and immediately closes! What should I do?**
  - **Reason:** Another program (or an older copy of the server) is already using port `8004`.
  - **Fix:** Open Task Manager (`Ctrl + Shift + Esc`), look for any running `pdf_upload_server.exe` or `python.exe` under Background Processes, select it, and click **End Task**. Then try double-clicking again.

- **Q: Windows Defender shows a blue screen saying "Windows protected your PC"?**
  - **Reason:** Windows SmartScreen flags newly compiled internal `.exe` files that don't have an expensive commercial digital signature.
  - **Fix:** Click **"More info"** and then click **"Run anyway"**.

- **Q: Windows Firewall asks for network permissions?**
  - **Fix:** Check **"Private networks (home or work)"** and click **"Allow access"**. The server only communicates locally on your own computer (`127.0.0.1:8004`).

- **Q: Why is the Material Name blank in the text box?**
  - **Reason:** Some TRUMPF setup plans have an empty "Material" field in the PDF header. The extractor automatically leaves it empty rather than accidentally capturing the wrong header word. You can manually enter the material name if required.

---

# SECTION 2: DEVELOPER & TECHNICAL INTEGRATION GUIDE
> **Audience:** Software Engineers, Full-Stack Developers, ERP System Integrators, and DevOps Administrators.

---

### 1. Architecture & Data Flow

The solution decouples PDF parsing logic from the legacy VB.NET client by deploying a lightweight, high-performance local microservice powered by **FastAPI** and **pdfplumber**.

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Operator / User
    participant WinForms as VB.NET Client (Form5)
    participant Server as FastAPI Server (Port 8004)
    participant Parser as extract_pdf_data.py (pdfplumber)

    Operator->>WinForms: Clicks "Browse" & selects PDF
    WinForms->>WinForms: Reads PDF bytes & encodes to Base64 Data URI
    WinForms->>Server: POST http://127.0.0.1:8004/upload_pdf {"file": "data:application/pdf;base64,..."}
    Server->>Server: Decodes Base64 into temporary file (uploads/)
    Server->>Parser: extract_all_programs(temp_pdf_path)
    Parser->>Parser: Opens PDF via pdfplumber, extracts text & regex tokens
    Parser-->>Server: Returns structured Python dict (all programs + fields)
    Server-->>WinForms: JSON response {"total_programs": N, "programs": {...}, "csv": "..."}
    WinForms->>WinForms: Clears & binds ComboBoxProgramCode with program keys
    WinForms->>WinForms: Auto-selects index 0 & fills TextBox16, 18, 21, 22, 24, 25, 26, 27
    WinForms-->>Operator: Displays loaded data ready for production
```

---

### 2. Prerequisites & Environment Setup

#### Prerequisites
- **Operating System:** Windows 10/11 or Windows Server 2016+
- **Python Version:** Python 3.10, 3.11, or 3.12 (64-bit recommended)
- **.NET Framework:** .NET Framework 4.5+ or .NET 6/8 for client applications

#### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/developer19rdl/Mallik_PDF_Extractor_Single_and_Multi.git
   cd Mallik_PDF_Extractor_Single_and_Multi
   ```

2. Navigate to the desired version directory:
   ```bash
   cd "Mallik PDF Extracter TPP Ver 1 Multi extract/PDF Extracter"
   ```

3. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. Install the required dependencies:
   ```bash
   pip install pdfplumber fastapi uvicorn httpx pydantic pyinstaller
   ```

---

### 3. Standalone CLI Usage

The core engine `extract_pdf_data.py` can be executed standalone from the terminal for batch processing, debugging, or headless pipeline integration.

#### Command-line Syntax:
```bash
python extract_pdf_data.py "<path_to_pdf>" [OPTIONS]
```

#### Options:
- `--out <filename.csv>`: Export the extracted data directly to a CSV file.
- `--program <name>`: In multi-program PDFs, specify which NC program to extract.
- `--all`: Print every program found in the PDF.
- `--json`: Output raw parsed data as formatted JSON to stdout.

#### Examples:
```bash
# Extract single or multi-program PDF and write to CSV
python extract_pdf_data.py "test_sample_multi.pdf" --out extracted.csv

# Inspect full JSON payload in terminal
python extract_pdf_data.py "test_sample_multi.pdf" --json
```

---

### 4. Local REST API Specification

#### Service Configuration
- **Host:** `0.0.0.0` (accessible via `127.0.0.1` locally)
- **Port:** `8004`
- **Interactive OpenAPI Documentation:** Available at `http://127.0.0.1:8004/docs`

#### Endpoint: Health Check
```http
GET / HTTP/1.1
Host: 127.0.0.1:8004
```
**Response (200 OK):**
```json
{
  "service": "Laser-Cut Setup Plan PDF Multi-Extract Server",
  "status": "online",
  "port": 8004,
  "endpoint": "POST /upload_pdf",
  "version": "2.0.0"
}
```

---

#### Endpoint: Upload & Extract PDF
```http
POST /upload_pdf HTTP/1.1
Host: 127.0.0.1:8004
Content-Type: application/json
```

##### Request Body:
```json
{
  "file": "data:application/pdf;base64,JVBERi0xLjQKJcTl8uXr..."
}
```

##### Response Body (`v2.0.0 Multi-Extract`):
```json
{
  "total_programs": 2,
  "default_program": "VIHANG_Gaur_3MMHR_1",
  "machine_name": "TruLaser_1030_L94_6KW",
  "programs": {
    "VIHANG_Gaur_3MMHR_1": {
      "Program Name": "VIHANG_Gaur_3MMHR_1",
      "Machine Name": "TruLaser_1030_L94_6KW",
      "Machine Name (TextBox21)": "TruLaser_1030_L94_6KW",
      "Material Name": "HR",
      "Material Name (TextBox16)": "HR",
      "is_material_blank": false,
      "Laser Material Name": "HRAM0300---",
      "Laser Material Name (TextBox27)": "HRAM0300---",
      "Material Size": "1500.00 x 1250.00 x 3.00 mm",
      "Material Size (TextBox18)": "1500.00 x 1250.00 x 3.00 mm",
      "Thickness": "3.00",
      "Thickness (TextBox22)": "3.00",
      "Raw Material Weight": "44.16",
      "Raw Material Weight (TextBox24)": "44.16",
      "Process Length": "19722.08",
      "Process Length (TextBox25)": "19722.08",
      "Process Quantity": "2",
      "Process Quantity (TextBox26)": "2"
    },
    "VIHANG_Gaur_3MMHR_2": {
      "Program Name": "VIHANG_Gaur_3MMHR_2",
      "Machine Name": "TruLaser_1030_L94_6KW",
      "Material Name": "HR",
      "Thickness": "3.00",
      "Raw Material Weight": "44.16",
      "Process Length": "21255.34",
      "Laser Material Name": "HRAM0300---",
      "Material Size": "1500.00 x 1250.00 x 3.00 mm",
      "Process Quantity": "1"
    }
  },
  "fields": {
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
  "csv": "Program Name,VIHANG_Gaur_3MMHR_1\nMachine Name,TruLaser_1030_L94_6KW\n...",
  "table_csv": "Program Name,Machine Name,Material Name,...\nVIHANG_Gaur_3MMHR_1,TruLaser_1030_L94_6KW,..."
}
```

---

### 5. VB.NET Windows Forms Integration (Form5)

Integrating with existing WinForms desktop software requires minimal code changes using `Newtonsoft.Json`.

#### Step 1: Add Class Variable in `Form5.vb`
```vb
Imports System.IO
Imports System.Net
Imports System.Text
Imports Newtonsoft.Json.Linq

Public Class Form5
    ' Cache the dictionary of all extracted programs
    Private pdfPrograms As JObject = Nothing
```

#### Step 2: Handle PDF Upload Response
```vb
Private Sub UploadPdf(ByVal base64String As String)
    Try
        Dim url As String = "http://127.0.0.1:8004/upload_pdf"
        Dim request As HttpWebRequest = CType(WebRequest.Create(url), HttpWebRequest)
        request.Method = "POST"
        request.ContentType = "application/json"
        request.Timeout = 30000

        ' Create request JSON payload
        Dim jsonPayload As String = "{""file"":""" & base64String & """}"
        Dim byteArray As Byte() = Encoding.UTF8.GetBytes(jsonPayload)
        request.ContentLength = byteArray.Length

        Using dataStream As Stream = request.GetRequestStream()
            dataStream.Write(byteArray, 0, byteArray.Length)
        End Using

        Using response As WebResponse = request.GetResponse()
            Using responseStream As Stream = response.GetResponseStream()
                Using reader As New StreamReader(responseStream)
                    Dim serverResponse As String = reader.ReadToEnd()
                    Dim json As JObject = JObject.Parse(serverResponse)

                    ' Multi-program handling
                    If json.ContainsKey("programs") Then
                        pdfPrograms = CType(json("programs"), JObject)

                        ' Populate ComboBox
                        ComboBoxProgramCode.Items.Clear()
                        For Each item In pdfPrograms.Properties()
                            ComboBoxProgramCode.Items.Add(item.Name)
                        Next

                        ' Automatically trigger selection of first program
                        If ComboBoxProgramCode.Items.Count > 0 Then
                            ComboBoxProgramCode.SelectedIndex = 0
                            MessageBox.Show("Successfully extracted " & ComboBoxProgramCode.Items.Count.ToString() & " NC programs!", 
                                            "Extraction Complete", MessageBoxButtons.OK, MessageBoxIcon.Information)
                        End If
                    End If
                End Using
            End Using
        End Using
    Catch ex As Exception
        MessageBox.Show("Error communicating with PDF server: " & ex.Message, 
                        "Connection Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
    End Try
End Sub
```

#### Step 3: Populate Controls on Dropdown Change
```vb
Private Sub ComboBoxProgramCode_SelectedIndexChanged(sender As Object, e As EventArgs) Handles ComboBoxProgramCode.SelectedIndexChanged
    If pdfPrograms Is Nothing OrElse ComboBoxProgramCode.SelectedItem Is Nothing Then Exit Sub

    Dim selectedProg As String = ComboBoxProgramCode.SelectedItem.ToString()
    If pdfPrograms.ContainsKey(selectedProg) Then
        Dim p As JObject = CType(pdfPrograms(selectedProg), JObject)

        ' Direct 1:1 textbox mapping
        TextBox21.Text = If(p("Machine Name") IsNot Nothing, p("Machine Name").ToString(), "")
        TextBox16.Text = If(p("Material Name") IsNot Nothing, p("Material Name").ToString(), "")
        TextBox18.Text = If(p("Material Size") IsNot Nothing, p("Material Size").ToString(), "")
        TextBox22.Text = If(p("Thickness") IsNot Nothing, p("Thickness").ToString(), "")
        TextBox24.Text = If(p("Raw Material Weight") IsNot Nothing, p("Raw Material Weight").ToString(), "")
        TextBox25.Text = If(p("Process Length") IsNot Nothing, p("Process Length").ToString(), "")
        TextBox26.Text = If(p("Process Quantity") IsNot Nothing, p("Process Quantity").ToString(), "")
        TextBox27.Text = If(p("Laser Material Name") IsNot Nothing, p("Laser Material Name").ToString(), "")
    End If
End Sub
```

---

### 6. Building the Standalone Executable (.exe)

To package the FastAPI server into a zero-dependency standalone `.exe` using PyInstaller:

1. Open PowerShell and navigate to the folder containing `pdf_upload_server.spec`:
   ```powershell
   cd "Mallik PDF Extracter TPP Ver 1 Multi extract\PDF Extracter"
   ```

2. Execute PyInstaller with the spec file:
   ```bash
   pyinstaller --clean pdf_upload_server.spec
   ```

3. The generated standalone executable will be placed in the `dist/` directory:
   ```
   dist/pdf_upload_server.exe
   ```

#### Key Spec Configuration Details
The `pdf_upload_server.spec` bundles necessary hidden imports for Uvicorn's asynchronous loop workers and protocol handlers:
```python
hiddenimports=[
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'extract_pdf_data',
]
```

---

### 7. Automated Testing & Verification

An end-to-end integration test is provided in `test_end_to_end.py`. It spins up the server in the background, crafts a simulated VB.NET base64 JSON payload, verifies HTTP status 200, checks the multi-program JSON dictionary, and confirms legacy CSV output.

Run the test:
```powershell
python test_end_to_end.py test_sample_multi.pdf
```

Expected Output:
```text
Testing with PDF: test_sample_multi.pdf
Starting FastAPI server on port 8004 ...
POSTing PDF to http://127.0.0.1:8004/upload_pdf ...
HTTP status: 200

--- Multi-Program Verification ---
Total Programs Extracted: 2
  Program: VIHANG_Gaur_3MMHR_1
    Machine:       TruLaser_1030_L94_6KW
    Material:      HR
    Thickness:     3.00
    Weight:        44.16
    Process Length:19722.08
    Process Qty:   2
...
All tests passed successfully!
```

---

### 8. Edge Cases & Parser Robustness

1. **Blank Material Handling:**
   In certain CAM exports, the `Material:` label is immediately followed by other header keys (e.g., `Raw material`, `Dimensions`). The parser implements strict guard words (`raw`, `production`, `dimensions`, `thickness`, `rpt`) to ensure it flags `is_material_blank = true` instead of capturing section headers.

2. **Machine Name Normalization:**
   Spaces in machine titles (e.g., `TruLaser 1030 L94 6KW`) are automatically transformed into clean underscores (`TruLaser_1030_L94_6KW`) to match ERP database naming conventions.

3. **Fallback Thickness Derivation:**
   If `Thickness [X] mm` is absent in text blocks, the parser parses the third dimension from `Dimensions` (`1500 x 1250 x 3.00 mm`) to ensure `Thickness` is always populated.

4. **Multi-Program Splitting:**
   The multi-extract engine chunks the PDF based on `Main program:` anchors across pages, creating isolated extraction contexts so parameters from Sheet 2 never overwrite Sheet 1.

---

## License & Support

Maintained for Mallik engineering operations. For issues, enhancements, or bug reports, submit a GitHub issue or contact Developer 19.
