# Bee and Bumblebee COI Identification Pipeline

A Python-based workflow for processing AB1 files, generating clean FASTA sequences, and identifying bee/bumblebee species through BOLD using **BOLDigger3**.

---

## Overview

This project handles the final stages of a DNA barcoding pipeline:

1. Convert raw AB1 files (LCO/HCO reads) into clean consensus FASTA sequences.
2. Optionally convert sequences stored in Excel into FASTA format.
3. Query BOLD's identification engine automatically with **BOLDigger3**.
4. Review species-level identifications for bees and bumblebees.

BOLDigger3 is used as the BOLD search engine inside a larger Python pipeline. It handles BOLD batch limits, rate limits, database access, and result formatting.

---

## Workflow Summary

```text
AB1 files (LCO + HCO)
        │
        ▼
Clean consensus FASTA
        │
        ▼
[Optional] Excel → FASTA conversion
        │
        ▼
BOLDigger3 identification against BOLD
        │
        ▼
Results: .xlsx / .parquet files
```

---

## Requirements

- Python **3.11 or higher**
- VS Code
- Free BOLD account: https://www.boldsystems.org
- Input sequences in FASTA format, or Excel with ID and sequence columns

Python packages:

```bash
pip install boldigger3 pandas biopython openpyxl
```

Install the browser automation dependency used by BOLDigger3:

```bash
playwright install
```

---

## Project Structure

A recommended folder layout:

```text
project/
├── .venv/
├── data/
│   ├── raw_ab1/
│   ├── clean_sequences.fasta
│   └── sequences.xlsx
├── bold_db/
├── results/
├── scripts/
│   ├── excel_to_fasta.py
│   └── run_bold_pipeline.py
└── README.md
```

---

## Step 1 — Set Up VS Code Environment

1. Open your project folder in VS Code.
2. Open the integrated terminal: `Ctrl+`` ` or `View > Terminal`.
3. Create a virtual environment:

```bash
python -m venv .venv
```

4. Activate it:

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

5. In VS Code, select the interpreter:
   - Press `Ctrl+Shift+P` / `Cmd+Shift+P`
   - Type `Python: Select Interpreter`
   - Choose the interpreter inside `.venv`

---

## Step 2 — Install BOLDigger3

With the virtual environment active:

```bash
pip install boldigger3
playwright install
```

Verify installation:

```bash
boldigger3 --help
```

---

## Step 3 — Download the BOLD Reference Database

BOLDigger3 uses a local copy of the BOLD database for faster and more complete identification.

Create a database folder:

```bash
mkdir bold_db
```

Download the database:

```bash
boldigger3 download_db ./bold_db
```

You will be prompted for your BOLD username and password. Register for free at:
https://www.boldsystems.org

The database is converted to a local DuckDB file for fast processing.

---

## Step 4 — Prepare Input Sequences

### Option A — You already have clean FASTA

Place your consensus FASTA file in `data/`, for example:

```text
data/clean_sequences.fasta
```

### Option B — Sequences are stored in Excel

Use the script below to convert an Excel file into FASTA.

Create `scripts/excel_to_fasta.py`:

```python
import pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


def excel_to_fasta(excel_path, fasta_path, id_col, seq_col, sheet_name=0):
    """
    Convert sequences from an Excel file to a FASTA file.

    Parameters:
    - excel_path: path to input Excel file
    - fasta_path: path to output FASTA file
    - id_col: column name containing sequence IDs
    - seq_col: column name containing DNA sequences
    - sheet_name: sheet name or index, default 0
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        records = []

        for index, row in df.iterrows():
            seq_id = str(row[id_col]).strip()
            sequence = str(row[seq_col]).strip()

            if not seq_id or not sequence:
                print(f"Skipping row {index + 2}: missing ID or sequence.")
                continue

            record = SeqRecord(Seq(sequence), id=seq_id, description="")
            records.append(record)

        if records:
            SeqIO.write(records, fasta_path, "fasta")
            print(f"Wrote {len(records)} sequences to {fasta_path}")
        else:
            print("No valid sequences found.")

    except FileNotFoundError:
        print(f"Error: file not found: {excel_path}")
    except KeyError as e:
        print(f"Error: column not found: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    INPUT_EXCEL = "data/sequences.xlsx"
    OUTPUT_FASTA = "data/clean_sequences.fasta"
    ID_COLUMN = "Sample_ID"
    SEQUENCE_COLUMN = "Sequence"
    SHEET = 0

    excel_to_fasta(INPUT_EXCEL, OUTPUT_FASTA, ID_COLUMN, SEQUENCE_COLUMN, SHEET)
```

