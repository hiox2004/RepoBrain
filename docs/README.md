# RepoBrain Documentation Portal

Welcome to the **RepoBrain** documentation library. This folder is organized hierarchically so you can explore the project at whatever depth matches your current needs—from high-level intuition to low-level byte-slicing math.

---

## 🗺️ Documentation Directory Map

```
docs/
├── README.md                          <-- (You are here) Master Portal & Reading Paths
├── 01_LAYMAN_EXPLANATION.md           <-- Plain English: E2E project guide & analogies
├── 02_FOUNDING_ARCHITECTURE.md        <-- Full Technical Spec: 5 Pillars & 8 Guardrails
├── 03_SYSTEM_STATUS_AND_AUDIT.md      <-- Technical Audit: Where we are now & CTO Q&A
└── interactive/
    ├── 04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html  <-- Living Interactive Masterclass
    └── HOW_TO_OPEN_STUDY_GUIDE.md    <-- Instructions to open the HTML in your browser
```

---

## 📖 Recommended Reading Paths

### Path A: "Explain it to me like I'm 5" (10 minutes)
1. Read **[`01_LAYMAN_EXPLANATION.md`](01_LAYMAN_EXPLANATION.md)**:
   - Understand why standard AI coding tools fail on real codebases.
   - Learn the 4 Layers through simple real-world analogies.
   - Walk through an end-to-end task from prompt to verified patch.

### Path B: "Show me the Interactive Visualizer" (15 minutes)
1. Read **[`interactive/HOW_TO_OPEN_STUDY_GUIDE.md`](interactive/HOW_TO_OPEN_STUDY_GUIDE.md)**.
2. Launch **[`interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html`](interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html)** in your browser using:
   ```powershell
   Start-Process "docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html"
   ```
3. Use the **Reading Depth Switcher** (Beginner $\to$ Senior Engineer $\to$ CTO), test the **UTF-8 Byte Slicer Simulator**, and take the **8-question self-assessment**.

### Path C: "I am a Systems Architect / Senior Developer" (30 minutes)
1. Read **[`02_FOUNDING_ARCHITECTURE.md`](02_FOUNDING_ARCHITECTURE.md)**:
   - Inspect the mathematical formulation of Two-Stage Hybrid RRF ($k=60$).
   - Review the UTF-8 byte boundary invariant (`Guardrail #1`).
   - Examine the 5 FastMCP tools and stdio hygiene rules.
2. Read **[`03_SYSTEM_STATUS_AND_AUDIT.md`](03_SYSTEM_STATUS_AND_AUDIT.md)**:
   - Review the line-by-line implementation status of every module.
   - Read the self-answered CTO interview addressing database topologies, latency, and sandbox security.

---

## 🧪 Verification & Running Tests

To verify that all systems described in these documents are 100% operational in code:

```powershell
# Run the 14-test unit & integration suite:
python -m unittest discover tests

# Run the 4-Gate Deterministic Stress Test:
python src/repobrain/verify_gates.py
```

