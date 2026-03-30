# SQL Agent — Natural Language to SQL

> Ask your business database questions in plain English. Powered by Gemini AI + FastAPI + SQLite.

---

## What it does

Type a question like *"Which salesperson had the highest revenue?"* and the AI agent:
1. Converts it to a SQL query using Gemini AI
2. Runs it against the database
3. Explains the results in plain English

---

## Project Structure

```
sql-agent/
├── app.py              # FastAPI backend + Gemini AI agent
├── index.html          # Frontend UI (dark terminal theme)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container config
├── railway.json        # Railway deployment config
└── README.md
```

---

## Tables in Demo Database

| Table | Columns |
|-------|---------|
| `sales` | product, category, amount, quantity, region, sale_date, salesperson |
| `customers` | name, email, city, country, total_orders, total_spent |
| `products` | name, category, price, stock, supplier |
| `employees` | name, department, salary, hire_date, manager |

---

## Deploy on Railway (Free — Recommended)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "SQL Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sql-agent.git
git push -u origin main
```

### Step 2 — Deploy
1. Go to railway.app → Login with GitHub
2. Click New Project → Deploy from GitHub repo
3. Select your sql-agent repo
4. Go to Variables tab → Add:  GEMINI_API_KEY = your key from aistudio.google.com
5. Click Deploy → get your public URL in ~2 minutes

---

## Deploy on Hugging Face Spaces (Free — No Card)

1. Go to huggingface.co/spaces → New Space
2. Choose Docker as SDK
3. Connect your GitHub repo
4. Go to Settings → Secrets → add GEMINI_API_KEY
5. Public URL: https://YOUR_USERNAME-sql-agent.hf.space

---

## Deploy on Koyeb (Free — No Card)

1. Go to koyeb.com → Sign up
2. New App → GitHub → select repo
3. Add env var GEMINI_API_KEY
4. Deploy → public URL ready

---

## Run Locally

```bash
pip install -r requirements.txt
GEMINI_API_KEY=your_key uvicorn app:app --reload --port 8080
# Open http://localhost:8080
```

---

## Architecture

```
User (browser)
     ↓
index.html (UI)
     ↓
POST /api/query
     ↓
FastAPI (app.py)
     ↓
Gemini AI → generates SQL
     ↓
SQLite database → runs query
     ↓
Gemini AI → explains results
     ↓
JSON response → renders table + explanation
```

---

## Sample Queries to Try

- Which product had the highest total sales revenue?
- Show top 5 customers by total amount spent
- What is the average salary by department?
- Which region had the most sales?
- List all products with stock under 50
- Who is the top salesperson by total sales amount?

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Google Gemini 1.5 Flash |
| Backend | FastAPI + Python |
| Database | SQLite (in-memory demo data) |
| Frontend | Vanilla HTML/CSS/JS |
| Deployment | Docker → Railway / Hugging Face / Koyeb |

---

## PPT Slide Outline

Slide 1 — Problem & Solution
- Problem: Business users cannot query databases without knowing SQL
- Solution: AI Agent that converts plain English to SQL and explains results
- Stack: Gemini AI + FastAPI + SQLite + Railway

Slide 2 — Architecture Diagram
- Flow: User → Web UI → FastAPI → Gemini AI → SQLite → Results
- Show the 4 database tables and sample questions

Slide 3 — Demo & Outcomes
- Screenshot of running app
- 3 sample query results
- Public deployment URL