Update the configuration at the bottom with your real file paths and column names.

---

## Step 5 — Run BOLDigger3 Identification

Run BOLDigger3 against the public COI species database.

Example command:

```bash
boldigger3 identify ./data/clean_sequences.fasta ./bold_db --db 1 --mode 2
```

Recommended parameters for bees and bumblebees:

| Parameter | Value | Meaning |
|---|---|---|
| `--db` | `1` | COX1_SPECIES_PUBLIC database |
| `--mode` | `2` | Genus and species search |

Other modes:

- `--mode 1` — Rapid species search, fastest
- `--mode 3` — Animal library, most thorough but slower

> Check the exact CLI flags for your BOLDigger3 version:
> ```bash
> boldigger3 identify --help
> ```

---

## Step 6 — Automate as a Python Pipeline

Create `scripts/run_bold_pipeline.py` to run the full workflow automatically.

```python
import subprocess
import os
import sys


# Paths
INPUT_EXCEL = "data/sequences.xlsx"
CLEAN_FASTA = "data/clean_sequences.fasta"
BOLD_DB_PATH = "bold_db"
RESULTS_OUTPUT_DIR = "results"


def excel_to_fasta(excel_path, fasta_path):
    """
    Optional: call your Excel-to-FASTA conversion here.
    You can import the function from excel_to_fasta.py instead.
    """
    from excel_to_fasta import excel_to_fasta as convert

    convert(
        excel_path=excel_path,
        fasta_path=fasta_path,
        id_col="Sample_ID",
        seq_col="Sequence",
        sheet_name=0,
    )


def run_bold_identification():
    os.makedirs(RESULTS_OUTPUT_DIR, exist_ok=True)

    command = [
        "boldigger3",
        "identify",
        CLEAN_FASTA,
        BOLD_DB_PATH,
        "--db", "1",
        "--mode", "2",
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        print("BOLD identification completed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error during BOLD identification:")
        print(e.stderr)
        sys.exit(1)


if __name__ == "__main__":
    print("Step 1: Converting Excel to FASTA...")
    excel_to_fasta(INPUT_EXCEL, CLEAN_FASTA)

    print("Step 2: Running BOLD identification...")
    run_bold_identification()

    print("Step 3: Pipeline finished.")
    print(f"Results are in: {RESULTS_OUTPUT_DIR}")
```

Run it from VS Code:

```bash
python scripts/run_bold_pipeline.py
```

---

## Output

BOLDigger3 writes results to the output directory. Typical output includes:

- **`.xlsx` file** — user-friendly spreadsheet with top BOLD hits
- **`.parquet` file** — efficient format for programmatic analysis
- **DuckDB database** — local database used for faster processing

The results usually contain:

- Query ID
- Matched species or genus
- Similarity percentage
- BOLD Process ID
- BIN information, when available

You can load the Excel results with pandas:

```python
import pandas as pd

df = pd.read_excel("results/your_results.xlsx")
print(df.head())
```

---

## Notes for Bees and Bumblebees

- The standard COI barcode region is amplified with **LCO1490 / HCO2198** primers.
- BOLD is well populated for many European and North American bumblebees.
- For less common bee genera or under-sampled regions, reference coverage may be sparser.
- Use the public COI species database for the broadest search:
  - `--db 1` / `COX1_SPECIES_PUBLIC`
- Pay attention to similarity scores and BIN assignments.
- A high similarity to a single BIN is a strong species-level signal.

---

## Troubleshooting

### BOLDigger3 command not found

Make sure the virtual environment is active:

```bash
pip install boldigger3
```

### Playwright error

Run:

```bash
playwright install
```

### BOLD login fails

Check your BOLD account at:
https://www.boldsystems.org

### Excel conversion fails

Check:

- The Excel file path is correct.
- The sheet name exists.
- Column names match exactly.
- Sequences contain valid DNA characters.

### BOLD identification is slow

- Use `--mode 1` for faster species-level searches.
- Make sure the local BOLD database has been downloaded.
- Avoid running multiple BOLD jobs at the same time.

---

## References

- BOLD Systems: https://www.boldsystems.org
- BOLDigger3: https://github.com/DNA-and-Natural-History-Museum-Berlin/BOLDigger3
- Biopython: https://biopython.org
- pandas: https://pandas.pydata.org

---
