"""Caminhos do projeto e leitura do config.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ROTEIROS = RAIZ / "roteiros"
NARRACOES = RAIZ / "narrações"
VOZES = RAIZ / "voices"
TRABALHO = NARRACOES / ".trabalho"


@dataclass
class Config:
    motor: dict = field(default_factory=dict)
    divisao: dict = field(default_factory=dict)
    montagem: dict = field(default_factory=dict)
    qualidade: dict = field(default_factory=dict)


PADRAO = {
    "motor": {
        "modelo": "k2-fsa/OmniVoice",
        "dispositivo": "auto",
        "num_step": 32,
        "guidance_scale": 2.0,
        "velocidade": 1.0,
        "semente": 1234,
    },
    "divisao": {"max_caracteres": 220},
    "montagem": {
        "pausa_frase": 0.15,
        "pausa_paragrafo": 0.50,
        "lufs": -14.0,
        "pico_max_db": -1.0,
        "mp3_kbps": 192,
    },
    "qualidade": {
        "tentativas": 3,
        "verificar_transcricao": False,
        "modelo_whisper": "openai/whisper-large-v3-turbo",
        "max_erro_palavras": 0.20,
    },
}


def carregar(caminho: Path | None = None) -> Config:
    caminho = caminho or RAIZ / "config.toml"
    dados: dict = {}
    if caminho.exists():
        dados = tomllib.loads(caminho.read_text(encoding="utf-8"))
    secoes = {}
    for nome, padrao in PADRAO.items():
        secoes[nome] = {**padrao, **dados.get(nome, {})}
    return Config(**secoes)
