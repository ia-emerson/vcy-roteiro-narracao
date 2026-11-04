"""Detecção automática do idioma do roteiro (offline)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

NOMES = {
    "pt": "português", "en": "inglês", "es": "espanhol", "fr": "francês",
    "de": "alemão", "it": "italiano", "ja": "japonês", "ko": "coreano",
    "zh": "chinês", "ru": "russo", "ar": "árabe", "hi": "hindi",
    "nl": "holandês", "pl": "polonês", "tr": "turco", "id": "indonésio",
}


@dataclass
class Idioma:
    codigo: str        # ISO 639-1, ex.: "pt"
    nome: str          # nome em português
    confianca: float   # 0..1


@lru_cache(maxsize=1)
def _detector():
    from lingua import LanguageDetectorBuilder

    return LanguageDetectorBuilder.from_all_languages().with_low_accuracy_mode().build()


def detectar(texto: str) -> Idioma:
    amostra = " ".join(texto.split())[:3000]
    if len(amostra) < 20:
        raise ValueError("Texto curto demais para identificar o idioma.")
    det = _detector()
    valores = det.compute_language_confidence_values(amostra)
    if not valores:
        raise ValueError("Não foi possível identificar o idioma.")
    melhor = valores[0]
    codigo = melhor.language.iso_code_639_1.name.lower()
    nome = NOMES.get(codigo, melhor.language.name.lower())
    return Idioma(codigo=codigo, nome=nome, confianca=round(melhor.value, 3))
