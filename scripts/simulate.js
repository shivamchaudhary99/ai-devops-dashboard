const http = require('http');

// Simulates 3 incoming JSON event streams
const simulatedStreams = [
  // Stream 1: Infra / Database Stream
  {
    source: "infra-db-cluster",
    type: "CPU Throttling & IOPS Exhaustion",
    severity: 8,
    impactScore: 9,
    latencyMs: 350,
    payload: { node: "db-primary-01", iopsUsage: "98%" }
  },
  // Stream 2: API Gateway / Edge Stream
  {
    source: "api-gateway-edge",
    type: "SSL Certificate Expiry Warning",
    severity: 5,
    impactScore: 6,
    latencyMs: 45,
    payload: { domain: "api.cloud.internal", daysRemaining: 3 }
  },
  // Stream 3: Application / Auth Stream
  {
    source: "auth-identity-service",
    type: "Brute Force Suspicious Pattern",
    severity: 9,
    impactScore: 7,
    latencyMs: 120,
    payload: { targetIPs: 14, failedAttempts: 2500 }
  }
];

const data = JSON.stringify(simulatedStreams);

const req = http.request({
  hostname: 'localhost',
  port: 3000,
  path: '/api/ingest',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
}, (res) => {
  let responseData = '';
  res.on('data', (chunk) => responseData += chunk);
  res.on('end', () => {
    console.log("Successfully ingested 3 simulated streams!");
    console.log("Response:", responseData);
  });
});

req.on('error', (error) => {
  console.error("Error connecting to GlanceApp 93 server. Is it running?", error.message);
});

req.write(data);
req.end();
