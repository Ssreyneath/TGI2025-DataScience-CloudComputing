import re
import pandas as pd
import streamlit as st
from db import init_db, insert_submission, fetch_latest

st.set_page_config(page_title="Form → Postgres", page_icon="🧾", layout="centered")

# Create table once per app start
init_db()

st.title("🧾 Form → Neon Postgres")
st.caption("Submit the form. Data is saved to Postgres and shown below.")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

with st.form("submission_form", clear_on_submit=True):
    name = st.text_input("Name", placeholder="e.g., Sokchea")
    email = st.text_input("Email", placeholder="e.g., sokchea@example.com")
    category = st.selectbox("Category", ["event", "training", "other"])
    message = st.text_area("Message / Notes", placeholder="Write something...")
    submitted = st.form_submit_button("Save to Database")

if submitted:
    name_clean = name.strip()
    email_clean = email.strip().lower()

    if not name_clean:
        st.error("Name is required.")
    elif not EMAIL_RE.match(email_clean):
        st.error("Please enter a valid email.")
    else:
        new_id = insert_submission(
            name=name_clean,
            email=email_clean,
            category=category,
            message=message.strip()
        )
        st.success(f"✅ Saved to Postgres (id={new_id})")

st.divider()
st.subheader("📄 Latest Submissions")

try:
    rows = fetch_latest(50)
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records yet. Submit the form above.")
except Exception as e:
    st.error("Could not fetch rows from the database.")
    st.code(str(e))
