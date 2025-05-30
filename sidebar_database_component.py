import streamlit as st
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine, inspect
import tempfile
import pandas as pd
import os
import sqlite3

def create_temp_db_from_uploaded_db(uploaded_file) -> str:
    """Save uploaded .db file to a temp file and return SQLite URI."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp.write(uploaded_file.read())
        return f"sqlite:///{tmp.name}"

def create_temp_db_from_csv(uploaded_file) -> str:
    """Convert CSV to SQLite temp DB and return URI."""
    df = pd.read_csv(uploaded_file)
    if df.empty:
        st.sidebar.error("CSV is empty or invalid.")
        st.stop()

    # Use the uploaded filename (without extension) as the table name
    filename = uploaded_file.name
    table_name = os.path.splitext(filename)[0].replace(" ", "_").replace("-", "_")

    # Use a unique temp file name to avoid conflicts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp_db_path = tmp.name

    conn = sqlite3.connect(tmp_db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    return f"sqlite:///{tmp_db_path}"

def sidebar_database_choice():

    st.sidebar.subheader("📊 Database Source")

    db_choice = st.sidebar.radio(
        "Select database source",
        options=["Use default database", "Upload your own (.db)", "Upload a CSV file"],
        index=0
    )

    db_uri = None
    db_label = None
    uploaded_file = None

    if db_choice == "Use default database":
        db_uri = 'sqlite:///data/SuperStore.db'
        db_label = "Default SuperStore.db"

    elif db_choice == "Upload your own (.db)":
        uploaded_file = st.sidebar.file_uploader("Upload SQLite DB file", type=["db"])
        if uploaded_file:
            try:
                db_uri = create_temp_db_from_uploaded_db(uploaded_file)
                db_label = "Uploaded SQLite DB"
            except Exception as e:
                st.sidebar.error(f"Failed to load DB file: {e}")
                st.stop()

    elif db_choice == "Upload a CSV file":
        uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file:
            try:
                db_uri = create_temp_db_from_csv(uploaded_file)
                db_label = f"CSV: {uploaded_file.name.split('.')[0]}"
            except Exception as e:
                st.sidebar.error(f"Failed to process CSV: {e}")
                st.stop()

    # Load the database connection
    if db_uri:
        try:
            db = SQLDatabase.from_uri(db_uri)
            engine = create_engine(db_uri)
            inspector = inspect(engine)
        except Exception as e:
            st.sidebar.error(f"Failed to connect to database: {e}")
            st.stop()
    else:
        st.sidebar.warning("Please select or upload to proceed.")
        st.stop()

    # Sidebar: Display tables from the database
    with st.sidebar:
        st.markdown("### 📂 Tables in Database")
        try:
            table_names = db.get_table_names()
            if table_names:
                for table in table_names:
                    st.markdown(f"- {table}")
                if len(table_names) == 1:
                    columns = inspector.get_columns(table)
                    st.markdown(f"### 📂 Top 5 Columns in {table}")
                    for col in columns[:5]:
                        st.markdown(f"  - `{col['name']}` ({col['type']})")
            else:
                st.markdown("_No tables found in database._")
        except Exception as e:
            st.markdown(f"❌ Error loading tables: {e}")

    return db