import os
import uuid
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, jsonify, abort
)
from werkzeug.utils import secure_filename

from config import Config
from database import db
from models import Dataset
from utils import analyzer, charts as chart_utils
from utils.pdf_generator import generate_pdf_report

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def get_active_dataset():
    return Dataset.query.filter_by(is_active=True).order_by(Dataset.uploaded_at.desc()).first()


def get_active_dataframe():
    dataset = get_active_dataset()
    if dataset is None:
        return None, None
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], dataset.stored_filename)
    if not os.path.exists(filepath):
        return dataset, None
    df = analyzer.load_dataframe(filepath)
    return dataset, df


def recent_datasets(limit=5):
    return Dataset.query.order_by(Dataset.uploaded_at.desc()).limit(limit).all()


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    if "csv_file" not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("overview"))

    file = request.files["csv_file"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("overview"))

    if not allowed_file(file.filename):
        flash("Only .csv files are supported.", "error")
        return redirect(url_for("overview"))

    original_filename = secure_filename(file.filename)
    stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(filepath)

    try:
        df = analyzer.load_dataframe(filepath)
    except Exception as exc:
        os.remove(filepath)
        flash(f"Could not parse this CSV file: {exc}", "error")
        return redirect(url_for("overview"))

    overview_stats = analyzer.get_overview(df)
    file_size = os.path.getsize(filepath)

    # deactivate previous datasets
    Dataset.query.update({Dataset.is_active: False})

    dataset = Dataset(
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size_bytes=file_size,
        total_rows=overview_stats["total_rows"],
        total_columns=overview_stats["total_columns"],
        numeric_columns=overview_stats["numeric_columns"],
        categorical_columns=overview_stats["categorical_columns"],
        missing_cells=overview_stats["missing_values"],
        is_active=True,
        uploaded_at=datetime.utcnow(),
    )
    db.session.add(dataset)
    db.session.commit()

    flash(f"'{original_filename}' uploaded and analyzed successfully.", "success")
    return redirect(url_for("overview"))


@app.route("/switch-dataset/<int:dataset_id>")
def switch_dataset(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    Dataset.query.update({Dataset.is_active: False})
    dataset.is_active = True
    db.session.commit()
    flash(f"Switched to '{dataset.original_filename}'.", "success")
    return redirect(url_for("overview"))


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def overview():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        return render_template("overview.html", dataset=None, recent=recent_datasets())

    ov = analyzer.get_overview(df)
    columns = analyzer.get_column_details(df)
    missing = analyzer.get_missing_values(df)
    statistics = analyzer.get_statistics(df)
    corr, numeric_cols = analyzer.get_correlation_matrix(df)
    cat_dist = analyzer.get_categorical_distribution(df)
    preview = analyzer.get_preview(df, page=1, per_page=5)

    chart_data = {
        "donut": chart_utils.column_type_donut(ov["numeric_columns"], ov["categorical_columns"]),
        "missing_bar": chart_utils.missing_values_bar(missing["columns"]),
        "boxplot": chart_utils.numeric_boxplot(df, ov["numeric_col_names"]),
        "heatmap": chart_utils.correlation_heatmap(corr),
        "pie": chart_utils.categorical_pie(cat_dist),
    }

    return render_template(
        "overview.html",
        dataset=dataset,
        overview=ov,
        columns=columns,
        missing=missing,
        statistics=statistics,
        preview=preview,
        charts=chart_data,
        recent=recent_datasets(),
    )


@app.route("/columns")
def columns_page():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        return redirect(url_for("overview"))
    columns = analyzer.get_column_details(df)
    ov = analyzer.get_overview(df)
    return render_template("columns.html", dataset=dataset, columns=columns, overview=ov)


@app.route("/missing-values")
def missing_values_page():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        return redirect(url_for("overview"))
    missing = analyzer.get_missing_values(df)
    chart = chart_utils.missing_values_bar(missing["columns"], limit=30)
    return render_template("missing_values.html", dataset=dataset, missing=missing, chart=chart)


@app.route("/statistics")
def statistics_page():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        return redirect(url_for("overview"))
    statistics = analyzer.get_statistics(df)
    return render_template("statistics.html", dataset=dataset, statistics=statistics)


@app.route("/correlations")
def correlations_page():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        return redirect(url_for("overview"))
    corr, numeric_cols = analyzer.get_correlation_matrix(df)
    heatmap = chart_utils.correlation_heatmap(corr)

    strong_pairs = []
    if corr is not None:
        for i, col_a in enumerate(corr.columns):
            for j, col_b in enumerate(corr.columns):
                if j <= i:
                    continue
                val = corr.loc[col_a, col_b]
                if abs(val) >= 0.5:
                    strong_pairs.append({"a": col_a, "b": col_b, "value": round(float(val), 2)})
        strong_pairs.sort(key=lambda x: abs(x["value"]), reverse=True)

    return render_template(
        "correlations.html", dataset=dataset, heatmap=heatmap,
        numeric_cols=numeric_cols, strong_pairs=strong_pairs,
    )


@app.route("/distributions")
def distributions_page():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        return redirect(url_for("overview"))
    numeric_cols, categorical_cols = analyzer.get_column_types(df)

    numeric_charts = [{"column": c, "img": chart_utils.distribution_histogram(df, c)} for c in numeric_cols]
    categorical_charts = [{"column": c, "img": chart_utils.categorical_bar(df, c)} for c in categorical_cols[:6]]

    return render_template(
        "distributions.html", dataset=dataset,
        numeric_charts=numeric_charts, categorical_charts=categorical_charts,
    )


@app.route("/data-preview")
def data_preview_page():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        return redirect(url_for("overview"))
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 15, type=int)
    preview = analyzer.get_preview(df, page=page, per_page=per_page)
    return render_template("data_preview.html", dataset=dataset, preview=preview)


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

@app.route("/download-pdf")
def download_pdf():
    dataset, df = get_active_dataframe()
    if dataset is None or df is None:
        flash("Upload a CSV file before downloading a report.", "error")
        return redirect(url_for("overview"))

    ov = analyzer.get_overview(df)
    columns = analyzer.get_column_details(df)
    missing = analyzer.get_missing_values(df)
    statistics = analyzer.get_statistics(df)
    corr, numeric_cols = analyzer.get_correlation_matrix(df)
    cat_dist = analyzer.get_categorical_distribution(df)

    chart_data = {
        "donut": chart_utils.column_type_donut(ov["numeric_columns"], ov["categorical_columns"]),
        "missing_bar": chart_utils.missing_values_bar(missing["columns"]),
        "boxplot": chart_utils.numeric_boxplot(df, ov["numeric_col_names"]),
        "heatmap": chart_utils.correlation_heatmap(corr),
        "pie": chart_utils.categorical_pie(cat_dist),
    }

    pdf_buffer = generate_pdf_report(dataset.to_dict(), ov, columns, missing, statistics, chart_data)

    filename = f"{os.path.splitext(dataset.original_filename)[0]}_report.pdf"
    return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)


# ---------------------------------------------------------------------------
# Reset / delete
# ---------------------------------------------------------------------------

@app.route("/reset")
def reset_dataset():
    dataset = get_active_dataset()
    if dataset:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], dataset.stored_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(dataset)
        db.session.commit()
        flash("Dataset removed.", "success")
    return redirect(url_for("overview"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found"), 404


@app.errorhandler(413)
def too_large(e):
    flash("File is too large. Max upload size is 50MB.", "error")
    return redirect(url_for("overview"))


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Something went wrong on our end"), 500


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)
