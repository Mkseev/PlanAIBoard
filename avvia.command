#!/bin/bash
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then echo "Serve Python 3: installalo da python.org e riprova."; read -n 1 -p "Premi un tasto"; exit 1; fi
exec python3 sistema.py
