"""
utils/pdf_generator.py
-----------------------
Builds a real, downloadable PDF report from the current dataset's
live analysis results (same numbers shown on screen) using reportlab.
"""
import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)

styles = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#1e293b"))
HEADING_STYLE = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1e293b"))
NORMAL_STYLE = ParagraphStyle("NormalStyle", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#475569"))


def _b64_to_image(b64_string, width=15 * cm):
    header, encoded = b64_string.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    buf = io.BytesIO(img_bytes)
    img = Image(buf)
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = width
    img.drawHeight = width * aspect
    return img


def generate_pdf_report(dataset_info, overview, columns, missing, statistics, charts):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    story = []

    story.append(Paragraph("CSV Data Analyzer Report", TITLE_STYLE))
    story.append(Paragraph(f"File: {dataset_info['original_filename']}  |  Generated report based on live analysis", NORMAL_STYLE))
    story.append(Spacer(1, 12))

    overview_data = [
        ["Total Rows", "Total Columns", "Numeric Columns", "Categorical Columns", "Missing Values"],
        [
            f"{overview['total_rows']:,}",
            f"{overview['total_columns']:,}",
            f"{overview['numeric_columns']:,}",
            f"{overview['categorical_columns']:,}",
            f"{overview['missing_values']:,}",
        ],
    ]
    t = Table(overview_data, hAlign="LEFT", colWidths=[3.3 * cm] * 5)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Column Data Types & Missing Values", HEADING_STYLE))
    if charts.get("donut"):
        story.append(_b64_to_image(charts["donut"], width=8 * cm))
    if charts.get("missing_bar"):
        story.append(_b64_to_image(charts["missing_bar"], width=15 * cm))

    story.append(PageBreak())

    story.append(Paragraph("Numeric Columns Distribution", HEADING_STYLE))
    if charts.get("boxplot"):
        story.append(_b64_to_image(charts["boxplot"], width=15 * cm))

    story.append(Paragraph("Correlation Heatmap", HEADING_STYLE))
    if charts.get("heatmap"):
        story.append(_b64_to_image(charts["heatmap"], width=12 * cm))

    if charts.get("pie"):
        story.append(Paragraph("Categorical Distribution", HEADING_STYLE))
        story.append(_b64_to_image(charts["pie"], width=11 * cm))

    story.append(PageBreak())

    story.append(Paragraph("Summary Statistics (Numeric Columns)", HEADING_STYLE))
    if statistics:
        header = ["Column", "Count", "Mean", "Std", "Min", "25%", "Median", "75%", "Max", "Missing"]
        rows = [header]
        for s in statistics:
            rows.append([
                s["column"], s["count"], s["mean"], s["std"], s["min"],
                s["p25"], s["median"], s["p75"], s["max"], s["missing"],
            ])
        stat_table = Table(rows, hAlign="LEFT", repeatRows=1)
        stat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(stat_table)
    else:
        story.append(Paragraph("No numeric columns found in this dataset.", NORMAL_STYLE))

    story.append(Spacer(1, 16))

    story.append(Paragraph("Column Details", HEADING_STYLE))
    col_header = ["Column", "Type", "Dtype", "Missing", "Missing %", "Unique"]
    col_rows = [col_header]
    for c in columns:
        col_rows.append([c["name"], c["type"], c["dtype"], c["missing"], f"{c['missing_pct']}%", c["unique"]])
    col_table = Table(col_rows, hAlign="LEFT", repeatRows=1)
    col_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(col_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
