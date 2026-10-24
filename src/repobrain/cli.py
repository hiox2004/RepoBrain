# src/repobrain/cli.py
"""
RepoBrain V2 & ResearchBrain OS Unified CLI
Enables developers to index repositories, search symbols via Hybrid RRF,
research topics via 5-Phase CRAG, inspect distilled episodes, and run verification gates.
"""

from __future__ import annotations
import argparse
import json
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from typing import List

# Ensure src is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from repobrain.ast_chunker import ASTCodeChunker
from repobrain.hybrid_retriever import HybridCodebaseRetriever
from repobrain.storage_sqlite import SQLiteStorageTier


def cmd_index(args: argparse.Namespace) -> None:
    target_dir = Path(args.path).resolve()
    print(f"[*] Indexing codebase at: {target_dir}")
    chunker = ASTCodeChunker()
    storage = SQLiteStorageTier(db_path=target_dir / ".repobrain" / "repobrain.db")

    count_parents = 0
    count_children = 0

    for ext in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx"):
        for file_p in target_dir.glob(f"**/{ext}"):
            # Skip hidden, virtualenv, and node_modules
            parts = file_p.parts
            if any(p.startswith(".") or p in ("node_modules", "dist", "build", "venv", ".venv", "__pycache__") for p in parts):
                continue
            try:
                parent, children = chunker.chunk_file(file_p, repo_root=target_dir)
                storage.upsert_parent_and_children(parent, children)
                count_parents += 1
                count_children += len(children)
            except Exception as e:
                print(f"[!] Warning: failed to parse {file_p.name}: {e}", file=sys.stderr)

    print(f"[+] Successfully indexed {count_parents} files into {count_children} AST child nodes!")
    print(f"[+] Persisted to local SQLite store: {storage.db_path}")
    storage.close()


def cmd_search(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo).resolve()
    retriever = HybridCodebaseRetriever(repo_root=repo_root)

    # Load from SQLite storage into retriever memory mirror
    storage = SQLiteStorageTier(db_path=repo_root / ".repobrain" / "repobrain.db")
    for parent, child in storage.get_all_children_with_parents():
        retriever.parents_db[parent.file_path] = parent
        if parent.file_path not in retriever.children_db:
            retriever.children_db[parent.file_path] = []
        retriever.children_db[parent.file_path].append(child)
    storage.close()

    print(f"[*] Executing Two-Stage Hybrid RRF (k=60) query: '{args.query}'")
    results = retriever.search(args.query, top_k=args.top_k, include_episodes=True)

    if not results:
        print("[-] No matching symbols found. Did you run 'repobrain index' first?")
        return

    print(f"\n[+] Found {len(results)} matching code context blocks:\n")
    for idx, res in enumerate(results, start=1):
        print(f"--- Result #{idx}: {res.symbol_name} ({res.node_kind}) [RRF: {res.rrf_score:.5f}, Rerank: {res.cross_encoder_score:.4f}] ---")
        print(res.to_xml_prompt_block())
        print()


def cmd_research(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo).resolve()
    retriever = HybridCodebaseRetriever(repo_root=repo_root)
    print(f"[*] Executing ResearchBrain 5-Phase CRAG on: '{args.topic}'")
    brief = retriever.research_brain.research_technology(args.topic, domain=args.domain)

    print(f"\n[+] Research Source: {brief.source.upper()} (Confidence: {brief.confidence_score:.2f})")
    print(brief.summary_markdown)


def cmd_templates(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo).resolve()
    retriever = HybridCodebaseRetriever(repo_root=repo_root)
    print(f"[*] Searching Template Stockroom for: '{args.query}' (Domain: {args.domain})")
    blueprints = retriever.template_stockroom.search_templates(args.query, stack_domain=args.domain)

    if not blueprints:
        print("[-] No matching blueprints found.")
        return

    print(f"\n[+] Found {len(blueprints)} verified starter blueprints:\n")
    for bp in blueprints:
        print(bp.to_advisory_markdown())
        print("-" * 60)


