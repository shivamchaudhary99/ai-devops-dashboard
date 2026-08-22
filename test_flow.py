import requests

def check_integration():
    print("Checking connection between Member 1 and Member 2...\n")
    
    try:
        # Pinging the Member 2 Backend
        response = requests.get("http://localhost:8000/logs")
        data = response.json()
        
        total_events = data.get("total_events", 0)
        
        if total_events > 0:
            print("✅ SUCCESS! Member 1 and Member 2 are connected perfectly.")
            print(f"📊 Total Events Received by Server: {total_events}")
            print(f"🔥 Last Event Captured: {data['events'][-1]['source']} - {data['events'][-1]['description']}")
            print("\nReady to move to Member 3 (AI Ranking)!")
        else:
            print("⚠️ Server is ON, but no data found.")
            print("Fix: Make sure you are running 'python member1_ingestion.py' in another terminal!")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Backend (Member 2) is OFF.")
        print("Fix: Run 'python -m uvicorn member2_backend:app --reload' first!")

if __name__ == "__main__":
    check_integration()