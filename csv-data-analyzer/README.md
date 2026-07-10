# CSV Data Analyzer

A real, working full-stack web app that lets you upload a CSV file and instantly get:

- Dataset overview (rows, columns, numeric/categorical counts, missing values)
- Per-column details (dtype, missing %, unique values)
- Missing values breakdown with chart
- Summary statistics (count, mean, std, min, 25/50/75%, max) for numeric columns
- Correlation heatmap + strong-correlation pairs
- Distribution charts (histograms for numeric columns, bar charts for categorical columns)
- Full paginated data preview
- One-click **downloadable PDF report** built from the exact same live analysis

Every number and chart is computed live with **pandas / matplotlib / seaborn** from
the actual uploaded CSV — nothing on screen is hard-coded demo data.

Tech stack: **HTML/CSS/JS, Python, Flask, PostgreSQL, Pandas, Matplotlib, Seaborn, ReportLab**.

---

## 1. Prerequisites

- Python 3.10+
- PostgreSQL 13+ installed and running
- pip

## 2. Set up PostgreSQL

Create the database (adjust user/password as you like):

```bash
psql -U postgres -c "CREATE DATABASE csv_analyzer_db;"
```

You don't need to run `schema.sql` manually — the Flask app creates the
`datasets` table automatically on first run. `schema.sql` is provided in
case you prefer to create it yourself.

## 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your real Postgres credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=csv_analyzer_db
DB_USER=postgres
DB_PASSWORD=your_real_password
SECRET_KEY=some-random-string
FLASK_DEBUG=True
```

## 4. Install dependencies

It's recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 5. Run the app

```bash
python app.py
```

Open your browser at **http://localhost:5000**

## 6. Try it out

A ready-to-use sample dataset is included at `sample_data/sample_dataset.csv`
(500 rows, mixed numeric/categorical columns, real missing values) — drag it
into the upload box on the Overview page to see the whole app in action.
You can also upload any CSV of your own.

---

## Project structure

```
csv-data-analyzer/
├── app.py                  # Flask app + all routes
├── config.py                # Config from environment variables
├── database.py               # SQLAlchemy db instance
├── models.py                 # Dataset model (Postgres table)
├── schema.sql                 # Optional manual SQL schema
├── requirements.txt
├── .env.example
├── utils/
│   ├── analyzer.py           # Pandas analysis functions (the "brain")
│   ├── charts.py              # Matplotlib/Seaborn chart generation
│   └── pdf_generator.py        # ReportLab PDF report builder
├── templates/                # Jinja2 HTML templates (7 pages)
├── static/
│   ├── css/style.css
│   └── js/main.js
├── sample_data/sample_dataset.csv
└── uploads/                  # Uploaded CSVs are stored here
```

## How it works

1. You upload a CSV on the Overview page (drag-and-drop or file picker).
2. Flask saves the file to `uploads/`, and records its metadata (filename,
   row/column counts, size, timestamp) in PostgreSQL via SQLAlchemy.
3. Every page load reads the *active* dataset's row from Postgres, loads the
   real CSV file from disk with pandas, and computes fresh statistics.
4. Charts are rendered server-side with matplotlib/seaborn and streamed to
   the browser as base64 PNG images — no client-side charting library needed.
5. "Download as PDF" re-runs the same analysis and charts and assembles them
   into a PDF with ReportLab, so the report always matches what's on screen.

## Pages

| Page | Route | Description |
|---|---|---|
| Overview | `/` | Dashboard combining all key stats and charts |
| Columns | `/columns` | Full column-by-column breakdown |
| Missing Values | `/missing-values` | Missing data detail + chart |
| Statistics | `/statistics` | Full summary statistics table |
| Correlations | `/correlations` | Correlation heatmap + strong pairs |
| Distributions | `/distributions` | Histogram/bar chart per column |
| Data Preview | `/data-preview` | Full paginated raw data table |

## Notes

- Max upload size is 50MB (configurable via `MAX_CONTENT_LENGTH_MB` in `.env`).
- Only `.csv` files are accepted.
- You can upload multiple datasets over time; the most recently uploaded one
  becomes "active", and previous uploads are listed for quick switching when
  no dataset is currently loaded.
- Use `/reset` (the "Remove" link in the sidebar) to delete the active dataset
  and its file.
