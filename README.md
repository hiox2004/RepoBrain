# RepoBrain V2 & ResearchBrain OS

**Autonomous Codebase Memory, Self-Healing Bug Cache & Execution Harness**  
*Connecting frontier AI coding agents to local repositories over `stdio` FastMCP with zero context bloat and bounded execution.*

---

## 📚 Documentation & Study Guides

All documentation has been consolidated into the **[`docs/`](docs/)** directory:

| Document | Description |
| :--- | :--- |
| 📖 **[`docs/01_LAYMAN_EXPLANATION.md`](docs/01_LAYMAN_EXPLANATION.md)** | **E2E Layman's Guide:** The project explained in plain English with analogies. |
| 🎓 **[`docs/interactive/HOW_TO_OPEN_STUDY_GUIDE.md`](docs/interactive/HOW_TO_OPEN_STUDY_GUIDE.md)** | **Study Guide Instructions:** How to open the interactive HTML masterclass. |
| 🌐 **[`docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html`](docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html)** | **Interactive Web Masterclass:** Live visualizers, calculators, and self-test. |
| 🏛️ **[`docs/02_FOUNDING_ARCHITECTURE.md`](docs/02_FOUNDING_ARCHITECTURE.md)** | **Founding Architecture:** The 5 Pillars, 8 Guardrails, and PostgreSQL DDL. |
| 🔍 **[`docs/03_SYSTEM_STATUS_AND_AUDIT.md`](docs/03_SYSTEM_STATUS_AND_AUDIT.md)** | **Status & CTO Defense:** Line-by-line codebase audit and self-answered CTO Q&A. |
| 🗺️ **[`docs/README.md`](docs/README.md)** | **Master Portal:** Reading paths from beginner to senior architect. |

---

## ⚡ Quick Start: Open the Interactive Study Guide

To launch the interactive HTML masterguide in your browser immediately:

```powershell
Start-Process "docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html"
```

---

## 🧪 Quick Start: Run Tests & Verification Gates

```powershell
# 1. Run full 14-test verification suite:
python -m unittest discover tests

# 2. Run the 4-Gate Deterministic Stress Test against src/billing/ledger.py:
python src/repobrain/verify_gates.py
```

