import os
from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from mangum import Mangum
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.extraction.extractor import extract_invention
from src.mapping.mapper import map_claims

app = FastAPI(title="Patent Prior Art Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Key Security ──────────────────────────────────────────
API_KEY = os.getenv("APP_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str = Security(api_key_header)):
    if not API_KEY or key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key


class ExtractRequest(BaseModel):
    patent_text: str


class IngestRequest(BaseModel):
    extraction: dict
    max_results: int = 5


class RetrieveRequest(BaseModel):
    extraction: dict
    max_results: int = 5


class MapRequest(BaseModel):
    extraction: dict
    prior_art_number: str
    prior_art_chunks: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
def extract(request: ExtractRequest, key: str = Security(verify_api_key)):
    extraction = extract_invention(request.patent_text)
    return {"extraction": extraction}


@app.post("/ingest")
def ingest(request: IngestRequest, key: str = Security(verify_api_key)):
    """Search EPO and ingest candidate patents into Pinecone."""
    from src.retrieval.epo_search import search_patents
    from src.ingestion.ingest import ingest_patent

    concept_text = request.extraction.get("concept", "")
    elements = request.extraction.get("elements", [])

    candidate_patents = search_patents(
        concept_text,
        elements=elements,
        max_results=request.max_results
    )

    ingested = []
    failed = []

    for patent_number in candidate_patents:
        try:
            ingest_patent(patent_number)
            ingested.append(patent_number)
        except Exception as e:
            failed.append({"patent": patent_number, "error": str(e)})

    return {
        "candidates": candidate_patents,
        "ingested": ingested,
        "failed": failed
    }


@app.post("/retrieve")
def retrieve(request: RetrieveRequest, key: str = Security(verify_api_key)):
    """Query Pinecone for semantically similar patents — fast."""
    from src.ingestion.embedder import embed_text
    from src.ingestion.pinecone_store import get_index

    concept_text = request.extraction.get("concept", "")
    query_embedding = embed_text(concept_text)
    index = get_index()

    results = index.query(
        vector=query_embedding,
        top_k=request.max_results,
        include_metadata=True
    )

    matches = []
    for match in results.matches:
        matches.append({
            "patent_number": match.metadata.get("patent_number"),
            "section": match.metadata.get("section"),
            "claim_number": match.metadata.get("claim_number"),
            "score": round(match.score, 3),
            "chunk_id": match.metadata.get("chunk_id"),
            "text": match.metadata.get("text", "")
        })

    return {"results": matches}


@app.post("/map")
def map_patent(request: MapRequest, key: str = Security(verify_api_key)):
    mapping = map_claims(
        request.extraction,
        request.prior_art_number,
        request.prior_art_chunks
    )
    return {"mapping": mapping}


handler = Mangum(app, lifespan="off", api_gateway_base_path="/prod")