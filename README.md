# 🚨 AI DevOps Alert Dashboard

Welcome to the **AI DevOps Alert Dashboard**! This project is a complete, real-time AI-powered pipeline built for our hackathon to ingest, analyze, and visually rank system and network alerts using Google Gemini AI.

---

## 👥 Team Members & Architecture

This project is divided into four main microservices, built collaboratively by our team:

*   **Member 1: Data Ingestion Engine (`member1_ingestion.py`)** 
    *   Simulates real-time DevOps environments by continuously generating and streaming JSON-based system logs, network traffic, and database alerts.
*   **Member 2: FastAPI Backend Server (`member2_backend.py`)**
    *   Acts as the central nervous system. It receives incoming data streams, stores them in memory, and handles API endpoints for both ingestion and data retrieval.
*   **Member 3: AI Analysis Integration (`test_ai.py` & AI Logic)**
    *   Connects to the Google Gemini API to analyze raw error logs, assigns a severity score (1-10), and generates actionable plain-text advice for developers.
*   **Member 4: Streamlit UI Dashboard (`member4_frontend.py`)**
    *   A responsive, real-time web frontend that fetches the AI-processed data from the backend and displays it in a clean, color-coded dashboard (Critical, Warning, Low Priority).

---

## ⚙️ Prerequisites

Make sure you have Python installed, along with the following libraries:
```bash
pip install fastapi uvicorn requests google-generativeai streamlit
