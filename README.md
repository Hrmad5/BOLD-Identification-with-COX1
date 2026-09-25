# Bee and Bumblebee COI Identification Pipeline

A Python-based workflow for identifying bee and bumblebee species from COI sequences using **BOLDigger3** against the BOLD reference database — run entirely from a **Jupyter notebook** inside VS Code.

---

## Overview

This notebook (`run_bold_identification.ipynb`) handles the final stage of a DNA barcoding pipeline:

1. Convert sequences stored in Excel into a clean FASTA file.
2. Query BOLD's identification engine with **BOLDigger3**.
3. Write results to a local output directory for downstream analysis.

The pipeline assumes that AB1 → consensus FASTA processing has already been done, and that sequences are ready as either a FASTA file or an Excel sheet.

---

## Project Structure

The notebook was written with the following layout in mind:

```text
bompar_project/
├── .venv/
├── bold_db/
│   └── BOLD_Public.11-Sep-2026.ddb
├── data/
│   ├── sequence_data.xlsx
│   └── sequence_data.fasta
├── notebooks/
│   └── run_bold_identification.ipynb     <- this notebook
└── README.md
```

The notebook uses **relative paths** (`../data/`, `../bold_db/`) for most operations, so it assumes it lives in a subfolder of the project (e.g., `notebooks/`). If you place the notebook elsewhere, adjust the paths in the configuration cell accordingly.

---

## Requirements

- Python **3.11 or higher** (tested with 3.12.3)
- VS Code with the **Jupyter extension**
- Free BOLD account: https://www.boldsystems.org
- Input: either
  - an Excel file with at least two columns (sample ID + sequence), or
  - a pre-made FASTA file

---

## Step 1 — Set Up the Environment

Open a terminal in VS Code and create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

Then, in VS Code:

1. Install the **Jupyter extension** from the Extensions panel.
2. Select the `.venv` interpreter: `Ctrl+Shift+P` → `Python: Select Interpreter`.
3. Open `run_bold_identification.ipynb`. The kernel picker (top-right) should show `.venv`.

---

## Step 2 — Notebook Walkthrough

Run the cells top-to-bottom. Each section below corresponds to a cell in the notebook.

### Cell 1 — Install packages (once)

```python
%pip install boldigger3 pandas biopython openpyxl
```

**After running this cell, restart the kernel:**
`Ctrl+Shift+P` → `Kernel: Restart Kernel`

This is required so the newly installed packages become importable in the current session.

### Cell 2 — Install Playwright browser (once)

```python
!playwright install
```

BOLDigger3 uses Playwright under the hood to interact with BOLD.

### Cell 3 — Create directories (once)

```python
!mkdir -p /home/hommurat/sanger_data_analysis_pipeline/bompar_project/data
!mkdir -p /home/hommurat/sanger_data_analysis_pipeline/bompar_project/bold_db
```

Creates the `data/` and `bold_db/` folders inside the project. Edit the absolute paths to match your machine.

### Cell 4 — Download the BOLD database (once)

```python
!boldigger3 download --db /home/hommurat/sanger_data_analysis_pipeline/bompar_project/bold_db
```

You will be prompted for your BOLD username and password. Register for a free account at https://www.boldsystems.org.

The database will be downloaded into the specified folder and converted into a local `.ddb` file (DuckDB) for fast offline lookups.

> **Note:** The `--db` flag here specifies the *output location* of the download. This is different from the `--db` flag in the `identify` command (see below), where it selects *which* database to query. This is a BOLDigger3-specific quirk.

### Cell 5 — Imports and configuration

```python
INPUT_EXCEL     = "../data/sequence_data.xlsx"
ID_COLUMN       = "Sample_ID"
SEQUENCE_COLUMN = "Sequence"
SHEET           = "Sheet1"
CLEAN_FASTA     = "../data/sequence_data.fasta"
BOLD_DB_PATH    = "../bold_db/BOLD_Public.11-Sep-2026.ddb"
```

Edit these to match your files. Everything downstream uses these variables, so you only update paths and column names here.

### Cell 6 — `excel_to_fasta` function

Defines a helper that reads an Excel sheet, iterates over rows, and writes valid records to FASTA. Rows with an empty ID or sequence are skipped with a warning. Errors (missing file, missing columns, etc.) are logged rather than raised, so the notebook keeps running.

### Cell 7 — Convert Excel to FASTA

```python
excel_to_fasta(INPUT_EXCEL, CLEAN_FASTA, ID_COLUMN, SEQUENCE_COLUMN, SHEET)
```

Skip this cell if your input is already a clean FASTA file.

### Cell 8 — Run BOLD identification (Option A — simple bash call)

```python
!boldigger3 identify ../data/sequence_data.fasta ../bold_db/BOLD_Public.11-Sep-2026.ddb --db 1 --mode 2
```

This is the simplest way to run the identification. It runs the CLI directly through the notebook's shell.

### Cell 9 — Run BOLD identification (Option B — Python subprocess)

