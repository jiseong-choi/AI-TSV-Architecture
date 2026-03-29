from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .config import SETTINGS
from .engine import TSVCompressionEngine


class QueryRequest(BaseModel):
    query: str


app = FastAPI(title="TSV Compression Research Prototype", version="0.2.0")
engine = TSVCompressionEngine()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/sessions/{session_id}/query")
def query(session_id: str, body: QueryRequest) -> dict:
    return engine.process_query(session_id, body.query).to_dict()


@app.post("/sessions/{session_id}/pack")
def pack(session_id: str, body: QueryRequest) -> dict:
    return engine.inspect_pack(session_id, body.query)


@app.get("/sessions/{session_id}/history")
def history(session_id: str) -> list[dict]:
    return engine.get_history(session_id)


@app.get("/sessions/{session_id}/archive")
def archive(session_id: str) -> dict:
    return engine.get_archive(session_id)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.api:app",
        host=SETTINGS.default_host,
        port=SETTINGS.default_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
