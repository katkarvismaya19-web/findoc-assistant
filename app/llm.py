"""Answer layer. Retrieved chunks go in, a grounded answer comes out.

The system prompt forces the model to answer only from the supplied context
and to say so when the context is insufficient. Without that instruction the
model will happily fill gaps from memory, which defeats the point of RAG.
"""
import requests

from app import config

SYSTEM = (
    "You answer questions about financial regulatory documents. "
    "Use ONLY the numbered context passages provided. "
    "Cite the passage numbers you relied on, like [1] or [2]. "
    "If the passages do not contain the answer, say so plainly instead of "
    "guessing. Do not add information from outside the passages."
)


def build_prompt(question, chunks):
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(
            f"[{i}] (source: {chunk['source']}, page {chunk['page']})\n{chunk['text']}"
        )
    context = "\n\n".join(blocks)
    return f"Context passages:\n\n{context}\n\nQuestion: {question}\n\nAnswer:"


def answer(question, chunks, timeout=45):
    if not config.GROQ_API_KEY:
        return (
            "[No GROQ_API_KEY set, so no answer was generated. "
            "Retrieval still ran - see the sources below.]"
        )

    payload = {
        "model": config.GROQ_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_prompt(question, chunks)},
        ],
    }
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}

    try:
        resp = requests.post(
            config.GROQ_URL, json=payload, headers=headers, timeout=timeout
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except requests.RequestException as exc:
        return f"[LLM call failed: {exc}]"
