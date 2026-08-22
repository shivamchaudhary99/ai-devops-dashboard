from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
import json

# ⚠️ BHAI, YAHAN APNI ASLI API KEY DAALNA ZAROORI HAI! ⚠️
API_KEY = "AQ.Ab8RN6JBH909HA7-5WVlFHldd-sAO95tYmYfwH1M7rFGECyWpQ"
client = genai.Client(api_key=API_KEY)

app = FastAPI()
audit_trail = []

class EventPayload(BaseModel):
    event_id: str
    timestamp: str
    source: str
    description: str
    impact_score: int

def analyze_with_ai(description):
    try:
        prompt = f"""
        You are a Cloud DevOps AI. Analyze this system event: "{description}".
        Return ONLY a JSON response with two keys:
        - "ai_score": A severity score from 1 to 10 (10 being critical).
        - "ai_explanation": A simple 1-sentence explanation of the issue and what an operator should do.
        Do not use markdown formatting like ```json, just return the raw JSON text.
        """
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        ai_data = json.loads(response.text.strip())
        return ai_data
    except Exception as e:
        print(f"AI Error: {e}")
        return {"ai_score": 0, "ai_explanation": "AI failed to analyze."}

@app.post("/ingest")
async def ingest_data(event: EventPayload):
    event_data = event.model_dump()
    
    print(f"🤖 AI is analyzing: {event.description}...")
    ai_result = analyze_with_ai(event.description)
    
    event_data["ai_score"] = ai_result.get("ai_score")
    event_data["ai_explanation"] = ai_result.get("ai_explanation")
    
    audit_trail.append(event_data)
    print(f"✅ Scored {event_data['ai_score']}/10: {event_data['ai_explanation']}\n")
    
    return {"status": "success", "data": event_data}

@app.get("/logs")
async def get_logs():
    sorted_events = sorted(audit_trail, key=lambda x: x.get('ai_score', 0), reverse=True)
    return {"total_events": len(audit_trail), "events": sorted_events}