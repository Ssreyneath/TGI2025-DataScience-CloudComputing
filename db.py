import os
import psycopg2
import psycopg2.extras

def get_db_url():
    # Cloud concept: Configuration outside code (Secrets)
    # 1) Local/server environment variable
    url = os.environ.get("NEON_DATABASE_URL")
    if url:
        return url

    # 2) Streamlit Cloud Secrets
    try:
        import streamlit as st
        url = st.secrets.get("NEON_DATABASE_URL")
        if url:
            return url
    except Exception:
        pass

    return None

DB_URL = get_db_url()
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS submissions (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  category TEXT NOT NULL,
  message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

INSERT_SQL = """
INSERT INTO submissions (name, email, category, message)
VALUES (%s, %s, %s, %s)
RETURNING id;
"""

SELECT_LATEST_SQL = """
SELECT id, name, email, category, message, created_at
FROM submissions
ORDER BY id DESC
LIMIT %s;
"""

def get_conn():
    if not DB_URL:
        raise ValueError("NEON_DATABASE_URL is not set. Add it in Colab Secrets or os.environ.")
    return psycopg2.connect(DB_URL)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)

def insert_submission(name: str, email: str, category: str, message: str) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(INSERT_SQL, (name, email, category, message))
            new_id = cur.fetchone()[0]
            return int(new_id)

def fetch_latest(limit: int = 50):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SELECT_LATEST_SQL, (limit,))
            return cur.fetchall()
