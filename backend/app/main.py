from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from app.rag import build_rag_chain, CHARACTER_NAMES

app = FastAPI(title="Wit & Wisdom", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-build all three character chains at startup
chains = {
    "austen": build_rag_chain("austen"),
    "darcy":  build_rag_chain("darcy"),
    "emma":   build_rag_chain("emma"),
}


class ChatRequest(BaseModel):
    question: str
    character: Literal["austen", "darcy", "emma"] = "austen"


@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(400, "Question cannot be empty")

    chain = chains.get(request.character, chains["austen"])

    def stream_response():
        for chunk in chain.stream(request.question):
            yield chunk

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "assistant": "Wit & Wisdom",
        "characters": CHARACTER_NAMES,
        "novels": [
            "Pride and Prejudice",
            "Sense and Sensibility",
            "Emma",
            "Persuasion",
            "Northanger Abbey",
            "Mansfield Park",
        ],
    }