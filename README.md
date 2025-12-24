# KB-grounded financial content agent

This repository provides a minimal Python project skeleton for an agent that ingests financial knowledge base content, indexes it, retrieves grounded snippets, and drafts responses with light SEO and compliance helpers.

## Running the CLI

The CLI is runnable with the module entrypoint:

```bash
python -m agent.cli --help
```

When running from a fresh clone, either install the project (for example with `pip install -e .`) or set `PYTHONPATH=src` so Python can locate the `agent` package.

### Ingest raw documents

Place `.pdf`, `.md`, or `.txt` files in `data/kb_raw/` (populated at runtime only). Then run:

```bash
python -m agent.cli ingest
```

This writes `data/kb_processed/kb.jsonl` with normalized fields (`doc_id`, `title`, `source_path`, `text`, `created_at`, `risk_level`). Scanned PDFs without extractable text are skipped.

You can provide a query and optional SEO keyword injection:

```bash
python -m agent.cli query --query "What are diversification benefits?" --apply-seo
```

Configuration defaults are read from `config.json` when present. Raw knowledge base files are expected under `data/kb_raw`, processed output is written to `data/kb_processed/kb.jsonl`, and an index file is written to `data/index`.
