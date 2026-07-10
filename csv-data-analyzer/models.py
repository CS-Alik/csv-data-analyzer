from datetime import datetime
from database import db


class Dataset(db.Model):
    """
    Stores metadata about every CSV file a user has uploaded.
    The raw CSV itself lives on disk (uploads/) and is analyzed live
    with pandas on every request -- nothing about the analysis is
    pre-baked or fake, it is always computed from the real file.
    """
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_size_bytes = db.Column(db.BigInteger, nullable=False)

    total_rows = db.Column(db.Integer, nullable=False, default=0)
    total_columns = db.Column(db.Integer, nullable=False, default=0)
    numeric_columns = db.Column(db.Integer, nullable=False, default=0)
    categorical_columns = db.Column(db.Integer, nullable=False, default=0)
    missing_cells = db.Column(db.Integer, nullable=False, default=0)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_size_bytes": self.file_size_bytes,
            "file_size_mb": round(self.file_size_bytes / (1024 * 1024), 2),
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "missing_cells": self.missing_cells,
            "uploaded_at": self.uploaded_at.strftime("%b %d, %Y %I:%M %p"),
        }