def cmd_episodes(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo).resolve()
    storage = SQLiteStorageTier(db_path=repo_root / ".repobrain" / "repobrain.db")
    episodes = storage.find_matching_episodes(limit=args.limit)

    if not episodes:
        print("[-] No distilled episodes recorded in this repository yet.")
        storage.close()
        return

    print(f"[+] Found {len(episodes)} distilled fail-to-pass bug lessons:\n")
    for idx, ep in enumerate(episodes, start=1):
        print(f"--- Episode #{idx}: {ep.target_symbol} ({ep.file_path}) ---")
        print(f"Error: {ep.error_signature}")
        print(f"Root Cause: {ep.root_cause_summary}")
        print(f"Diff:\n{ep.resolution_diff}\n")
    storage.close()


def cmd_verify(args: argparse.Namespace) -> None:
    from repobrain.verify_gates import run_gate1, run_gate2, run_gate3, run_gate4
    print("[*] Running RepoBrain 4-Gate Deterministic Verification Stress Test...\n")
    run_gate1()
    run_gate2()
    run_gate3()
    run_gate4()
    print("\n[+] ALL 4 VERIFICATION GATES DETERMINISTICALLY VERIFIED!")



def cmd_blast_radius(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo).resolve()
    retriever = HybridCodebaseRetriever(repo_root=repo_root)
    print(f"[*] Analyzing blast radius for symbol: '{args.symbol}'")
    report = retriever.compute_blast_radius(args.symbol, file_path=args.file)

    print(f"\n[+] Symbol: {report['symbol_name']} (Risk Level: {report['risk_level']})")
    print(f"[+] Callers Detected ({report['callers_count']}):")
    for caller in report.get("callers", []):
        print(f"    - {caller['file_path']} :: {caller['symbol_name']} (Lines {caller['lines']})")
    print(f"[+] Associated Test Suites ({report['associated_tests_count']}):")
    for t in report.get("associated_tests", []):
        print(f"    - {t}")
    print(f"\n[!] Advisory: {report['advisory']}")


def cmd_benchmark(args: argparse.Namespace) -> None:
    from repobrain.benchmark import run_scientific_benchmarks
    print("[*] Running RepoBrain Live Dual-Experiment Benchmark Suite...\n")
    results = run_scientific_benchmarks(repo_root=Path(args.repo).resolve())
    print(json.dumps(results, indent=2))



def cmd_watch(args: argparse.Namespace) -> None:
    from repobrain.watcher import RetrieverWatcher
    repo_root = Path(args.repo).resolve()
    print(f"[*] Starting RepoBrain File Watcher daemon on {repo_root} (interval: {args.interval}s)")
    watcher = RetrieverWatcher(repo_root=repo_root, poll_interval_seconds=args.interval)
    if args.once:
        synced = watcher.sync_once()
        print(f"[+] Sync completed. Synced {len(synced)} changed file(s): {synced}")
        return

    watcher.start()
    print("[+] Watcher running in background. Press Ctrl+C to terminate.")
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping Watcher daemon...")
        watcher.stop()
        print("[+] Daemon gracefully stopped.")


def cmd_heal(args: argparse.Namespace) -> None:
    from repobrain.ci_heal import CIHealingOrchestrator
    repo_root = Path(args.repo).resolve()
    print(f"[*] Autonomous CI Self-Healing initiated on '{args.test_path}'...")
    orchestrator = CIHealingOrchestrator(repo_root=repo_root)
    result = orchestrator.diagnose_and_heal(
        test_path=args.test_path,
        target_file=args.target_file,
        max_iterations=args.max_iterations,
    )
    print(f"\n[+] Healing Verdict: {result['status']}")
    print(f"[+] Message: {result['message']}")
    if result.get("pr_comment_markdown"):
        print("\n--- GitHub PR Comment Markdown ---\n")
        print(result["pr_comment_markdown"])
    if args.output_file and result.get("pr_comment_markdown"):
        out_p = Path(args.output_file).resolve()
        out_p.write_text(result["pr_comment_markdown"], encoding="utf-8")
        print(f"\n[+] Wrote PR comment to {out_p}")

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="repobrain",
        description="RepoBrain V2 & ResearchBrain OS: Autonomous Codebase Memory & Execution Harness",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # index
    p_index = subparsers.add_parser("index", help="Index a repository into local SQLite AST storage")
    p_index.add_argument("path", nargs="?", default=".", help="Path to codebase root")

    # search
    p_search = subparsers.add_parser("search", help="Execute Two-Stage Hybrid RRF (k=60) codebase search")
    p_search.add_argument("query", help="Symbol or natural-language query")
    p_search.add_argument("--repo", default=".", help="Repository root path")
    p_search.add_argument("--top-k", type=int, default=5, help="Number of results to return")

    # research
    p_research = subparsers.add_parser("research", help="Research a topic via 5-Phase CRAG")
    p_research.add_argument("topic", help="Topic, library, or architectural concept")
    p_research.add_argument("--repo", default=".", help="Repository root path")
    p_research.add_argument("--domain", default="general_tech", help="Technical domain filter")

    # templates
    p_templates = subparsers.add_parser("templates", help="Search GitHub Template Stockroom starter blueprints")
    p_templates.add_argument("query", help="Scaffolding query (e.g. oauth2, fastapi, mcp)")
    p_templates.add_argument("--repo", default=".", help="Repository root path")
    p_templates.add_argument("--domain", default="all", help="Stack domain filter")

    # episodes
    p_episodes = subparsers.add_parser("episodes", help="List distilled fail-to-pass episodic bug lessons")
    p_episodes.add_argument("--repo", default=".", help="Repository root path")
    p_episodes.add_argument("--limit", type=int, default=10, help="Max episodes to display")

    # blast-radius
    p_blast = subparsers.add_parser("blast-radius", help="Calculate static blast radius & dependent callers for a symbol")
    p_blast.add_argument("symbol", help="Target symbol name (e.g. compute_git_blob_sha, SanctuaryPolicyGuard)")
    p_blast.add_argument("--file", default=None, help="Optional relative file path constraint")
    p_blast.add_argument("--repo", default=".", help="Repository root path")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run comprehensive dual-experiment token & speed benchmarks")
    p_bench.add_argument("--repo", default=".", help="Repository root path")

    # verify
    p_verify = subparsers.add_parser("verify", help="Run the 4-Gate Deterministic Stress Test")

    # watch
    p_watch = subparsers.add_parser("watch", help="Start background file watcher daemon for real-time AST sync")
    p_watch.add_argument("--repo", default=".", help="Repository root path")
    p_watch.add_argument("--interval", type=float, default=0.5, help="Polling interval in seconds")
    p_watch.add_argument("--once", action="store_true", help="Run a single sync check and exit")

    # heal
    p_heal = subparsers.add_parser("heal", help="Autonomous CI self-healing for failing test suites")
    p_heal.add_argument("test_path", help="Path to failing test suite")
    p_heal.add_argument("--target-file", default=None, help="Target implementation file")
    p_heal.add_argument("--max-iterations", type=int, default=3, help="Max self-healing iterations")
    p_heal.add_argument("--repo", default=".", help="Repository root path")
    p_heal.add_argument("--output-file", default=None, help="Output markdown report file for PR comment")

    args = parser.parse_args()
    if args.command == "index":
        cmd_index(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "research":
        cmd_research(args)
    elif args.command == "templates":
        cmd_templates(args)
    elif args.command == "episodes":
        cmd_episodes(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "blast-radius":
        cmd_blast_radius(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "heal":
        cmd_heal(args)


if __name__ == "__main__":
    main()
