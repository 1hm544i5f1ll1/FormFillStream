#!/usr/bin/env python3
import io
import sqlite3
import tempfile
import streamlit as st
import pandas as pd
from pdfjinja import PdfJinja
import io
from pypdf import PdfReader, PdfWriter

st.title("PDF Autofill Demo")

DB_PATH = st.secrets.get("sqlite", {}).get("path", "demo.db")
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT
      )""")
    cur.execute("""
      INSERT OR IGNORE INTO customers VALUES
        (1,'Alice','Smith','alice@example.com'),
        (2,'Bob','Jones','bob@example.com')
    """)
    conn.commit()
    conn.close()

init_db()

def fill_pdf_bytes(template_bytes, data):
    # read the uploaded PDF
    reader = PdfReader(io.BytesIO(template_bytes))
    # clone everything (pages, AcroForm, etc.)
    writer = PdfWriter(clone_from=reader)
    # let the viewer regenerate field appearances
    writer.set_need_appearances_writer(True)  # :contentReference[oaicite:0]{index=0}
    # fill each page’s form fields
    for page in writer.pages:
        writer.update_page_form_field_values(page, data)  # :contentReference[oaicite:1]{index=1}
    # write out to a buffer
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf

tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", get_conn())['name']
table = st.selectbox("Choose table:", tables)
if not table:
    st.stop()

df = pd.read_sql(f"SELECT * FROM {table}", get_conn())
st.dataframe(df)

uploaded = st.file_uploader("Upload PDF form", type="pdf")
if not uploaded or df.empty:
    st.stop()

template = uploaded.read()

def extract_fields(pdf_bytes):
    from pdfrw import PdfReader
    FIELD_KEY = '/T'
    SUBTYPE_KEY = '/Subtype'
    WIDGET_SUBTYPE = '/Widget'
    ANNOT_KEY = '/Annots'
    PARENT_KEY = '/Parent'

    pdf = PdfReader(fdata=pdf_bytes)
    names = set()

    # fields via AcroForm
    if hasattr(pdf.Root, 'AcroForm') and hasattr(pdf.Root.AcroForm, 'Fields'):
        for f in pdf.Root.AcroForm.Fields or []:
            if f.get(FIELD_KEY):
                names.add(f[FIELD_KEY][1:-1])

    # annotations
    for p in pdf.pages:
        for ann in (p[ANNOT_KEY] or []):
            if ann.get(SUBTYPE_KEY)==WIDGET_SUBTYPE:
                fld = ann
                if FIELD_KEY not in fld and PARENT_KEY in fld:
                    fld = fld[PARENT_KEY]
                if fld.get(FIELD_KEY):
                    names.add(fld[FIELD_KEY][1:-1])
    return sorted(names)

fields = extract_fields(template)
if not fields:
    st.error("No form fields detected.")
    st.stop()

st.write("Detected fields:", fields)

mapping = {}
with st.expander("Field Mapping"):
    for f in fields:
        opts = [""] + [c for c in df.columns if c!="id"]
        mapping[f] = st.selectbox(f, opts, index=opts.index(f) if f in opts else 0, key=f)

if st.button("Generate PDFs"):
    for i, row in df.iterrows():
        data = {f: row[mapping[f]] for f in fields if mapping[f]}
        if not data:
            st.warning(f"No data for row {i+1}")
            continue
        buf = fill_pdf_bytes(template, data)
        fname = f"{table}_row{i+1}.pdf"
        st.download_button(f"Download #{i+1}", buf, file_name=fname, mime="application/pdf")
    st.success("Done!")
