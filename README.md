# Zepto Data and AI Platform

This repository is a single capstone submission built around three connected modules. Together they tell one story. A data pipeline turns a public catalog website into a clean relational database. An analytics pipeline profiles and predicts outcomes on the Titanic dataset. A support assistant answers Zepto policy questions using a locally grounded retrieval pipeline. Each module lives in its own folder and is graded on its own criteria, but all three sit inside this one repository.

## Repository Layout

The project root contains three module folders and one consolidated requirements file.

- `data_pipeline` holds the scraping, cleaning, and SQLite loading code along with the executed SQL queries.
- `analytics` holds the Titanic EDA and modeling scripts, the saved charts, and the saved model pipeline.
- `support_assistant` holds the LangGraph and FastAPI service that answers Zepto policy questions.

## Setup

This project uses one consolidated `requirements.txt` at the repository root, so a single environment can run all three modules.

Create a virtual environment with Python 3.11 and install everything in one step.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to Run Each Module

### 1. Data Pipeline

```bash
cd data_pipeline
python run_pipeline.py
```

This scrapes books.toscrape.com across three categories, cleans the fields, converts price to INR using a fixed rate of 1 GBP equal to 105.50 INR, builds a normalized SQLite database, and writes the executed SQL queries and their output to `sql_query_outputs.md`.

### 2. Analytics Pipeline

```bash
cd analytics
python 01_eda.py
python 02_modeling.py
```

The first script loads the Titanic dataset once, profiles it, cleans it, saves it as `titanic.csv`, and writes the EDA findings to `eda_summary.md`. The second script continues from that same cleaned data, trains and evaluates three classifiers plus a regression model, and writes everything to `modeling_summary.md` along with a saved pipeline file.

### 3. Support Assistant

```bash
cd support_assistant
uvicorn main:app --host 0.0.0.0 --port 7860
```

The service ingests the eight Zepto policy documents, embeds them locally with sentence-transformers, stores them in ChromaDB, and answers questions through a LangGraph flow. By default `MOCK_LLM` is left unset, so every answer is produced deterministically without any external LLM call. Send a request with curl or any HTTP client.

```bash
curl -X POST http://localhost:7860/ask -H "Content-Type: application/json" -d "{\"query\": \"What is Zepto's return policy\"}"
```

The service can also be built and run with Docker.

```bash
docker build -t zepto-support-assistant support_assistant
docker run --rm -p 7860:7860 zepto-support-assistant
```

## Design Decisions

### Data Pipeline

The pipeline scrapes three categories from books.toscrape.com rather than paginating the full catalog, since three categories already comfortably clears the sixty book minimum while keeping the scrape fast. Prices and star ratings are parsed with defensive fallbacks so a single malformed row cannot crash the whole run. Rows with an unreadable availability field are dropped rather than guessed, since a wrong stock status is worse than a missing row. The currency conversion uses the fixed project rate of 105.50 INR per GBP exactly as specified, with no external lookup involved.

### Analytics Pipeline

The Titanic dataset is loaded once through Seaborn's loader and immediately saved as a CSV, so every later step, including modeling, works from that single saved copy instead of re fetching the data. Missing values are handled using the percentage thresholds from the brief, dropping rows under five percent missing, imputing between five and thirty percent, and turning the very sparse deck column into its own category rather than guessing values. All preprocessing for modeling is fit only on the training split and reused on the test split, so no information leaks across the split. Three classifiers are compared side by side, class imbalance is handled three different ways for comparison, and a Random Forest is tuned with grid search while reporting its out of bag score. A parallel linear regression task predicts fare and reports the standard regression metrics alongside a residual plot.

### Support Assistant

Retrieval always runs for real, since embedding with sentence-transformers and querying ChromaDB need no API key and no network call. Only the final answer generation step is gated behind the `MOCK_LLM` toggle. With the default mock mode, intent classification uses a keyword heuristic and answers are built from canned templates populated with the actual retrieved chunks, so the output is fully deterministic and reproducible without any paid service. Setting `MOCK_LLM=0` is an optional extension that would call a real LLM through Groq's free tier, with retry logic if the model's output fails schema validation.

## Git Workflow

The implementation for each module was developed on a dedicated feature branch, committed once per module, and merged back into `main`.
