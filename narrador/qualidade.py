"""Conferência automática de cada parte gerada."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache

import numpy as np


def inspecionar(audio: np.ndarray, sr: int, texto: str, cps_ref: float | None) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia = parte aprovada).

    cps_ref: caracteres por segundo medidos nas partes anteriores (ou None no início).
    """
    problemas: list[str] = []
    dur = len(audio) / sr
    if dur < 0.3:
        return ["áudio vazio"]
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    if rms < 1e-3:
        problemas.append("quase silencioso")
    if float(np.mean(np.abs(audio) > 0.999)) > 0.001:
        problemas.append("distorção (clipping)")
    cps = cps_ref or 14.0      # fala típica: ~12-16 caracteres por segundo
    esperado = max(len(texto) / cps, 0.6)
    razao = dur / esperado
    if razao < 0.55:
        problemas.append(f"curto demais ({dur:.1f}s, esperado ~{esperado:.1f}s): pode ter pulado texto")
    elif razao > 1.8:
        problemas.append(f"longo demais ({dur:.1f}s, esperado ~{esperado:.1f}s): pode ter repetido ou travado")
    return problemas


def _normalizar_palavras(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.findall(r"\w+", s)


def taxa_erro(referencia: str, transcrito: str) -> float:
    a, b = _normalizar_palavras(referencia), _normalizar_palavras(transcrito)
    if not a:
        return 0.0
    m = SequenceMatcher(None, a, b, autojunk=False)
    iguais = sum(bloco.size for bloco in m.get_matching_blocks())
    return round(1 - iguais / max(len(a), len(b)), 3)


@lru_cache(maxsize=1)
def _whisper(modelo: str, dispositivo: str):
    import torch
    from transformers import pipeline

    dtype = torch.float16 if dispositivo.startswith("cuda") else torch.float32
    return pipeline("automatic-speech-recognition", model=modelo, device=dispositivo, torch_dtype=dtype)


def transcrever(audio: np.ndarray, sr: int, idioma: str, modelo: str, dispositivo: str) -> str:
    asr = _whisper(modelo, dispositivo)
    saida = asr({"raw": audio.astype(np.float32), "sampling_rate": sr},
                generate_kwargs={"language": idioma, "task": "transcribe"})
    return saida["text"].strip()
