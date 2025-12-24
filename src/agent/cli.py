"""Command-line interface for the KB-grounded financial content agent."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import AgentConfig
from .generate import draft_response
from .ingest import discover_documents, load_documents
from .index import build_index
from .retrieve import retrieve_snippets
from .seo_rules import apply_keywords
from .validate import check_compliance


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="KB-grounded financial content agent")
    parser.add_argument("--config", type=Path, help="Path to a config.json file")
    parser.add_argument("--query", type=str, help="User question to answer")
    parser.add_argument("--apply-seo", action="store_true", help="Append default SEO keywords")
    parser.add_argument("--limit", type=int, default=3, help="Limit the number of retrieved snippets")
    return parser


def run(args: argparse.Namespace) -> str:
    """Execute the CLI workflow."""
    config = AgentConfig.load(args.config)
    documents = load_documents(discover_documents(config.knowledge_base_path))
    index_path = build_index(documents, config.index_path)
    snippets: List[str] = []
    response = "No query provided."
    if args.query:
        snippets = retrieve_snippets(index_path, args.query, limit=args.limit)
        response = draft_response(args.query, snippets)
    if args.apply_seo:
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