```python
command = [
    "boldigger3", "identify",
    CLEAN_FASTA,
    BOLD_DB_PATH,
    "--db", "2",
    "--mode", "2"
]

try:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    logging.info("BOLD identification completed successfully.")
    logging.info(result.stdout)
except subprocess.CalledProcessError as e:
    logging.error(f"Error during BOLD identification: {e}.")
    logging.error(e.stderr)
    sys.exit(1)
```

This version uses `subprocess.run()` and the config variables, making it easier to integrate into a larger script. **You only need to run one of the two options — not both.**

> ⚠️ **Important:** The two options currently use different `--db` values (`1` in Option A, `2` in Option B). These correspond to different reference databases in BOLD. Decide which one fits your project and use the same value in both cells, or delete the one you don't use.

### Understanding the key flags

| Flag | Purpose | Common values |
|---|---|---|
| `--db` | Selects which BOLD reference database to query | `1`, `2`, `3` (see BOLDigger3 docs) |
| `--mode` | Selects search depth | `1` (fast) · `2` (balanced) · `3` (thorough) |

For bees and bumblebees, `--mode 2` is a good default: it is faster than full-library searches while remaining reliable for well-sampled groups.

Check the exact flags for your version with:

```python
!boldigger3 identify --help
```

---

## Output

Results from BOLDigger3 are written under:

```text
data/boldigger3_data/
```

Typical output includes:

- **`.xlsx`** — top-hit table, easy to open in Excel
- **`.parquet`** — efficient format for programmatic analysis
- Supporting files in the same directory (DuckDB cache, logs, etc.)

The results typically contain:

- Query ID
- Matched species or genus
- Similarity percentage
- BOLD Process ID
- BIN assignment (when available)

Load the `.xlsx` output with pandas to filter, summarize, or plot:

```python
import pandas as pd
df = pd.read_excel("data/boldigger3_data/<your_results>.xlsx")
df.head()
```

---

## Notes for Bees and Bumblebees

- The COI barcode region is usually amplified with **LCO1490 / HCO2198** primers.
- BOLD is well populated for European and North American bumblebees (`Bombus`).
- For less common bee genera or under-sampled regions, reference coverage may be sparser.
- Pay attention to:
  - **Similarity scores** — high similarity to a single reference is a strong signal.
  - **BIN assignments** — clusters of sequences that often correspond to species.
- If you see unexpected hits (e.g., *Wolbachia* or NUMTs), verify your primers and consider filtering those references out.

---

## About YAML and "Pipelines"

YAML is not the universal format for pipelines — it is used by *some* tools (CWL, Galaxy, GitHub Actions), but plenty of pipeline systems do not use it.

| Tool | Format | Typical use |
|---|---|---|
| Snakemake | Python-based `Snakefile` | Bioinformatics, HPC |
| Nextflow | Groovy DSL | Large-scale bioinformatics, cloud |
| CWL | YAML | Portable workflows, HPC |
| GitHub Actions / CI | YAML | Automation, testing |
| Airflow / Prefect | Python | Data engineering |
| **Jupyter notebook** | Python | Analysis, small/medium pipelines |

A "pipeline" simply means *a sequence of steps that runs in order*. This notebook **is** your pipeline. You do not need YAML.

**When to move to a workflow manager:**

1. You have **>50 samples** and want parallel execution.
2. You want to skip already-processed samples and re-run only failures.
3. You need to run on a cluster or the cloud.
4. You need publication-grade provenance.
5. Several people must run the same pipeline.

At that point, **Snakemake** is the easiest next step for a Python user. You would write a `Snakefile` in Python-like syntax, not YAML.

---

## Troubleshooting

### "boldigger3: command not found"

Make sure the notebook's kernel is using the same environment where BOLDigger3 was installed. Check:

```python
import sys
print(sys.executable)
```

The path should point inside `.venv`.

### Playwright errors on the first run

Run once:

```python
!playwright install
```

On some systems you may also need:

```bash
playwright install-deps
```

### BOLD login fails

Check your BOLD account at https://www.boldsystems.org. BOLDigger3 will prompt for credentials when downloading the database.

### `FileNotFoundError` on the Excel or FASTA file

- Confirm the notebook is in the folder you expect.
- Confirm that `../data/` resolves correctly relative to the notebook location.
- Use `!pwd` and `!ls ../data` in a cell to debug.

### "No valid sequences found to write"

The Excel parser found every row empty or invalid. Check:

- Column names match `ID_COLUMN` and `SEQUENCE_COLUMN` exactly.
- The sheet name matches `SHEET`.
- Sequences contain valid DNA characters (A, T, G, C).

### Kernel dies or "module not found" after install

Restart the kernel after `%pip install`:

`Ctrl+Shift+P` → `Kernel: Restart Kernel`

### Identification is very slow

- Use `--mode 1` for faster (less thorough) species-level searches.
- Make sure the local `.ddb` database has finished downloading.
- Do not run multiple BOLD jobs at the same time.

---

## References

- BOLD Systems — https://www.boldsystems.org
- BOLDigger3 — https://github.com/DNA-and-Natural-History-Museum-Berlin/BOLDigger3
- Biopython — https://biopython.org
- pandas — https://pandas.pydata.org
- VS Code Jupyter docs — https://code.visualstudio.com/docs/datascience/jupyter-notebooks