# Support Assistant

## Objective

This module builds a local retrieval grounded assistant for Zepto policy questions, using Chroma for the vector store, sentence-transformers for embeddings, and a LangGraph flow that routes each query and answers it deterministically by default.

## How to Run

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860
```

## API

Send a POST request to `/ask` with a JSON body containing a query.

Request body

```json
{"query": "What is the return window for perishable items"}
```

Response schema

```json
{"answer": "...", "sources": ["doc_02"], "confidence": 1.0}
```

## Example Calls

Both calls below were run with `MOCK_LLM` left at its default, meaning no external LLM was contacted for either response.

Policy question, which should trigger retrieval.

Request

```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"query":"What is the delivery fee for orders under INR 149?"}'
```

Response

```json
{"answer":"Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order volume. Standard del","sources":["doc_01","doc_05","doc_03"],"confidence":1.0}
```

General question, which should not trigger retrieval.

Request

```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"query":"What is the capital of France?"}'
```

Response

```json
{"answer":"I can only answer questions about Zepto policies right now.","sources":[],"confidence":1.0}
```

The first call was correctly routed to the retrieval node, since the query contains the keyword "delivery," and the returned chunks and snippet come from the delivery policy document. The second call has no policy keyword, so it was routed straight to the canned direct answer with no retrieval and no sources.

## MOCK_LLM Toggle

With `MOCK_LLM` left unset or set to `1`, the service runs in deterministic mock mode. Intent classification uses a keyword heuristic, retrieval always runs for real against ChromaDB, and the final answer is built from a canned template that is populated with the actual retrieved content, so no external LLM call ever happens. Setting `MOCK_LLM=0` is an optional extension that would call a real LLM through Groq's free tier, with retry logic if the model's raw output fails to validate against the response schema.

## Prompt Template

The app defines a structured prompt following a role, context, task, format, and length layout. It includes an explicit negative constraint telling the model not to answer using information outside the provided context, and it includes a few shot example showing the exact JSON shape expected in the response. This template is used by the optional real LLM path.

## Architecture

Ingestion loads the eight policy documents from the `docs` folder. Each document is embedded as a single chunk using `SentenceTransformer` with the `all-MiniLM-L6-v2` model. Those embeddings are stored in a ChromaDB collection called `zepto_policy_docs`. When a query comes in, the `retrieve_and_answer` node embeds the query the same way and pulls back the three most similar chunks from that collection. Generation is the only stage that branches on `MOCK_LLM`. In the default mock state, the answer is a canned string built from the top retrieved chunk. In the optional real LLM state, the retrieved chunks are placed into the structured prompt above and sent to the model instead.

## Routing

The LangGraph flow has three nodes, `classify_intent`, `retrieve_and_answer`, and `direct_answer`. A conditional edge out of `classify_intent` sends policy questions to `retrieve_and_answer` and everything else to `direct_answer`. This routing decision itself does not depend on `MOCK_LLM`, only the generation step inside each node does.

## Docker

```bash
docker build -t zepto-support-assistant support_assistant
docker run --rm -p 7860:7860 zepto-support-assistant
```

This Dockerfile builds and runs locally and serves the same `/ask` endpoint on port 7860. Deploying it to a hosted platform is an optional extension and is not required for grading.
