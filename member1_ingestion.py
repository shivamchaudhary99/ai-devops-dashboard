import requests
import time
import random
from datetime import datetime

# Your backend API URL (we will build this in step 2)
API_URL = "http://localhost:8000/ingest"

def generate_fake_event():
    # 3 Simulated Data Sources
    sources = ["Server Logs", "Database Alerts", "DNetwork Traffic"]
    source = random.choice(sources)
    
    # Matching realistic errors for each source
    if source == "Server Logs":
        msg = random.choice(["API latency spike to 2000ms", "500 Internal Server Error on /login", "CPU usage at 98%"])
    elif source == "Database Alerts":
        msg = random.choice(["Deadlock detected in transaction", "Connection pool exhausted", "Slow query execution > 5s"])
    else:
        msg = random.choice(["DDoS attack signature detected", "Unexpected outbound traffic port 22", "Firewall rules sync failed"])
        
    # Constructing the JSON event
    return {
        "event_id": f"evt_{random.randint(10000, 99999)}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": source,
        "description": msg,
        "impact_score": random.randint(1, 10) # Random initial score for testing
    }

print("Starting Data Ingestion Script... (Press Ctrl+C to stop)")

# Infinite loop to send data every 2 seconds
while True:
    event_payload = generate_fake_event()
    try:
        print(f"Sending event from {event_payload['source']}...")
        response = requests.post(API_URL, json=event_payload)
        print(f"Success! Status Code: {response.status_code}")
    except Exception as e:
        print("Backend is not running yet, bro! Start the API server first.")
    
    # Wait 2 seconds before sending the next event
    time.sleep(2)