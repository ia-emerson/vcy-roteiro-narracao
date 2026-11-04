"""Catálogo das vozes de referência da pasta voices/.

Convenção de nomes: <idioma>_<nome>.<ext> + <idioma>_<nome>.txt
  ex.: pt_joana.wav + pt_joana.txt, en-US_mike.wav + en-US_mike.txt
O .txt deve conter exatamente o que é falado no áudio.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import soundfile as sf

from narrador import config

EXTENSOES = (".wav", ".flac", ".mp3", ".ogg", ".m4a")
_PADRAO = re.compile(r"^(?P<idioma>[a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?)_(?P<nome>.+)$")


@dataclass
class Voz:
    id: str              # nome do arquivo sem extensão, ex.: pt_joana
    idioma: str          # código base, ex.: pt
    variante: str        # ex.: pt-BR (ou igual ao idioma)
    nome: str            # ex.: joana
    audio: str
    texto_arquivo: str | None
    texto: str
    duracao: float
    problemas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def utilizavel(self) -> bool:
        return not self.problemas

    def para_dict(self) -> dict:
        d = asdict(self)
        d["utilizavel"] = self.utilizavel
        return d


def _duracao(caminho: Path) -> float:
    try:
        info = sf.info(str(caminho))
        return round(info.frames / info.samplerate, 2)
    except Exception:
        return -1.0


def listar(pasta: Path | None = None, idioma: str | None = None) -> list[Voz]:
    pasta = pasta or config.VOZES
    if not pasta.exists():
        return []
    vozes: list[Voz] = []
    for arq in sorted(pasta.iterdir()):
        if arq.suffix.lower() not in EXTENSOES or not arq.is_file():
            continue
        m = _PADRAO.match(arq.stem)
        problemas: list[str] = []
        avisos: list[str] = []
        if m:
            variante = m["idioma"]
            base = variante.split("-")[0].lower()
            nome = m["nome"]
        else:
            variante = base = "?"
            nome = arq.stem
            problemas.append(
                "nome fora do padrão <idioma>_<nome> (ex.: pt_joana.wav)"
            )
        txt = arq.with_suffix(".txt")
        texto = ""
        if txt.exists():
            texto = txt.read_text(encoding="utf-8-sig").strip()
            if not texto:
                problemas.append(f"{txt.name} está vazio")
        else:
            problemas.append(f"falta o arquivo de texto {txt.name}")
        dur = _duracao(arq)
        if dur < 0:
            problemas.append("não foi possível ler o áudio (prefira .wav)")
        elif dur < 3:
            problemas.append(f"áudio curto demais ({dur}s; use 5 a 12 s)")
        elif dur > 15:
            avisos.append(f"áudio longo ({dur}s); o ideal é ~10 s, acima disso a clonagem pode piorar")
        vozes.append(
            Voz(
                id=arq.stem, idioma=base, variante=variante, nome=nome,
                audio=str(arq), texto_arquivo=str(txt) if txt.exists() else None,
                texto=texto, duracao=dur, problemas=problemas, avisos=avisos,
            )
        )
    if idioma:
        idioma = idioma.split("-")[0].lower()
        vozes = [v for v in vozes if v.idioma == idioma]
    return vozes


def obter(id_voz: str, pasta: Path | None = None) -> Voz:
    for v in listar(pasta):
        if v.id == id_voz:
            if not v.utilizavel:
                raise ValueError(f"Voz '{id_voz}' com problemas: {'; '.join(v.problemas)}")
            return v
    raise ValueError(f"Voz '{id_voz}' não encontrada em {pasta or config.VOZES}")
