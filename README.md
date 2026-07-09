# CreditPath

> GenAI-powered loan readiness and scheme discovery for Indian MSMEs.

CreditPath helps small business owners understand their loan eligibility,
get a plain-English explanation of their financial profile, receive an
AI-generated improvement plan, and discover the most relevant government
financing schemes — all from a single assessment.

## Status

🚧 Under active development — 32-day build in progress.

## Tech Stack

| Layer | Choice |
|---|---|
| API | FastAPI + Pydantic |
| Frontend | Streamlit |
| LLM | Gemini 2.5 Flash |
| Retrieval | ChromaDB + sentence-transformers |
| ML | scikit-learn K-Means |
| Evaluation | RAGAs + custom plan evaluator |
| Deploy | Railway + Streamlit Cloud + GitHub Pages |

## Local Setup

```bash
git clone https://github.com/Beast-jr/creditpath.git
cd creditpath
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

## Architecture

_Diagram coming soon._

## License

MIT
