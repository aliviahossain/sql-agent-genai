from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import sqlite3, os, json, re, csv, io
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'csv'}

client = OpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1"
)

DB = os.path.join(os.path.expanduser("~"), "business.db")

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, product TEXT, category TEXT,
        amount REAL, quantity INTEGER, region TEXT, sale_date TEXT, salesperson TEXT);
    CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, email TEXT,
        city TEXT, country TEXT, total_orders INTEGER, total_spent REAL, joined_date TEXT);
    CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category TEXT,
        price REAL, stock INTEGER, supplier TEXT);
    CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT,
        salary REAL, hire_date TEXT, manager TEXT);
    """)
    if not c.execute("SELECT COUNT(*) FROM sales").fetchone()[0]:
        c.executemany("INSERT INTO sales (product,category,amount,quantity,region,sale_date,salesperson) VALUES (?,?,?,?,?,?,?)", [
            ("Laptop Pro","Electronics",1299.99,2,"North","2024-01-15","Alice"),
            ("Wireless Mouse","Accessories",29.99,10,"South","2024-01-18","Bob"),
            ("Monitor 4K","Electronics",599.99,3,"East","2024-01-20","Alice"),
            ("Keyboard RGB","Accessories",89.99,5,"West","2024-02-01","Charlie"),
            ("MacBook Air","Electronics",1099.99,1,"North","2024-02-05","Bob"),
            ("USB Hub","Accessories",39.99,8,"South","2024-02-10","Alice"),
            ("Headphones Pro","Audio",249.99,4,"East","2024-02-14","Charlie"),
            ("Webcam HD","Electronics",79.99,6,"West","2024-03-01","Bob"),
            ("Desk Lamp","Office",49.99,12,"North","2024-03-05","Alice"),
            ("iPad Mini","Electronics",499.99,2,"South","2024-03-10","Charlie"),
            ("Standing Desk","Furniture",799.99,1,"East","2024-03-15","Bob"),
            ("Chair Ergonomic","Furniture",499.99,2,"West","2024-03-20","Alice"),
            ("Speakers Bluetooth","Audio",129.99,7,"North","2024-04-01","Charlie"),
            ("External SSD","Storage",119.99,9,"South","2024-04-05","Bob"),
            ("Smart Watch","Electronics",349.99,3,"East","2024-04-10","Alice"),
        ])
    if not c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]:
        c.executemany("INSERT INTO customers (name,email,city,country,total_orders,total_spent,joined_date) VALUES (?,?,?,?,?,?,?)", [
            ("Priya Sharma","priya@example.com","Mumbai","India",12,4599.88,"2023-01-10"),
            ("James Wilson","james@example.com","New York","USA",8,3200.50,"2023-02-15"),
            ("Chen Wei","chen@example.com","Shanghai","China",15,6750.25,"2022-11-20"),
            ("Sofia Garcia","sofia@example.com","Madrid","Spain",5,1890.00,"2023-05-08"),
            ("Raj Patel","raj@example.com","Delhi","India",20,9100.75,"2022-08-30"),
            ("Emma Brown","emma@example.com","London","UK",7,2450.30,"2023-03-22"),
            ("Ahmed Hassan","ahmed@example.com","Cairo","Egypt",3,980.00,"2023-07-14"),
            ("Yuki Tanaka","yuki@example.com","Tokyo","Japan",18,7800.60,"2022-06-05"),
        ])
    if not c.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        c.executemany("INSERT INTO products (name,category,price,stock,supplier) VALUES (?,?,?,?,?)", [
            ("Laptop Pro","Electronics",1299.99,45,"TechCorp"),
            ("MacBook Air","Electronics",1099.99,30,"Apple"),
            ("Monitor 4K","Electronics",599.99,60,"Samsung"),
            ("Headphones Pro","Audio",249.99,120,"Sony"),
            ("Standing Desk","Furniture",799.99,25,"IKEA"),
            ("Chair Ergonomic","Furniture",499.99,40,"Herman Miller"),
            ("External SSD","Storage",119.99,200,"Samsung"),
            ("Smart Watch","Electronics",349.99,85,"Apple"),
        ])
    if not c.execute("SELECT COUNT(*) FROM employees").fetchone()[0]:
        c.executemany("INSERT INTO employees (name,department,salary,hire_date,manager) VALUES (?,?,?,?,?)", [
            ("Alice Johnson","Sales",75000,"2021-03-15","Director Smith"),
            ("Bob Martinez","Sales",68000,"2021-07-20","Director Smith"),
            ("Charlie Lee","Sales",72000,"2022-01-10","Director Smith"),
            ("Diana Prince","Engineering",95000,"2020-05-01","CTO Rogers"),
            ("Ethan Hunt","Engineering",88000,"2021-09-15","CTO Rogers"),
            ("Fiona Green","Marketing",65000,"2022-03-01","VP Marketing"),
            ("George Hill","Finance",78000,"2020-11-20","CFO Davis"),
            ("Hannah White","HR",62000,"2023-01-05","Director Smith"),
        ])
    conn.commit()
    conn.close()

init_db()

def get_schema():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    schema = {}
    for (t,) in tables:
        cols = c.execute(f"PRAGMA table_info({t})").fetchall()
        schema[t] = [{"name": col[1], "type": col[2]} for col in cols]
    conn.close()
    return schema

def run_sql(query):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute(query)
        rows = c.fetchall()
        cols = [d[0] for d in c.description] if c.description else []
        data = [dict(r) for r in rows]
        conn.close()
        return {"success": True, "columns": cols, "data": data, "count": len(data)}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def root():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.route("/api/health")
def health_check():
    try:
        test_response = client.chat.completions.create(
            model="mistral",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=10
        )
        return jsonify({"status": "healthy", "ollama": "running"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "ollama": "not running", "error": str(e)}), 503

@app.route("/api/schema")
def api_schema():
    try:
        return jsonify(get_schema())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/suggestions")
def api_suggestions():
    return jsonify([
        "Which product had the highest total sales revenue?",
        "Show top 5 customers by total amount spent",
        "What is the average salary by department?",
        "Which region had the most sales?",
        "List all products with stock under 50",
        "Who is the top salesperson by total sales amount?",
        "Show sales grouped by category with total revenue",
        "Which country has the most customers?",
    ])

@app.route("/api/query", methods=["POST"])
def query_agent():
    data = request.get_json()
    question = data.get("question", "")
    schema = get_schema()
    schema_text = "\n\n".join([
        f"Table: {t}\nColumns: " + ", ".join([f"{col['name']} ({col['type']})" for col in cols])
        for t, cols in schema.items()
    ])
    prompt = f"""You are a SQL expert. Convert this question into a valid SQLite SELECT query.

