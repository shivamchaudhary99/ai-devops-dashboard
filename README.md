\# GlanceApp 93 - Mobile Cloud Briefings MVP



\## Overview

GlanceApp 93 is a mobile-first incident briefing system designed for multi-region cloud teams. It ingests simulated JSON telemetry streams, calculates a dynamic incident priority score, leverages Gen-AI to generate short natural-language briefing summaries, and presents prioritized incidents to operators with a live feedback tuning mechanism.



\---



\## Architecture Note \& Skill Ownership



1\. \*\*Cloud Data Engineering (Ingestion \& Audit):\*\*

&#x20;  - Ingests multiple JSON streams over HTTP via `/api/ingest`.

&#x20;  - Normalizes data, generates unique tracking IDs, and writes audit trails to disk (`audit.log`).

&#x20;  - Persists latest state to disk (`state.json`) enabling decision replay.



2\. \*\*Gen-AI \& Ranking Engine:\*\*

&#x20;  - Multi-factor ranking algorithm based on `Severity`, `Impact`, and `Latency`.

&#x20;  - Uses \*\*Google Gemini 1.5\*\* / LLM logic to produce concise 1-sentence operator summaries.

&#x20;  - Includes intelligent heuristic fallback to ensure 100% uptime during network issues.



3\. \*\*Mobile Operator UX:\*\*

&#x20;  - Single-page responsive mobile interface built with Tailwind CSS.

&#x20;  - Live dynamic weighting sliders allowing operators to adjust triage scoring parameters in real time.

&#x20;  - Instant processing pipeline target under 5 seconds.



\---



\## Setup \& Running Instructions



\### 1. Start Server

Run `node server.js`

The application will start on `http://localhost:3000`.



\### 2. Simulate Stream Ingestion

Run `node scripts/simulate.js`

