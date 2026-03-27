# ⚖️ Patent Prior Art Search
### Invention Extraction · Prior Art Retrieval · Claim Mapping

A production-grade RAG system that automates patent prior art search before filing. A patent attorney inputs a patent application; the system extracts the core inventive concept in plain English, searches the EPO database for semantically similar prior art, and produces an element-by-element claim mapping with colour-coded novelty assessment.

Built to reduce the cost and time of pre-filing patent searches — helping attorneys identify conflicts before submitting to the EPO, reducing rejection cycles and client costs.

---

## 🎯 The Problem

Patent claims are deliberately written in broad, abstract legal language that obscures the core inventive concept. Comparing two patents manually requires an attorney to mentally extract the essence of both — a slow, expensive, and cognitively demanding process.

This system automates that workflow in three steps:

```
EXTRACT  →  RETRIEVE  →  MAP
```

1. **Extract** — Nova Pro reads the patent and extracts the inventive concept in plain English
2. **Retrieve** — The extracted concept is embedded and used to search the EPO database for semantically similar prior art
3. **Map** — Each prior art patent is compared element by element against the client's claims, with colour-coded novelty assessment

---

## 🏗️ Architecture

```
Streamlit UI (Streamlit Community Cloud)
        ↓
AWS API Gateway → AWS Lambda (FastAPI + Mangum)
        ↓                    ↓
   AWS Bedrock            AWS S3
 (Nova Pro +           (Patent storage)
  Titan Embed)
        ↓
     Pinecone
  (Vector store)
        ↓
   EPO OPS API
 (Patent database)
```

### Key Design Decisions

**Concept-first retrieval** — The system embeds the *extracted inventive concept* rather than raw claim text. Patent claims are written to be broad and abstract — retrieving on that language finds patents that use similar legal phrasing, not patents that describe similar inventions.

**Structure-aware chunking** — Each patent claim is treated as an atomic unit and never split. A naive text splitter would destroy the semantic integrity of patent claims by cutting mid-sentence.

**Serverless backend** — AWS Lambda charges only per invocation with no idle server costs. The architecture scales automatically and costs ~$0 at demo scale.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Amazon Nova Pro via AWS Bedrock |
| Embeddings | Amazon Titan Text Embeddings V2 via AWS Bedrock |
| Vector Store | Pinecone (free tier, serverless) |
| Patent Data | EPO OPS API (GB, EP, PCT patents) |
| Orchestration | LangChain |
| Evaluation | RAGAS |
| Backend | FastAPI + Mangum |
| Frontend | Streamlit |
| Deployment | AWS Lambda + API Gateway |
| UI Hosting | Streamlit Community Cloud |
| CI/CD | GitHub Actions |

---

## 📁 Project Structure

```
patent-prior-art-rag/
├── src/
│   ├── ingestion/
│   │   ├── epo_client.py        # EPO OPS API client
│   │   ├── patent_parser.py     # Structure-aware XML parser
│   │   ├── chunker.py           # Atomic claim chunker
│   │   ├── embedder.py          # Bedrock Titan embeddings
│   │   ├── pinecone_store.py    # Pinecone ingestion
│   │   └── ingest.py            # Full ingestion pipeline
│   ├── extraction/
│   │   └── extractor.py         # Invention concept extraction
│   ├── retrieval/
│   │   ├── epo_search.py        # EPO CQL search
│   │   └── retriever.py         # Semantic retrieval pipeline
│   ├── mapping/
│   │   └── mapper.py            # Element-by-element claim mapping
│   ├── evaluation/
│   │   └── evaluator.py         # RAGAS evaluation pipeline
│   ├── api/
│   │   └── handler.py           # FastAPI + Lambda handler
│   └── ui/
│       └── app.py               # Streamlit three-panel UI
├── tests/
│   ├── test_epo_client.py
│   ├── test_patent_parser.py
│   ├── test_chunker.py
│   ├── test_ingestion.py
│   ├── test_extractor.py
│   ├── test_retriever.py
│   ├── test_mapper.py
│   └── test_evaluator.py
├── .env                         # Credentials (never committed)
├── .gitignore
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- AWS account with Bedrock access (Nova Pro + Titan Embeddings V2)
- Pinecone free account with an index named `patent-prior-art` (1024 dimensions, cosine, dense)
- EPO OPS API account (ops.epo.org)

### Installation

```bash
git clone https://github.com/VerneCorpTechnologies/patent-prior-art-rag.git
cd patent-prior-art-rag
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```bash
# AWS
AWS_REGION=us-east-1
AWS_PROFILE=your-aws-profile

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=patent-prior-art

# EPO OPS API
EPO_CONSUMER_KEY=your_epo_consumer_key
EPO_CONSUMER_SECRET=your_epo_consumer_secret
```

