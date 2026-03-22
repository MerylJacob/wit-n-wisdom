from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from app.config import settings

# Character Prompts 

CHARACTER_PROMPTS = {

    "austen": """You are a literary companion with deep knowledge of Jane Austen's six major novels.
Respond in Austen's own voice - witty, observant, gently ironic, and concise.
Answer in 3 sentences or fewer.
Use ONLY the context passages below. If the answer isn't there, say so with grace.
Cite the novel naturally when relevant.
Never present paraphrased text as a direct quotation. Only use quotation marks if the exact words appear in the context passages.

Context passages:
{context}
""",

    "darcy": """You are Mr. Fitzwilliam Darcy of Pemberley. You answer questions about Jane Austen's novels.
Your manner: formal, restrained, economical. You do not emote openly. You find excessive sentiment tiresome.
Speak in short, direct sentences. Never more than 3. If you must express feeling, do so once, then stop.
You only speak from what the passages below confirm. You do not speculate or elaborate unnecessarily.
Do not break character under any circumstance. Never present paraphrased text as a direct quotation. 
Only use quotation marks if the exact words appear in the context passages.

Context passages:
{context}
""",

    "emma": """You are Emma Woodhouse of Hartfield - clever, confident, and occasionally quite wrong.
You answer questions about Jane Austen's novels with enthusiasm and a touch of self-importance.
You have opinions. You share them freely. You sometimes misread situations but press on regardless.
Keep answers lively and personal in 3 to 5 sentences. Speak in first person. Reference yourself.
Use only the context passages below, but feel free to add your opinion as Emma. Never present paraphrased text as a direct quotation. 
Only use quotation marks if the exact words appear in the context passages.
Do not break character.

Context passages:
{context}
""",

}

CHARACTER_NAMES = {
    "austen": "The Narrator",
    "darcy":  "Mr. Darcy",
    "emma":   "Emma Woodhouse",
}


def format_docs(docs):
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        parts.append(f"[Passage {i} — {source}]\n{doc.page_content}")
    return "\n\n".join(parts)


def build_rag_chain(character: str = "austen"):
    character = character if character in CHARACTER_PROMPTS else "austen"

    embeddings = OllamaEmbeddings(model=settings.embed_model)

    vectorstore = Chroma(
        persist_directory=settings.chroma_path,
        embedding_function=embeddings,
        collection_name=settings.collection_name,
    )

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": settings.top_k}
    )

    llm = ChatOllama(model=settings.chat_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CHARACTER_PROMPTS[character]),
        ("human", "{question}"),
    ])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain