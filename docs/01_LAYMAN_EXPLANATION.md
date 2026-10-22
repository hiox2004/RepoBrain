# RepoBrain Explained in Plain English (Layman's Guide)

> **"What if your AI coding assistant had the memory of a senior engineer, the reading speed of an indexer, and a safety net that never lets it break your code?"**

---

## 1. The Core Problem: Why AI Coding Assistants Struggle

Today's AI coding tools (Claude Code, ChatGPT, Cursor, GitHub Copilot) are like brilliant, lightning-fast interns with three frustrating flaws:

1. **They have Goldfish Memory when files get large:** If you ask the AI to fix a bug in a 2,000-line file, it has to read the entire file. By the time it reaches line 1,500, it forgets what was on line 50. This is called **"Lost in the Middle" attention degradation**. Worse, you pay real money for every single line of code it reads over and over again!
2. **They are "Name Blind":** If you ask the AI to find `getUserById`, a standard AI vector search might hand it `updateUserById` or `deleteUser` because in the AI's mind, those phrases "sound conceptually related." But in programming, an exact name is the difference between showing a user their profile and wiping their account.
3. **They are Stubborn and Unsupervised:** When an AI's code edit fails a test, it panics. If left alone in a terminal, it will try random edits 10 or 15 times, make a mess of your project, and sometimes even **delete your test assertions** just so the tests pass!

---

## 2. What RepoBrain Does (The Senior Tech Lead Analogy)

**RepoBrain** sits between the AI and your codebase like a battle-tested Senior Tech Lead. It acts as the AI's **Memory**, **Search Engine**, and **Safety Harness**:

```
Developer Prompt ("Fix the invoice tax calculation in ledger.py")
                          │
                          ▼
             ┌─────────────────────────┐
             │       AI Assistant      │
             │ (Claude / Antigravity)  │
             └────────────┬────────────┘
                          │ Asks RepoBrain via MCP
                          ▼
             ┌─────────────────────────┐
             │        RepoBrain        │
             │  • Gives 1-page cue card│
             │  • Watches the sandbox  │
             │  • Records bug lessons  │
             └────────────┬────────────┘
                          │
                          ▼
            Safe, Verified Code on Disk
```

---

## 3. The 4 Compounding Layers (Explained Simply)

### Layer 1: Codebase Memory (Precision Cue Cards)
- **Without RepoBrain:** The AI reads a 5,000-word file just to fix one 5-line calculation.
- **With RepoBrain:** RepoBrain acts like a pair of surgical scissors. It cuts out *just* the function you care about (e.g. `settleInvoiceById`), clips the file's `import` statements onto the top like a sticky note, and hands the AI a tiny 1-page cue card.
- **The Result:** The AI only reads 300 words instead of 5,000. It is **90% cheaper**, lightning fast, and has 100% focused attention.

### Layer 2: Episodic Memory (The Bug Diary)
- **Without RepoBrain:** If the AI fixes a weird currency rounding bug on Tuesday, and you ask it to touch the same code on Friday, it will make the exact same mistake again.
- **With RepoBrain:** Whenever the AI fails a test and then successfully fixes it, RepoBrain writes a lesson in a permanent diary:
  > *"Lesson: Decimal calculations in `settleInvoiceById` must always be rounded using `.quantize(Decimal('0.01'))` or precision will fail."*
- Next time the AI touches that function, RepoBrain hands it the diary entry first. The AI **never repeats past mistakes**.

### Layer 3: ResearchBrain (The Bookshelf Before the Internet)
- **Without RepoBrain:** When an AI needs to look up a documentation detail, it starts scraping 50 web pages, downloading megabytes of HTML, advertisements, and navigation menus.
- **With RepoBrain:** RepoBrain keeps a curated shelf of local manuals, RFCs, and engineering decisions (`.repobrain/kb/`). If the answer is on the shelf, **0 internet tokens are spent**. If it must search the web, it grabs at most 1 page, strips all the junk, and compresses the answer into a tidy 200-word summary.

### Layer 4: Template Stockroom (The Proven Recipe Box)
- **Without RepoBrain:** When you ask the AI to write a new API endpoint or authentication flow, it writes code from memory, which often contains subtle security bugs or outdated patterns.
- **With RepoBrain:** RepoBrain keeps a library of battle-tested starter blueprints from top open-source projects (FastAPI, Shadcn, FastMCP). It tells the AI: *"Use this exact proven recipe, and cite line 12 of `tiangolo/full-stack-fastapi-template` to the developer."*

---

## 4. The Safety Harness (Why Your Code is Always Safe)

What happens when an AI writes bad code? RepoBrain enforces three unbreakable safety rules:

1. **The Sanctuary Shield:** The AI is strictly forbidden from touching sensitive files like `.env`, passwords, lockfiles (`uv.lock`, `package-lock.json`), or configuration files.
2. **The "Polaroid" Snapshot:** Before the AI touches a single file on your hard drive, RepoBrain takes an exact byte-for-byte snapshot of those files in memory.
3. **The 3-Strike Rule & Instant Undo:**
   - **Strike 1:** The AI tries a fix $\to$ test fails $\to$ RepoBrain gives it the error.
   - **Strike 2:** The AI refines its fix $\to$ test fails again.
   - **Strike 3:** The AI tries once more $\to$ if it still fails, RepoBrain **instantly rolls back only the touched files** to their original state.
   - **Crucially:** Unlike running `git reset --hard` (which destroys all uncommitted work across your entire project), RepoBrain's rollback is surgical—any files you were personally editing in your editor are completely safe and untouched!

---

## 5. End-to-End Walkthrough of a Typical Task

Let's see what happens step-by-step when you say: **"Fix the tax calculation bug in `src/billing/ledger.py`"**:

```
Step 1: AI calls search_codebase("settleInvoiceById decimal")
        └── RepoBrain finds the exact method using Hybrid Search.
        └── RepoBrain checks the Bug Diary: "Ah, remember to quantize currency!"
        └── RepoBrain hands the AI a clean XML snippet (400 tokens).

Step 2: AI writes a surgical unified diff (+ tax_rate instead of - tax_rate).

Step 3: AI calls apply_git_patch(diff)
        └── RepoBrain checks Sanctuary Policy (is it touching .env? No. Safe!).
        └── RepoBrain takes a memory snapshot of ledger.py.
        └── RepoBrain runs a 150ms syntax check (did it leave a syntax error? No).
        └── RepoBrain applies the patch and runs tests.

Step 4: Tests fail! (AssertionError: 120.0000 != 120.00).
        └── RepoBrain strips third-party noise and returns only the relevant error.

Step 5: AI calls apply_git_patch(diff_v2) with .quantize(Decimal("0.01")).
        └── Tests pass! (exit_code == 0).
        └── RepoBrain distills this win into the Layer 2 Bug Diary!
```

---

## 6. Summary in Numbers

| Feature | Standard AI Coding | With RepoBrain |
| :--- | :--- | :--- |
| **Tokens read per task** | 50,000 – 120,000 | 1,500 – 3,000 (**90% cheaper**) |
| **Exact function matching** | Often confuses similar names | 100% exact via Hybrid RRF |
| **Repeating old bugs** | Frequent across sessions | 0% (Protected by Bug Diary) |
| **Risk of broken worktree** | High (accidental overwrites) | Zero (Protected by Surgical Rollback) |
| **Max retry loops** | Unbounded (loops 10–15 times) | Strictly capped at $\le 3$ |

