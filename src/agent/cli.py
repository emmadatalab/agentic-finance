"""Command-line interface for the KB-grounded financial content agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .config import AgentConfig
from .generate import draft_response
from .ingest import ingest_knowledge_base
from .index import DEFAULT_MODEL, build_index
from .retrieve import RetrievedChunk, retrieve_chunks
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

    index_parser = subparsers.add_parser("index", help="Build a FAISS index from processed KB JSONL")
    index_parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/kb_processed/kb.jsonl"),
        help="Path to processed kb.jsonl file",
    )
    index_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/index"),
        help="Directory where the FAISS index and metadata should be written",
    )
    index_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="SentenceTransformer model name to use for embeddings (defaults to all-MiniLM-L6-v2)",
    )
    index_parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size in characters")
    index_parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap in characters")
    index_parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")

    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve chunks from the FAISS index")
    retrieve_parser.add_argument("--config", type=Path, help="Path to a config.json file")
    retrieve_parser.add_argument("--query", type=str, required=True, help="Query string to search for")
    retrieve_parser.add_argument("--topk", type=int, default=3, help="Number of chunks to return")

    query_parser = subparsers.add_parser("query", help="Run the end-to-end query workflow")
    query_parser.add_argument("--config", type=Path, help="Path to a config.json file")
    query_parser.add_argument("--query", type=str, help="User question to answer")
    query_parser.add_argument("--apply-seo", action="store_true", help="Append default SEO keywords")
    query_parser.add_argument(
        "--limit", type=int, default=3, help="Limit the number of retrieved snippets in the response"
    )

    write_parser = subparsers.add_parser("write", help="Generate a Markdown article from the KB")
    write_parser.add_argument("--config", type=Path, help="Path to a config.json file")
    write_parser.add_argument("--topic", type=str, required=True, help="Article topic to write about")
    write_parser.add_argument(
        "--limit", type=int, default=5, help="Number of retrieved snippets to ground the article"
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

    if args.command == "index":
        index_path = build_index(
            kb_path=args.input,
            index_dir=args.output,
            model_name=args.model or DEFAULT_MODEL,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size,
        )
        return f"Built index at {index_path}"

    config_path = getattr(args, "config", None)
    config = AgentConfig.load(config_path)
    kb_path = config.knowledge_base_path
    index_dir = config.index_path
    index_path = index_dir / "index.faiss"
    if not index_path.exists():
        build_index(kb_path=kb_path, index_dir=index_dir)

    if args.command == "retrieve":
        results = retrieve_chunks(index_dir=index_dir, query=args.query, top_k=args.topk)
        return json.dumps([chunk.to_dict() for chunk in results], ensure_ascii=False, indent=2)

    topic: str | None = None
    if args.command == "write":
        topic = args.topic
    else:
        topic = getattr(args, "query", None)

    chunks: List[RetrievedChunk] = []
    response = "No query provided."
    if topic:
        chunks = retrieve_chunks(index_dir=index_dir, query=topic, top_k=args.limit)
        response = draft_response(topic, chunks)
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
