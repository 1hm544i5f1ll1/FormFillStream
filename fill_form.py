#!/usr/bin/env python3
import sqlite3
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfObject, PdfString

ANNOT_KEY      = '/Annots'
SUBTYPE_KEY    = '/Subtype'
WIDGET_SUBTYPE = '/Widget'
FIELD_KEY      = '/T'

DB_PATH    = 'demo.db'
INPUT_PDF  = 'demo_form.pdf'

def init_db():
    conn = sqlite3.connect(DB_PATH)
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

def get_records():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT first_name, last_name, email FROM customers")
    rows = cur.fetchall()
    conn.close()
    return [
        {'first_name': fn, 'last_name': ln, 'email': em}
        for fn, ln, em in rows
    ]

def fill_pdf(input_pdf, output_pdf, data):
    pdf = PdfReader(input_pdf)
    for page in pdf.pages:
        annots = page.get(ANNOT_KEY)
        if not annots: continue
        for annot in annots:
            if annot.get(SUBTYPE_KEY)==WIDGET_SUBTYPE and annot.get(FIELD_KEY):
                name = annot[FIELD_KEY][1:-1]
                if name in data:
                    val = PdfString.encode(str(data[name]))
                    annot.update(PdfDict(V=val, AS=val))
    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfObject('true')))
    PdfWriter().write(output_pdf, pdf)

def main():
    init_db()
    records = get_records()
    for i, rec in enumerate(records, 1):
        out = f'filled_{i}.pdf'
        fill_pdf(INPUT_PDF, out, rec)
        print(f'Saved {out}')

if __name__ == '__main__':
    main()
