// server.js
/**
 * RepoBrain V2 Full-Stack Express Bridge Controller
 * Connects the React Workbench to the Python FastMCP and Multi-Agent Orchestrator.
 * Exposes live REST and SSE (Server-Sent Events) streaming endpoints.
 */

import express from 'express';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

// Enable CORS for local Vite dev server
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Helper: Run python CLI commands
function runPythonCli(args, inputData = null) {
  return new Promise((resolve, reject) => {
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const env = { ...process.env, PYTHONPATH: path.join(__dirname, 'src') };
    const proc = spawn(pythonCmd, ['-m', 'repobrain.cli', ...args], { cwd: __dirname, env });

    let stdout = '';
    let stderr = '';

    if (inputData) {
      proc.stdin.write(inputData);
      proc.stdin.end();
    }

    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });

    proc.on('close', (code) => {
      resolve({ exitCode: code, stdout, stderr });
    });

    proc.on('error', (err) => {
      reject(err);
    });
  });
}

// 1. Health check
app.get('/api/repobrain/health', (req, res) => {
  res.json({
    status: 'online',
    version: '2.0.0',
    layers: {
      layer1_ast: 'operational',
      layer2_episodic: 'operational',
      layer3_research: 'operational',
      layer4_templates: 'operational',
      pillar5_harness: 'operational'
    },
    timestamp: new Date().toISOString()
  });
});

// 2. Run Verification Gates Live
app.get('/api/repobrain/gates', async (req, res) => {
  try {
    const result = await runPythonCli(['verify']);
    const passed = result.exitCode === 0 && result.stdout.includes('ALL 4 VERIFICATION GATES DETERMINISTICALLY VERIFIED');
    res.json({
      success: passed,
      exitCode: result.exitCode,
      gateStatus: {
        1: result.stdout.includes('GATE 1 PROOF PASSED'),
        2: result.stdout.includes('GATE 2 PROOF PASSED'),
        3: result.stdout.includes('GATE 3 PROOF PASSED'),
        4: result.stdout.includes('GATE 4 PROOF PASSED')
      },
      rawOutput: result.stdout
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3. Search Codebase (Two-Stage Hybrid RRF)
app.post('/api/repobrain/search', async (req, res) => {
  const { query, top_k = 5 } = req.body;
  if (!query) {
    return res.status(400).json({ error: 'Missing query in request body' });
  }
  try {
    const result = await runPythonCli(['search', query, '--top-k', String(top_k)]);
    res.json({ query, output: result.stdout, rawError: result.stderr });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 4. Research Technology (5-Phase CRAG)
app.post('/api/repobrain/research', async (req, res) => {
  const { topic, domain = 'general_tech' } = req.body;
  if (!topic) {
    return res.status(400).json({ error: 'Missing topic in request body' });
  }
  try {
    const result = await runPythonCli(['research', topic, '--domain', domain]);
    res.json({ topic, domain, output: result.stdout });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 5. Template Stockroom Search
app.post('/api/repobrain/templates', async (req, res) => {
  const { query, domain = 'all' } = req.body;
  if (!query) {
    return res.status(400).json({ error: 'Missing query in request body' });
  }
  try {
    const result = await runPythonCli(['templates', query, '--domain', domain]);
    res.json({ query, output: result.stdout });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 6. List Episodic Bug Memory
app.get('/api/repobrain/episodes', async (req, res) => {
  try {
    const result = await runPythonCli(['episodes']);
    res.json({ output: result.stdout });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 7. Server-Sent Events (SSE) Streaming Autonomous Multi-Agent Prompt Loop
app.get('/api/repobrain/prompt-loop', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const sendEvent = (event, data) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };

  sendEvent('status', { message: 'Initializing Multi-Agent 5-Phase CoT Orchestrator...' });

  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  const scriptCode = `
import json, sys
from repobrain.verify_gates import run_gate1, run_gate2, run_gate3, run_gate4

print(json.dumps({"event": "phase", "phase": "context_retrieval", "msg": "Gate 1: Byte-Safe AST parent-child extraction"}))
sys.stdout.flush()
run_gate1()

print(json.dumps({"event": "phase", "phase": "conceptual_grounding", "msg": "Gate 2: Hybrid RRF k=60 candidate fusion and CE scoring"}))
sys.stdout.flush()
run_gate2()

print(json.dumps({"event": "phase", "phase": "diagnostic_hypothesis", "msg": "Gate 3: Self-healing fail-to-pass distillation"}))
sys.stdout.flush()
run_gate3()

print(json.dumps({"event": "phase", "phase": "verification_verdict", "msg": "Gate 4: Retry ceiling #3 and surgical byte rollback"}))
sys.stdout.flush()
run_gate4()
`;

  const env = { ...process.env, PYTHONPATH: path.join(__dirname, 'src') };
  const child = spawn(pythonCmd, ['-c', scriptCode], { cwd: __dirname, env });

  child.stdout.on('data', (chunk) => {
    const text = chunk.toString();
    for (const line of text.split('\n')) {
      const clean = line.trim();
      if (!clean) continue;
      try {
        const parsed = JSON.parse(clean);
        sendEvent(parsed.event || 'message', parsed);
      } catch {
        sendEvent('stdout', { text: clean });
      }
    }
  });

  child.stderr.on('data', (chunk) => {
    sendEvent('stderr', { text: chunk.toString() });
  });

  child.on('close', (code) => {
    sendEvent('complete', { exitCode: code, success: code === 0 });
    res.end();
  });
});

app.listen(PORT, () => {
  console.log(`[+] RepoBrain V2 Express Controller active on http://localhost:${PORT}`);
  console.log(`[+] Health check: http://localhost:${PORT}/api/repobrain/health`);
  console.log(`[+] Verification Gates API: http://localhost:${PORT}/api/repobrain/gates`);
  console.log(`[+] Live SSE Loop: http://localhost:${PORT}/api/repobrain/prompt-loop`);
});

