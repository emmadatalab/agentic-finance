"""Command-line interface for the KB-grounded financial content agent."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import AgentConfig
from .generate import draft_response
from .ingest import discover_documents, ingest_knowledge_base, load_documents
from .index import build_index
from .retrieve import retrieve_snippets
from .seo_rules import apply_keywords
from .validate import check_compliance


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="KB-grounded financial content agent")
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest raw KB files into a JSONL corpus")
    ingest_parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/kb_raw"),
        help="Directory containing raw knowledge base files (pdf/md/txt)",
    )
    ingest_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/kb_processed/kb.jsonl"),
        help="Destination JSONL file for processed documents",
    )

    query_parser = subparsers.add_parser("query", help="Run the end-to-end query workflow")
    query_parser.add_argument("--config", type=Path, help="Path to a config.json file")
    query_parser.add_argument("--query", type=str, help="User question to answer")
    query_parser.add_argument("--apply-seo", action="store_true", help="Append default SEO keywords")
    query_parser.add_argument(
        "--limit", type=int, default=3, help="Limit the number of retrieved snippets in the response"
    )

    # Support legacy invocation without a subcommand.
    parser.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--query", type=str, help=argparse.SUPPRESS)
    parser.add_argument("--apply-seo", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--limit", type=int, default=3, help=argparse.SUPPRESS)
    return parser


def run(args: argparse.Namespace) -> str:
    """Execute the CLI workflow."""
    if args.command == "ingest":
        documents = ingest_knowledge_base(args.raw_dir, args.output)
        return f"Ingested {len(documents)} documents into {args.output}"

    config_path = getattr(args, "config", None)
    config = AgentConfig.load(config_path)
    documents = load_documents(discover_documents(config.knowledge_base_path))
    index_path = build_index(documents, config.index_path)
    snippets: List[str] = []
    response = "No query provided."
    query = getattr(args, "query", None)
    if query:
        snippets = retrieve_snippets(index_path, query, limit=args.limit)
        response = draft_response(query, snippets)
    if getattr(args, "apply_seo", False):
        response = apply_keywords(response)
    warnings = check_compliance(response)
    if warnings:
        warning_text = "\n".join(f"Warning: {warning}" for warning in warnings)
        response = f"{response}\n\n{warning_text}"
    return response


def main() -> None:
    """Entry point used by python -m agent.cli."""
    parser = build_parser()
    args = parser.parse_args()
    output = run(args)
    print(output)


if __name__ == "__main__":
    main()
