#!/usr/bin/env bash
# Instalador do projeto Roteiro + Narracao (macOS / Linux)
# Uso: bash instalar.sh [--cpu] [--sem-modelo]
set -euo pipefail
cd "$(dirname "$0")"

CPU=0; SEM_MODELO=0
for a in "$@"; do
  case "$a" in --cpu) CPU=1 ;; --sem-modelo) SEM_MODELO=1 ;; esac
done
TORCH=2.8.0
passo() { printf '\n==> %s\n' "$1"; }

passo "Verificando o uv"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv nao encontrado. Instale com:"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "Depois abra um novo terminal e rode este instalador de novo."
  exit 1
fi
uv --version

passo "Criando o ambiente Python (.venv, Python 3.11)"
[ -x .venv/bin/python ] || uv venv .venv --python 3.11
PY="$(pwd)/.venv/bin/python"

passo "Instalando PyTorch $TORCH"
if [ "$(uname)" = "Darwin" ]; then
  uv pip install --python "$PY" "torch==$TORCH" "torchaudio==$TORCH"
elif [ $CPU -eq 0 ] && command -v nvidia-smi >/dev/null 2>&1; then
  uv pip install --python "$PY" "torch==$TORCH" "torchaudio==$TORCH" --index-url https://download.pytorch.org/whl/cu128
else
  uv pip install --python "$PY" "torch==$TORCH" "torchaudio==$TORCH" --index-url https://download.pytorch.org/whl/cpu
fi

passo "Instalando OmniVoice e dependencias"
uv pip install --python "$PY" -e .

mkdir -p roteiros voices "narrações"
export PYTHONUTF8=1
if [ $SEM_MODELO -eq 0 ]; then
  passo "Baixando o modelo OmniVoice (so na primeira vez)"
  "$PY" -m narrador baixar-modelo
fi
passo "Diagnostico final"
"$PY" -m narrador diagnostico
echo
echo "Instalacao concluida! Coloque uma voz em voices/ (veja voices/LEIA-ME.txt)"
echo "e abra esta pasta no Claude Code."
