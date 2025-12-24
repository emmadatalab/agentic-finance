# KB-grounded financial content agent

This repository provides a minimal Python project skeleton for an agent that ingests financial knowledge base content, indexes it, retrieves grounded snippets, and drafts responses with light SEO and compliance helpers.

## Running the CLI

The CLI is runnable with the module entrypoint:

```bash
python -m agent.cli --help
```

When running from a fresh clone, either install the project (for example with `pip install -e .`) or set `PYTHONPATH=src` so Python can locate the `agent` package.

You can provide a query and optional SEO keyword injection:

```bash
python -m agent.cli --query "What are diversification benefits?" --apply-seo
```

Configuration defaults are read from `config.json` when present. Knowledge base files are expected under `data/knowledge_base` and an index file is written to `data/index`.

## Ingesting raw knowledge base files

To normalize local documents (markdown, text, or readable PDFs) into a processed JSONL file, run:

```bash
python -m agent.cli ingest
```

By default this reads from `data/kb_raw/` and writes to `data/kb_processed/kb.jsonl`. Provide `--raw-dir` and `--output` to override these paths. Scanned PDFs without extractable text are skipped.

PDF ingestion requires the optional dependency `pypdf`. Install it locally (for example with `pip install pypdf`) when your corpus includes PDFs.
