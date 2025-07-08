import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
import json
import os
from typing import Dict, Any

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

# Initialize OpenAI client
try:
    client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))
except:
    client = None
    st.warning("Set OPENAI_API_KEY in .streamlit/secrets.toml or env var")

st.title("📊 SQLite Data Explorer with AI")

def get_database_schema(conn: sqlite3.Connection) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    schema = "Database Schema:\n"
    for table in tables:
        schema += f"\nTable: {table}\nColumns:\n"
        cursor.execute(f"PRAGMA table_info({table});")
        for col in cursor.fetchall():
            schema += f"- {col[1]} ({col[2]})\n"
        schema += "\nSample Data:\n"
        cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
        for row in cursor.fetchall():
            schema += f"{row}\n"
    return schema

# Sample datasets (same as before)
sample_datasets = {
    "Sales Data": {
        "tables": {
            "sales": {
                "columns": ["id INTEGER PRIMARY KEY","date TEXT","product TEXT","quantity INTEGER","price REAL","region TEXT"],
                "data": [
                    (1,"2023-01-01","Widget A",10,19.99,"North"),
                    (2,"2023-01-02","Widget B",5,29.99,"South"),
                    (3,"2023-01-03","Widget A",8,19.99,"East"),
                    (4,"2023-01-04","Widget C",3,39.99,"West"),
                    (5,"2023-01-05","Widget B",12,29.99,"North")
                ]
            },
            "products": {
                "columns": ["id INTEGER PRIMARY KEY","name TEXT","category TEXT","cost REAL"],
                "data": [
                    (1,"Widget A","Electronics",12.50),
                    (2,"Widget B","Electronics",18.75),
                    (3,"Widget C","Furniture",25.00)
                ]
            }
        }
    },
    "Employee Data": {
        "tables": {
            "employees": {
                "columns": ["id INTEGER PRIMARY KEY","name TEXT","department TEXT","salary REAL","hire_date TEXT"],
                "data": [
                    (1,"John Smith","Engineering",85000,"2020-01-15"),
                    (2,"Jane Doe","Marketing",72000,"2019-05-22"),
                    (3,"Bob Johnson","Engineering",92000,"2018-11-03"),
                    (4,"Alice Brown","HR",68000,"2021-02-10")
                ]
            }
        }
    }
}

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    db_name = st.text_input("Database name", "sample.db")
    dataset = st.selectbox("Load sample dataset", list(sample_datasets.keys()))
    if st.button("Initialize Database"):
        with st.spinner("Creating database..."):
            try:
                conn = sqlite3.connect(db_name)
                cur = conn.cursor()
                for tbl, td in sample_datasets[dataset]["tables"].items():
                    cur.execute(f"DROP TABLE IF EXISTS {tbl}")
                    cur.execute(f"CREATE TABLE {tbl} ({','.join(td['columns'])})")
                    cols = [c.split()[0] for c in td["columns"] if not c.startswith("id INTEGER PRIMARY KEY")]
                    ph = ",".join("?" for _ in cols)
                    cur.executemany(f"INSERT INTO {tbl} ({','.join(cols)}) VALUES ({ph})", [row[1:] for row in td["data"]])
                conn.commit()
                st.success(f"'{db_name}' initialized with {dataset}")
                st.session_state.db_initialized = True
                st.session_state.db_schema = get_database_schema(conn)
            except Exception as e:
                st.error(f"Error initializing database: {e}")
            finally:
                conn.close()

def query_database(sql: str, conn: sqlite3.Connection) -> pd.DataFrame:
    try:
        return pd.read_sql(sql, conn)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

def detect_intent(q: str, schema: str) -> Dict[str, Any]:
    # Fallback responses for common queries
    if "what data" in q.lower() or "what information" in q.lower():
        return {
            "intent": "data_query",
            "visualization_type": None,
            "explanation": "Showing available tables in the database",
            "sql_query": "SELECT name FROM sqlite_master WHERE type='table'"
        }
    elif "show me sales" in q.lower() or "sales graph" in q.lower():
        return {
            "intent": "visualization",
            "visualization_type": "bar",
            "explanation": "Showing sales by product",
            "sql_query": "SELECT product, SUM(quantity*price) as total_sales FROM sales GROUP BY product"
        }
    
    # Use AI for more complex queries if API is available
    if client:
        try:
            prompt = f"""
Database Schema:
{schema}

User Question: "{q}"

Generate a JSON response with:
- "intent": "data_query" or "visualization"
- "visualization_type": "bar", "line", "pie", or null
- "explanation": "Brief description"
- "sql_query": "SQL query"

Example response for "show sales by region":
{{
    "intent": "visualization",
    "visualization_type": "bar",
    "explanation": "Total sales by region",
    "sql_query": "SELECT region, SUM(quantity*price) as total FROM sales GROUP BY region"
}}
"""
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            response_text = res.choices[0].message.content
            # Clean the response to ensure valid JSON
            response_text = response_text[response_text.find('{'):response_text.rfind('}')+1]
            return json.loads(response_text)
        except Exception as e:
            st.error(f"AI analysis error: {e}")
    
    # Fallback if no API or error
    return {
        "intent": "data_query",
        "visualization_type": None,
        "explanation": "Basic table listing",
        "sql_query": "SELECT * FROM sqlite_master WHERE type='table'"
    }

def generate_visualization(df: pd.DataFrame, viz_type: str, title: str):
    if df.empty:
        st.warning("No data to visualize")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        if viz_type == "bar" and len(df.columns) >= 2:
            df.plot(kind="bar", x=df.columns[0], y=df.columns[1], ax=ax)
        elif viz_type == "line" and len(df.columns) >= 2:
            df.plot(kind="line", x=df.columns[0], y=df.columns[1], ax=ax)
        elif viz_type == "pie" and len(df.columns) >= 2:
            df.plot(kind="pie", y=df.columns[1], labels=df[df.columns[0]], ax=ax, autopct='%1.1f%%')
        else:
            st.dataframe(df)
            return
        
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Visualization error: {e}")
        st.dataframe(df)

# Main chat interface
st.subheader("Chat with your Database")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_q := st.chat_input("Ask a question"):
    if not st.session_state.db_initialized:
        st.warning("Initialize DB first"); st.stop()
    
    st.session_state.messages.append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.markdown(user_q)

    conn = sqlite3.connect(db_name)
    try:
        if 'db_schema' not in st.session_state:
            st.session_state.db_schema = get_database_schema(conn)

        intent = detect_intent(user_q, st.session_state.db_schema)
        df = query_database(intent['sql_query'], conn)

        with st.chat_message("assistant"):
            st.markdown(f"**Analysis:** {intent['explanation']}")
            
            if not df.empty:
                if intent['intent'] == "visualization" and intent['visualization_type']:
                    generate_visualization(df, intent['visualization_type'], user_q)
                else:
                    st.dataframe(df)
                
                with st.expander("View SQL Query"):
                    st.code(intent['sql_query'], language="sql")
            else:
                st.warning("No results found")
            
            reply = f"Analysis: {intent['explanation']}"
            if not df.empty:
                reply += f"\n\nResults:\n{df.to_markdown()}"
            st.session_state.messages.append({"role": "assistant", "content": reply})

    except Exception as e:
        st.error(f"Error processing request: {e}")
    finally:
        conn.close()

if 'db_schema' in st.session_state:
    with st.expander("View Database Schema"):
        st.text(st.session_state.db_schema)