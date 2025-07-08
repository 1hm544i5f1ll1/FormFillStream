````markdown
# PDF Autofill Demo

## Summary  
A Streamlit app to upload a PDF form, select a SQLite table, map fields, and auto-fill/download PDFs.

## Features  
- SQLite setup with sample `customers` table  
- PDF form field extraction  
- Interactive field-to-column mapping  
- Batch fill & download per row  

## Requirements  
- Python 3.7+  
- streamlit  
- pandas  
- pdfjinja  
- pypdf  
- pdfrw  

## Installation  
```bash
pip install streamlit pandas pdfjinja pypdf pdfrw
````

## Usage

1. Set `secrets.sqlite.path` in Streamlit or use default `demo.db`.
2. Run:

   ```bash
   streamlit run streamlit_course_app.py
   ```
3. Choose table, upload PDF form, map fields, click **Generate PDFs**.

## Code Structure

* **init\_db()**: creates & seeds `customers`
* **extract\_fields()**: reads form fields via `pdfrw`
* **fill\_pdf\_bytes()**: clones & fills PDF with `pypdf`
* **Streamlit UI**: table selector, field mapper, uploader, download buttons

## Customization

* Change `DB_PATH` or table seed data
* Adjust field-chunking logic in `extract_fields()`
* Modify UI labels/buttons in Streamlit
 