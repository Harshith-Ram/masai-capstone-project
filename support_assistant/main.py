# Author: harshith kumar | Date: 2026-09-22
import json
import os
from pathlib import Path
from typing import List, Literal, TypedDict

import chromadb
import requests
from fastapi import FastAPI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, ValidationError
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "zepto_policy_docs"

POLICY_KEYWORDS = [
    "delivery",
    "return",
    "refund",
    "membership",
    "tracking",
    "cancel",
    "gift card",
    "support hours",
]

STRUCTURED_PROMPT_TEMPLATE = """ROLE:
You are a Zepto support assistant.

CONTEXT:
Use only the policy context provided below.
{context}

TASK:
Answer the user's question accurately and cite the document ids used.
Do not answer using information not present in the provided context.

FORMAT:
Return strict JSON with keys: answer (string), sources (array of strings), confidence (float 0 to 1).

LENGTH:
Keep answer under 120 words.

FEW-SHOT EXAMPLE:
User: What is the standard delivery fee below INR 149?
Assistant:
{"answer": "Orders below INR 149 incur a flat INR 25 standard delivery fee.", "sources": ["doc_01"], "confidence": 0.96}
"""


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class GraphState(TypedDict, total=False):
    query: str
    intent: Literal["policy_question", "general_question"]
    retrieved_texts: List[str]
    retrieved_ids: List[str]
    answer: str
    sources: List[str]
    confidence: float


app = FastAPI(title="Zepto Support Assistant", version="1.0.0")

_embedder = SentenceTransformer("all-MiniLM-L6-v2")
_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def is_mock_mode() -> bool:
    return os.getenv("MOCK_LLM", "1") != "0"


def load_corpus_to_chroma() -> None:
    docs = sorted(DOCS_DIR.glob("doc_*.txt"))
    if not docs:
        raise FileNotFoundError(f"No docs found in {DOCS_DIR}")

    existing = _collection.count()
    if existing >= len(docs):
        return

    ids = []
    texts = []
    metadatas = []

    for doc_path in docs:
        doc_id = doc_path.stem
        text = doc_path.read_text(encoding="utf-8").strip()
        ids.append(doc_id)
        texts.append(text)
        metadatas.append({"source": doc_id})

    embeddings = _embedder.encode(texts, convert_to_numpy=True).tolist()

    if _collection.count() > 0:
        # Reset to avoid duplicate IDs when re-running ingestion.
        all_existing = _collection.get(include=[])
        if all_existing.get("ids"):
            _collection.delete(ids=all_existing["ids"])

    _collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def classify_intent_node(state: GraphState) -> GraphState:
    query = state["query"]

    if is_mock_mode():
        q = query.lower()
        intent = "policy_question" if any(k in q for k in POLICY_KEYWORDS) else "general_question"
    else:
        intent = classify_with_llm(query)

    return {**state, "intent": intent}


def classify_with_llm(query: str) -> Literal["policy_question", "general_question"]:
    prompt = (
        "Classify the user query as either policy_question or general_question. "
        "Respond with one token only. Query: "
        + query
    )
    content = call_groq(prompt)
    label = content.strip().lower()
    if label not in {"policy_question", "general_question"}:
        return "general_question"
    return label  # type: ignore[return-value]


def retrieve_and_answer_node(state: GraphState) -> GraphState:
    query = state["query"]
    query_emb = _embedder.encode([query], convert_to_numpy=True).tolist()[0]

    res = _collection.query(query_embeddings=[query_emb], n_results=3)
    docs = res.get("documents", [[]])[0]
    ids = res.get("ids", [[]])[0]

    if is_mock_mode():
        top = docs[0] if docs else "No policy context available."
        snippet = top[:200].strip()
        answer = f"Based on the retrieved context: {snippet}"
        response = AskResponse(answer=answer, sources=ids, confidence=1.0)
    else:
        response = answer_with_llm(query=query, contexts=docs, sources=ids)

    return {
        **state,
        "retrieved_texts": docs,
        "retrieved_ids": ids,
        "answer": response.answer,
        "sources": response.sources,
        "confidence": response.confidence,
    }


def direct_answer_node(state: GraphState) -> GraphState:
    query = state["query"]

    if is_mock_mode():
        response = AskResponse(
            answer="I can only answer questions about Zepto policies right now.",
            sources=[],
            confidence=1.0,
        )
    else:
        response = direct_with_llm(query)

    return {
        **state,
        "answer": response.answer,
        "sources": response.sources,
        "confidence": response.confidence,
    }


def answer_with_llm(query: str, contexts: List[str], sources: List[str]) -> AskResponse:
    context_block = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts))
    prompt = STRUCTURED_PROMPT_TEMPLATE.format(context=context_block) + f"\n\nUser: {query}"
    return ask_llm_with_validation(prompt=prompt, fallback_sources=sources)


def direct_with_llm(query: str) -> AskResponse:
    prompt = (
        "Answer briefly in strict JSON with keys answer/sources/confidence. "
        "For sources use empty array when no retrieval context is used. "
        f"User question: {query}"
    )
    return ask_llm_with_validation(prompt=prompt, fallback_sources=[])


def ask_llm_with_validation(prompt: str, fallback_sources: List[str]) -> AskResponse:
    corrective = ""
    for _ in range(3):
        output = call_groq(prompt + corrective)
        try:
            parsed = json.loads(output)
            return AskResponse(**parsed)
        except (json.JSONDecodeError, ValidationError):
            corrective = "\n\nYour previous output was invalid. Return only strict JSON matching schema: {answer: string, sources: string[], confidence: float between 0 and 1}."

    return AskResponse(
        answer="ERROR: LLM response validation failed after retries.",
        sources=fallback_sources,
        confidence=0.0,
    )


def call_groq(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return "{\"answer\": \"ERROR: GROQ_API_KEY missing.\", \"sources\": [], \"confidence\": 0.0}"

    payload = {
        "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        "messages": [
            {"role": "system", "content": "You are a strict JSON assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def route_from_intent(state: GraphState) -> str:
    return "retrieve_and_answer" if state["intent"] == "policy_question" else "direct_answer"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("retrieve_and_answer", retrieve_and_answer_node)
    graph.add_node("direct_answer", direct_answer_node)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_from_intent,
        {
            "retrieve_and_answer": "retrieve_and_answer",
            "direct_answer": "direct_answer",
        },
    )
    graph.add_edge("retrieve_and_answer", END)
    graph.add_edge("direct_answer", END)
    return graph.compile()


load_corpus_to_chroma()
compiled_graph = build_graph()


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    final_state = compiled_graph.invoke({"query": req.query})
    return AskResponse(
        answer=final_state["answer"],
        sources=final_state.get("sources", []),
        confidence=float(final_state.get("confidence", 0.0)),
    )
