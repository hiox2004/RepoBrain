# How to Open & Study the Interactive CTO Masterguide

The **RepoBrain CTO Masterguide** (`04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html`) is a standalone, interactive web application featuring:
- **Reading Depth Switcher:** Toggle between Beginner, Senior Engineer, and CTO perspectives.
- **Interactive UTF-8 Simulator:** Visual proof of byte slicing vs. string character drift on `€`, `≤`, `→`.
- **Identifier Split Visualizer:** Real-time demonstration of `normalize_code_identifiers()`.
- **RRF (k=60) Interactive Calculator:** Step-by-step mathematical score breakdown.
- **8-Question Architecture Self-Assessment:** Test your mastery of RepoBrain's invariants.

---

## Method 1: Instant PowerShell Launch (Fastest)

Run this one-liner in your terminal (PowerShell) to open it immediately in your default browser (Chrome, Edge, Brave, etc.):

```powershell
Start-Process "docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html"
```

Or from the repository root:
```powershell
Invoke-Item ".\RepoBrain\docs\interactive\04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html"
```

---

## Method 2: From Windows File Explorer

1. Open File Explorer.
2. Navigate to:  
   `C:\Users\hiox2\Desktop\PROJECTS\RepoBrain\RepoBrain\docs\interactive\`
3. **Double-click** on `04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html`.
4. It will open instantly in your web browser. No server or internet connection is required—it is 100% self-contained.

---

## Method 3: From Inside VS Code

- **Option A:** Right-click `04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html` in the VS Code file tree $\to$ Select **"Open in Default Browser"** or **"Reveal in File Explorer"**.
- **Option B (Live Server extension):** If you have the "Live Server" extension installed, right-click the file $\to$ **"Open with Live Server"**.
- **Option C (Simple Browser):** Press `Ctrl + Shift + P` $\to$ type `Simple Browser: Show` $\to$ paste the file's absolute path:
  `file:///C:/Users/hiox2/Desktop/PROJECTS/RepoBrain/RepoBrain/docs/interactive/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html`

---

## Method 4: Local Lightweight HTTP Server (Python)

If you want to view it via a local URL (e.g., `http://localhost:8080`):

```powershell
python -m http.server 8080 --directory "docs/interactive"
```
Then open your browser to:  
👉 **http://localhost:8080/04_REPOBRAIN_COMPLETE_CTO_MASTERGUIDE.html**

