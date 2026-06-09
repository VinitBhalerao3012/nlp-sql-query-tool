# ============================================================
# NLP to SQL Query Tool
# Tools: Python, Google Gemini AI, SQLite, Pandas
# Author: Vinit Bhalerao
# ============================================================

import sqlite3
import pandas as pd
from google import genai
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

DB_PATH = "data/ecommerce_database.db"

# ── 1. CREATE DATABASE FROM CSV
def create_database():
    print("[1/3] Setting up E-Commerce database...")
    df = pd.read_csv("data/ecommerce_data.csv")
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("orders", conn, if_exists="replace", index=False)
    conn.close()
    print(f"    Loaded {len(df):,} records into SQLite database")

# ── 2. GENERATE SQL FROM NATURAL LANGUAGE
def generate_sql(question, schema):
    prompt = f"""
    You are an expert SQL analyst. Convert the following question into a valid SQLite SQL query.
    
    Database table: orders
    Schema: {schema}
    
    Question: {question}
    
    Rules:
    - Return ONLY the SQL query, nothing else
    - No explanations, no markdown, no backticks
    - Use valid SQLite syntax
    - Table name is always: orders
    """
    
    response = client.models.generate_content(
        model="models/gemini-2.0-flash-lite",
        contents=prompt
    )
    return response.text.strip()

# ── 3. EXECUTE SQL QUERY
def execute_query(sql):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return df, None
    except Exception as e:
        conn.close()
        return None, str(e)

# ── 4. GENERATE NATURAL LANGUAGE ANSWER
def generate_answer(question, sql, results):
    prompt = f"""
    You are a data analyst. A user asked a question and we ran a SQL query to get results.
    
    Question: {question}
    SQL Query used: {sql}
    Results: {results.to_string() if len(results) > 0 else "No results found"}
    
    Please provide a clear, concise answer in plain English.
    Keep it to 2-3 sentences maximum.
    Focus on the key insight from the data.
    """
    
    response = client.models.generate_content(
        model="models/gemini-2.0-flash-lite",
        contents=prompt
    )
    return response.text.strip()

# ── 5. GET SCHEMA
def get_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(orders)")
    columns = cursor.fetchall()
    conn.close()
    schema = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
    return schema

# ── 6. MAIN LOOP
def main():
    print("=" * 60)
    print("NLP TO SQL QUERY TOOL")
    print("Powered by Google Gemini AI + SQLite")
    print("=" * 60)
    
    # Setup database
    create_database()
    schema = get_schema()
    print(f"\n    Database ready — columns: {schema[:100]}...")
    
    print("\n" + "=" * 60)
    print("Ask questions about the E-Commerce dataset in plain English!")
    print("Type 'exit' to quit")
    print("=" * 60)
    
    while True:
        print()
        question = input("Your question: ").strip()
        
        if question.lower() == "exit":
            print("\nGoodbye!")
            break
            
        if not question:
            continue
        
        print("\n[2/3] Generating SQL query...")
        sql = generate_sql(question, schema)
        print(f"    SQL: {sql}")
        
        print("\n[3/3] Executing query...")
        results, error = execute_query(sql)
        
        if error:
            print(f"    Error: {error}")
            continue
            
        print(f"    Found {len(results)} results")
        
        if len(results) > 0:
            print("\n📊 Raw Results:")
            print(results.to_string(index=False))
        
        print("\n🤖 AI Answer:")
        answer = generate_answer(question, sql, results)
        print(f"    {answer}")
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main()