### Run Locally

```bash
PYTHONPATH=. streamlit run src/ui/app.py
```

---

## 🧪 Running Tests

Run individual tests:

```bash
PYTHONPATH=. python3 tests/test_epo_client.py
PYTHONPATH=. python3 tests/test_patent_parser.py
PYTHONPATH=. python3 tests/test_chunker.py
PYTHONPATH=. python3 tests/test_ingestion.py
PYTHONPATH=. python3 tests/test_extractor.py
PYTHONPATH=. python3 tests/test_retriever.py
PYTHONPATH=. python3 tests/test_mapper.py
PYTHONPATH=. python3 tests/test_evaluator.py
```

### RAGAS Evaluation Results

| Metric | Score | Description |
|---|---|---|
| Faithfulness | 0.833 | Answers grounded in retrieved patent text |
| Answer Relevancy | 0.280 | Answer relevance to the question |
| Context Precision | 0.667 | Retrieved chunks relevance |
| Context Recall | 0.333 | Coverage of relevant chunks |

---

## 💡 How It Works

### Step 1 — Extract
The attorney enters a patent number or pastes patent text. Amazon Nova Pro extracts:
- The core inventive concept in 2-3 plain English sentences
- Key functional elements as a structured list
- The problem the invention solves

### Step 2 — Retrieve
The extracted concept (not raw claim text) is embedded using Titan Embeddings V2 and used to:
1. Build a CQL query to search the EPO OPS API for candidate patents
2. Ingest candidate patents into Pinecone with structure-aware chunking
3. Run semantic similarity search to find the most relevant prior art chunks

### Step 3 — Map
For each retrieved prior art patent, Nova Pro produces:
- Element-by-element comparison against the client's claims
- Evidence quotes from the prior art
- Colour-coded novelty status per element: 🔴 Prior Art / 🟡 Ambiguous / 🟢 Novel
- Overall risk assessment: High / Medium / Low

---

## 📊 Interview Talking Points

**Why concept-first retrieval?**
Raw patent claim text is deliberately broad and abstract — optimised for legal protection, not semantic clarity. Retrieving on the extracted concept finds patents that describe similar inventions even when the legal language is completely different.

**Why structure-aware chunking?**
A naive text splitter would cut mid-claim, destroying the semantic integrity of patent claims. Each claim is kept as an atomic unit — this was the single biggest driver of retrieval quality improvement measured by RAGAS Context Precision.

**Why Lambda over ECS?**
For a system handling occasional requests rather than continuous traffic, serverless is the right architectural choice. No idle server costs, automatic scaling, and the same IAM-based security model. A move to ECS would be warranted at sustained high request volumes.

**Why Pinecone over ChromaDB?**
ChromaDB requires persistent disk storage — incompatible with Lambda's stateless execution model. Pinecone is a managed serverless vector store called via API, which fits Lambda perfectly.

---

## 👤 Author

David Verne — [LinkedIn](https://linkedin.com/in/david-verne-329385103)