Schema:
{schema_text}

Question: {question}

Return ONLY the SQL query. No markdown, no explanation, no backticks."""

    try:
        response = client.chat.completions.create(
            model="mistral",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        sql = re.sub(r'```sql|```', '', response.choices[0].message.content.strip()).strip()
        result = run_sql(sql)

        if not result["success"]:
            fix = f"Fix this SQLite SQL: {sql}\nError: {result['error']}\nReturn only fixed SQL."
            fix_response = client.chat.completions.create(
                model="mistral",
                messages=[{"role": "user", "content": fix}],
                temperature=0
            )
            sql = re.sub(r'```sql|```', '', fix_response.choices[0].message.content.strip()).strip()
            result = run_sql(sql)

        explanation = ""
        if result["success"] and result["data"]:
            ep = f'Question: "{question}"\nSQL: {sql}\nSample: {json.dumps(result["data"][:3])}\nRows: {result["count"]}\nExplain in 1-2 sentences with numbers.'
            exp_response = client.chat.completions.create(
                model="mistral",
                messages=[{"role": "user", "content": ep}],
                temperature=0
            )
            explanation = exp_response.choices[0].message.content.strip()
        elif result["success"]:
            explanation = "The query returned no results."

        return jsonify({"sql": sql, "result": result, "explanation": explanation})
    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "localhost:11434" in error_msg:
            return jsonify({"error": "Ollama is not running. Please start Ollama with: ollama run mistral"}), 503
        return jsonify({"error": f"AI service error: {error_msg}"}), 500

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    table_name = request.form.get('table_name', '').strip()

    if not table_name:
        return jsonify({"error": "Table name is required"}), 400

    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        return jsonify({"error": "Table name can only contain letters, numbers, and underscores, and must start with a letter or underscore"}), 400

    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only CSV files are supported. Please upload a .csv file"}), 400

    try:
        raw = file.read()
        # Try UTF-8 with BOM first, then fallback to latin-1
        try:
            content = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            content = raw.decode('latin-1')

        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        if not rows:
            return jsonify({"error": "The CSV file is empty or has no data rows"}), 400

        cols = list(reader.fieldnames)
        if not cols:
            return jsonify({"error": "Could not detect column headers in the CSV"}), 400

        if len(rows) > 100000:
            return jsonify({"error": "File exceeds 100,000 row limit"}), 400

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        # Drop existing table with same name and recreate
        c.execute(f'DROP TABLE IF EXISTS "{table_name}"')

        # Create table — all columns as TEXT; user can cast in SQL
        col_defs = ", ".join(f'"{col.strip()}" TEXT' for col in cols)
        c.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

        placeholders = ", ".join("?" * len(cols))
        clean_cols = [col.strip() for col in cols]
        c.executemany(
            f'INSERT INTO "{table_name}" VALUES ({placeholders})',
            [tuple(row.get(col, '') for col in cols) for row in rows]
        )

        conn.commit()
        conn.close()

        return jsonify({
            "rows": len(rows),
            "columns": clean_cols,
            "table": table_name
        })

    except csv.Error as e:
        return jsonify({"error": f"CSV parsing error: {str(e)}"}), 400
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route("/api/detect-chart", methods=["POST"])
def detect_chart():
    data = request.get_json()
    result = data.get("result", {})

    if not result.get("success") or not result.get("data"):
        return jsonify({"chart_type": None})

    rows = result["data"]
    columns = result["columns"]

    if len(columns) == 2 and len(rows) <= 50:
        first_col_vals = [row.get(columns[0]) for row in rows]
        second_col_vals = [row.get(columns[1]) for row in rows]
        numeric_count = sum(1 for v in second_col_vals if isinstance(v, (int, float)))
        if numeric_count >= len(rows) * 0.8:
            chart_data = {
                "type": "bar",
                "labels": [str(v) for v in first_col_vals],
                "datasets": [{
                    "label": columns[1],
                    "data": [float(v) if isinstance(v, (int, float)) else 0 for v in second_col_vals],
                    "backgroundColor": "rgba(0, 212, 170, 0.6)",
                    "borderColor": "rgba(0, 212, 170, 1)",
                    "borderWidth": 1
                }]
            }
            return jsonify({"chart_type": "bar", "chart_data": chart_data})

    return jsonify({"chart_type": None})

if __name__ == "__main__":
    app.run(debug=True, port=8080)