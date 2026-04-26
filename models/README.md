# Local model checkpoints

Drop your sentence-transformers checkpoint directory here, then point
`LOCAL_EMBEDDING_MODEL_PATH` in `.env` at it.

This directory is **gitignored** — model weights are too big to commit.

## Recommended layout

```
models/
├── README.md                    ← this file (committed)
├── .gitkeep                     ← keeps the dir in git (committed)
└── qwen3-embedding-0.6B/        ← your downloaded checkpoint (NOT committed)
    ├── config.json
    ├── tokenizer.json
    ├── tokenizer_config.json
    ├── model.safetensors
    ├── modules.json                       ← ★ ST-specific
    ├── config_sentence_transformers.json  ← ★
    ├── sentence_bert_config.json          ← ★
    └── 1_Pooling/                         ← ★
        └── config.json
```

## How to populate

On a machine that has HuggingFace network access:

```bash
pip install huggingface_hub
huggingface-cli download Qwen/Qwen3-Embedding-0.6B \
  --local-dir ./qwen3-embedding-0.6B \
  --local-dir-use-symlinks False

# tar it, ship it into your fab environment, untar into ./models/
tar czf qwen3-embedding-0.6B.tgz qwen3-embedding-0.6B/
```

Then in your fab environment:

```bash
cd /path/to/rca-knowledge-poc
tar xzf /path/to/qwen3-embedding-0.6B.tgz -C models/

# wire .env:
sed -i.bak 's|^LOCAL_EMBEDDING_MODEL_PATH=.*|LOCAL_EMBEDDING_MODEL_PATH=./models/qwen3-embedding-0.6B|' .env
sed -i 's|^EMBEDDING_DIMENSIONS=.*|EMBEDDING_DIMENSIONS=1024|' .env

./scripts/demo.sh
```

## Alternative locations

If you'd rather centralize models system-wide (shared across projects), set:

```
LOCAL_EMBEDDING_MODEL_PATH=/opt/models/qwen3-embedding-0.6B
LOCAL_EMBEDDING_MODEL_PATH=/home/$USER/models/qwen3-embedding-0.6B
```

The embedding-server accepts any absolute or relative path; relative paths
are resolved against the project root (where `pyproject.toml` lives).

## Dim cheat-sheet

Set `EMBEDDING_DIMENSIONS` in `.env` to match your model:

| Model | Dim |
|---|---|
| Qwen3-Embedding-0.6B | 1024 |
| Qwen3-Embedding-4B | 2560 |
| Qwen3-Embedding-8B | 4096 |
| BAAI/bge-large-en-v1.5 | 1024 |
| BAAI/bge-base-en-v1.5 | 768 |
| sentence-transformers/all-MiniLM-L6-v2 | 384 |

If you set the wrong dim, cognee's vector store will reject writes with a
clear dimension-mismatch error on the first /retain call.
