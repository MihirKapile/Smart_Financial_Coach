# Elite Financial Intelligence Coach 💬

An AI-powered personal finance analysis and coaching application built with Streamlit, Groq LLMs, and Agno Agents. The app ingests raw transaction files (CSV/XLSX), analyzes real spending behavior, and produces an in-depth, persona-driven financial intelligence report with visual dashboards and a downloadable audit PDF.

---

## 🚀 Key Features

* Persona-based AI Financial Advisors

  * Conservative Advisor: Risk-averse, capital-protection focused
  * Fun Saver: High-energy, motivational, emoji-driven
  * Analytical Guru: Quant-heavy, anomaly and trend focused

* Smart Transaction Ingestion

  * Accepts CSV or Excel files with flexible column names
  * Automatically detects date, amount, and category fields
  * Handles messy, real-world bank exports

* Deep Financial Intelligence

  * 90-day rolling spend analysis
  * Monthly savings velocity and feasibility scoring
  * Savings gap detection vs goal
  * Recurring subscription leakage detection
  * Category-level anomaly detection (50/30/20 comparison)

* Interactive Dashboard

  * Savings rate, monthly savings, and gap metrics
  * Top spending categories (90 days)
  * Savings projection vs goal timeline
  * Daily fiscal burn tracker with safety alerts

* AI-Generated Financial Audit

  * Multi-section, highly detailed analysis
  * Strategy tiers: Aggressive, Balanced, Defensive
  * Stress testing with emergency expense simulation
  * Persona-driven recommendations and closing questions

* Exportable PDF Report

  * One-click download of the full financial audit

---

## 🧠 Tech Stack

* Frontend: Streamlit
* LLM: Groq (LLaMA 3.1 – 8B Instant)
* Agent Framework: Agno
* Data Processing: Pandas
* Visualization: Streamlit native charts
* PDF Generation: FPDF
* Environment Management: python-dotenv

---

## 📂 Project Structure

Single-file application:

* app.py (main Streamlit application)
* .env (Groq API key)

No database or backend services required.

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```
git clone https://github.com/MihirKapile/Smart_Financial_Coach.git
cd smart-financial-coach
```

### 2. Create Virtual Environment

```
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

Required packages:

* streamlit
* pandas
* agno
* openpyxl
* groq
* python-dotenv
* fpdf

---

### 4. Configure Environment Variables

To run this application, you need a Groq API key.

🔑 Where to Get a Groq API Key

1) Visit the Groq Console: https://console.groq.com

2) Sign up or log in with your account

3) Navigate to API Keys in the dashboard

4) Generate a new API key

Create a `.env` file in the root directory:

```
GROQ_API_KEY=your_groq_api_key_here
```

---

### 5. Run the App

```
streamlit run app.py
```

The application will open in your browser.

---

## 🧾 Supported Transaction File Formats

A sample dataset is included for quick testing and demos:

* **synthetic_financial_transactions.xlsx**

  * Artificially generated transaction data
  * Covers multiple categories, merchants, and dates
  * Designed to simulate realistic personal finance behavior
  * Safe to use for interviews, demos, and experimentation

You can upload this file directly to explore the full functionality of the app without providing real financial data.

The app intelligently detects columns using fuzzy matching.

Recognized fields:

* Date: date, time, day
* Amount: amount, value, cost, price, outflow
* Category: category, merchant, description

Files may contain additional columns — they are safely ignored.

---

## 🧮 Financial Logic Overview

* Uses last 90 days of data to estimate real monthly spending
* Monthly savings = income – average monthly spending
* Goal feasibility is evaluated using actual savings velocity
* Projection charts compare current savings trajectory vs required path
* Daily burn rate ensures short-term fiscal discipline

---

## 📊 Personas & Behavior

Each persona affects:

* Tone and verbosity of responses
* Risk tolerance
* Recommendation aggressiveness
* Language style (professional vs playful vs analytical)

Switching personas resets the conversation and analysis for clarity.

---

## 🔐 Privacy & Security

* No data is stored externally
* All processing happens in-session
* Uploaded files remain in memory only
* No authentication or tracking

---

## 🧪 Ideal Use Cases

* Interview-ready AI finance case study
* Agentic AI system demonstration
* Personal finance analysis MVP
* LLM + data intelligence portfolio project

---

## 🛣️ Future Enhancements

* Multi-file ingestion (bank + credit cards)
* Month-over-month trend comparisons
* Custom rule engines for spending caps
* Long-term net worth modeling
* Optional user authentication

---
