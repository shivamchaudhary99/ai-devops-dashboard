# Gen AI & Ranking Module

This module provides the AI explanation generation and weighted multi-factor ranking engine for the alert dashboard.

## Module Structure

```
GEN_AI_WORK/
├── app/
│   ├── explainer.py     # Gen AI explanation generation (Hugging Face / fallback + caching)
│   ├── scoring.py       # Multi-factor ranking engine (severity, recency, frequency, blast radius)
│   ├── models.py        # Pydantic schemas (EventPayload, ScoredEvent, BriefingResponse)
│   ├── store.py         # Thread-safe in-memory event store
│   ├── audit.py         # Processing audit trail logger
│   └── main.py          # Complete FastAPI REST service
├── simulator/
│   ├── event_generator.py  # 3-source cloud event generator
│   └── stream_sender.py    # Batch stream sender for testing
├── test_explainer.py    # Quick standalone test script
├── requirements.txt     # Python dependencies
└── .env.example         # Environment template
```

## Quick Start for Team Members

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Hugging Face Token (Optional)
```bash
cp .env.example .env
# Add your HF_API_TOKEN in .env (if omitted, high-accuracy fallback templates are used automatically)
```

### 3. Test AI Explanations
```bash
python test_explainer.py
```

### 4. Run the Full Backend API
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Send Simulated Event Batches
```bash
python -m simulator.stream_sender --rounds 3 --batch-size 15
```

## How to Integrate

### For Member 2 (FastAPI Backend):
You can import the explainer and ranking engine directly into your routes:

```python
from GEN_AI_WORK.app.explainer import explain_event, explain_top_events
from GEN_AI_WORK.app.scoring import scoring_engine

# Score an incoming event
scored_event = scoring_engine.score_event(event)

# Generate AI explanation for the event
explanation = await explain_event(scored_event)
```

### For Member 4 (Frontend / Streamlit):
Fetch ranked briefings directly from:
- `GET http://localhost:8000/api/briefings`
- `GET http://localhost:8000/api/briefings/{event_id}`
- `GET http://localhost:8000/api/audit`
