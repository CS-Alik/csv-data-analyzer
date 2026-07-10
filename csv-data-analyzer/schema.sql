-- Run this manually only if you prefer creating the schema yourself.
-- Otherwise, the Flask app creates this table automatically on first run
-- via db.create_all() in app.py.

CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL UNIQUE,
    file_size_bytes BIGINT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    total_columns INTEGER NOT NULL DEFAULT 0,
    numeric_columns INTEGER NOT NULL DEFAULT 0,
    categorical_columns INTEGER NOT NULL DEFAULT 0,
    missing_cells INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_datasets_is_active ON datasets (is_active);
CREATE INDEX IF NOT EXISTS idx_datasets_uploaded_at ON datasets (uploaded_at);
