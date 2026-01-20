# macOS dev setup

This repo is developed on macOS and deployed to a Pi over SSH.

## Virtual environment

A local venv lives at `.venv/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
```

## Lint

```bash
ruff check .
```

## Run CLI locally

Some subcommands require Pi-only tools (GPIO, libcamera). For local development:

- You can list CLI commands:

```bash
python -m slit_lamp_camera --help
```

- You can simulate a writable recording target by setting:

```bash
export SLITCAM_STORAGE_DIR=/tmp
python -m slit_lamp_camera usb-status
```
