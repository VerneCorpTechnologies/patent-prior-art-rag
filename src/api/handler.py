import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.extraction.extractor import extract_invention
from src.retrieval.retriever import retrieve_prior_art
from src.mapping.mapper import map_claims

app = FastAPI(title="Patent Prior Art Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    patent_text: str


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
def extract(request: ExtractRequest):
    extraction = extract_invention(request.patent_text)
    return {"extraction": extraction}


@app.post("/retrieve")
def retrieve(request: RetrieveRequest):
    results = retrieve_prior_art(request.extraction, request.max_results)
    return {"results": results}


@app.post("/map")
def map_patent(request: MapRequest):
    mapping = map_claims(
        request.extraction,
        request.prior_art_number,
        request.prior_art_chunks
    )
    return {"mapping": mapping}


# Lambda handler
handler = Mangum(app, lifespan="off", api_gateway_base_path="/prod")