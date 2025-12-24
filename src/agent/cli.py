"""Command-line interface for the KB-grounded financial content agent."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import AgentConfig
from .generate import draft_response
from .ingest import discover_documents, ingest_documents, load_documents
from .index import build_index
from .retrieve import retrieve_snippets
from .seo_rules import apply_keywords
from .validate import check_compliance


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="KB-grounded financial content agent")
    parser.add_argument("--config", type=Path, help="Path to a config.json file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest raw documents into kb.jsonl")
    ingest_parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing raw documents (defaults to config knowledge_base_path)",
    )
    ingest_parser.add_argument(
        "--output",
        type=Path,
        help="JSONL output file (defaults to config processed_output_path)",
    )

    query_parser = subparsers.add_parser("query", help="Query the agent with a prompt")
    query_parser.add_argument("--query", type=str, required=True, help="User question to answer")
    query_parser.add_argument("--apply-seo", action="store_true", help="Append default SEO keywords")
    query_parser.add_argument(
        "--limit", type=int, default=3, help="Limit the number of retrieved snippets"
    )
    return parser


def handle_query(args: argparse.Namespace, config: AgentConfig) -> str:
    """Execute the query workflow."""
    documents = load_documents(discover_documents(config.knowledge_base_path))
    index_path = build_index(documents, config.index_path)
    snippets: List[str] = retrieve_snippets(index_path, args.query, limit=args.limit)
    response = draft_response(args.query, snippets)
    if args.apply_seo:
        response = apply_keywords(response)
    warnings = check_compliance(response)
    if warnings:
        warning_text = "\n".join(f"Warning: {warning}" for warning in warnings)
        response = f"{response}\n\n{warning_text}"
    return response


def handle_ingest(args: argparse.Namespace, config: AgentConfig) -> str:
    """Run ingestion and report summary."""
    input_dir = args.input_dir or config.knowledge_base_path
    output = args.output or config.processed_output_path
    processed, skipped = ingest_documents(input_dir, output)
    return (
        f"Ingested {processed} document(s) into {output}. "
        f"Skipped {skipped} file(s) without extractable text."
    )


def main() -> None:
    """Entry point used by python -m agent.cli."""
    parser = build_parser()
    args = parser.parse_args()
    config = AgentConfig.load(args.config)
    if args.command == "ingest":
        print(handle_ingest(args, config))
    elif args.command == "query":
        print(handle_query(args, config))
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
