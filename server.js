const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const DATA_FILE = path.join(__dirname, 'data', 'state.json');
const LOG_FILE = path.join(__dirname, 'data', 'audit.log');

// Global State
let state = {
  events: [],
  weights: { severity: 0.5, impact: 0.3, latency: 0.2 },
  lastTriage: null
};

// Load persisted state if exists
if (fs.existsSync(DATA_FILE)) {
  try {
    state = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  } catch (e) {
    console.error("Could not parse saved state, starting fresh.");
  }
}

function logAudit(step, details) {
  const logEntry = `[${new Date().toISOString()}] [${step}] ${JSON.stringify(details)}\n`;
  fs.appendFileSync(LOG_FILE, logEntry);
}

// Gen-AI Explanation Generator
async function generateExplanation(event) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (apiKey) {
    try {
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
      const prompt = `Summarize this incident into a concise 1-sentence briefing for an operator: Source: ${event.source}, Type: ${event.type}, Severity: ${event.severity}/10, Details: ${JSON.stringify(event.payload)}`;
      const result = await model.generateContent(prompt);
      return result.response.text().trim();
    } catch (err) {
      logAudit("AI_FALLBACK", { error: err.message });
    }
  }
  // Fast offline heuristic generator
  return `[AI Summary] ${event.source.toUpperCase()} reported high-priority ${event.type} (Severity ${event.severity}/10). Immediate operator attention suggested.`;
}

// Calculate Priority Score
function calculateScore(event) {
  const w = state.weights;
  const sevScore = (event.severity || 1) * 10;
  const impactScore = (event.impactScore || 1) * 10;
  const latencyScore = Math.min((event.latencyMs || 0) / 100, 100);
  
  return parseFloat(((sevScore * w.severity) + (impactScore * w.impact) + (latencyScore * w.latency)).toFixed(2));
}

// Ingestion Endpoint (Supports 3 streams over HTTP)
app.post('/api/ingest', async (req, res) => {
  const startTime = Date.now();
  const incomingEvents = Array.isArray(req.body) ? req.body : [req.body];
  
  logAudit("INGEST_BATCH", { count: incomingEvents.length });

  const processed = [];
  for (let evt of incomingEvents) {
    const scoredEvt = {
      ...evt,
      id: evt.id || `evt_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      ingestedAt: new Date().toISOString(),
      score: calculateScore(evt),
      aiExplanation: await generateExplanation(evt)
    };
    processed.push(scoredEvt);
  }

  state.events = [...processed, ...state.events].slice(0, 50); // Keep top 50 recent
  state.events.sort((a, b) => b.score - a.score);
  state.lastTriage = { timestamp: new Date().toISOString(), count: processed.length };

  fs.writeFileSync(DATA_FILE, JSON.stringify(state, null, 2));
  
  const processingTimeMs = Date.now() - startTime;
  logAudit("TRIAGE_COMPLETE", { processingTimeMs, topItemId: state.events[0]?.id });

  res.json({ success: true, processingTimeMs, events: state.events });
});

// Fetch Triage Results & State Replay
app.get('/api/briefings', (req, res) => {
  res.json(state);
});

// Operator Feedback Loop
app.post('/api/feedback', (req, res) => {
  const { weightAdjustments } = req.body; // e.g. { severity: 0.7, impact: 0.2, latency: 0.1 }
  if (weightAdjustments) {
    state.weights = { ...state.weights, ...weightAdjustments };
    // Recalculate scores
    state.events.forEach(evt => {
      evt.score = calculateScore(evt);
    });
    state.events.sort((a, b) => b.score - a.score);
    fs.writeFileSync(DATA_FILE, JSON.stringify(state, null, 2));
    logAudit("WEIGHTS_UPDATED", state.weights);
  }
  res.json({ success: true, weights: state.weights, events: state.events });
});

// Audit Trail Route
app.get('/api/audit', (req, res) => {
  if (fs.existsSync(LOG_FILE)) {
    const logs = fs.readFileSync(LOG_FILE, 'utf8').trim().split('\n').slice(-30);
    res.json({ logs });
  } else {
    res.json({ logs: [] });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`GlanceApp 93 Server running on http://localhost:${PORT}`);
});
