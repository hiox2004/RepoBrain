# RepoBrain V2 & ResearchBrain OS

**Autonomous Codebase Memory, Self-Healing Bug Cache & Execution Harness**  
*Connecting frontier AI coding agents (Google Antigravity, Claude Code, Cursor, Windsurf) to local repositories over `stdio` FastMCP with zero context bloat and bounded execution.*

---

## ⚡ Quick Start: Connect to Claude Code in 10 Seconds

```powershell
# 1. Register RepoBrain as an MCP server in Claude Code:
claude mcp add repobrain -- python -m repobrain.server

# 2. Launch Claude Code in interactive terminal:
claude
```

---

## 📚 Documentation & User Guides

All documentation and technical specifications are organized in the **[`docs/`](docs/)** directory:

| Document | Description |
| :--- | :--- |
| 🚀 **[`docs/06_SETUP_AND_USER_MANUAL.md`](docs/06_SETUP_AND_USER_MANUAL.md)** | **Setup & User Manual:** Antigravity, Claude Code, Cursor, 6 tools reference, and troubleshooting. |
| 📖 **[`docs/01_LAYMAN_EXPLANATION.md`](docs/01_LAYMAN_EXPLANATION.md)** | **E2E Layman's Guide:** The project explained in plain English with analogies. |
| 🎓 **[`docs/interactive/HOW_TO_OPEN_STUDY_GUIDE.md`](docs/interactive/HOW_TO_OPEN_STUDY_GUIDE.md)** | **Study Guide Instructions:** How to open the interactive HTML masterclass. |
| 🌐 **[`docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html`](docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html)** | **Interactive Web Masterclass:** 15 modules, live simulators, calculators, and self-test. |
| 🏛️ **[`docs/02_FOUNDING_ARCHITECTURE.md`](docs/02_FOUNDING_ARCHITECTURE.md)** | **Founding Architecture:** The 5 Pillars, 8 Guardrails, LangGraph CRAG, and PostgreSQL DDL. |
| 🔍 **[`docs/03_SYSTEM_STATUS_AND_AUDIT.md`](docs/03_SYSTEM_STATUS_AND_AUDIT.md)** | **Status & CTO Defense:** Line-by-line codebase audit and self-answered CTO Q&A. |
| 🤖 **[`docs/05_MULTI_AGENT_SYSTEM_OF_WORKING.md`](docs/05_MULTI_AGENT_SYSTEM_OF_WORKING.md)** | **Multi-Agent Topology:** Roles, state transitions, LangGraph CRAG, and Antigravity protocol. |
| 🗺️ **[`docs/README.md`](docs/README.md)** | **Master Portal:** Reading paths from beginner to staff systems architect. |

---

## 🖥️ Launch the Full-Stack Workbench & In-App Masterguide

RepoBrain features a full-stack React workbench with 8 interactive views:

```powershell
# Terminal 1: Launch Express Bridge (Port 3001)
node server.js

# Terminal 2: Launch Vite React UI (Port 5173)
npm run dev
```
Open `http://localhost:5173` to explore:
* **4-Gate Verification:** Live execution of deterministic stress tests.
* **Masterguide & Docs:** 15-module interactive academy with reading depth switcher.
* **AST Explorer & UTF-8:** Live visualizer of sub-symbol AST slicing.
* **Hybrid RRF Calculator:** Step-by-step $k=60$ score calculator.
* **Harness Simulator:** Bounded $\le 3$-retry retry and surgical byte rollback sandbox.

---

## 🧪 Run Tests & Verification Gates

```powershell
# 1. Run full 38-test unit & integration suite:
python -m unittest discover tests

# 2. Run the 4-Gate Deterministic Stress Test:
python src/repobrain/verify_gates.py

# 3. Verify frontend production build:
npm run build
```
