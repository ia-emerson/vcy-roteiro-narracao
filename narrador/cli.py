"""Comandos usados pelas skills. Saída de dados em JSON (stdout); progresso em stderr.

  python -m narrador diagnostico
  python -m narrador baixar-modelo
  python -m narrador estimar  roteiros/x.txt
  python -m narrador idioma   roteiros/x.txt
  python -m narrador vozes    [--idioma pt]
  python -m narrador partes   roteiros/x.txt          (mostra como o texto será dividido)
  python -m narrador narrar   roteiros/x.txt --voz pt_joana [--saida nome] [--refazer 3,7] [--verificar]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("TORCH_DISTRIBUTED_DEBUG", "OFF")

PALAVRAS_MIN = {"pt": 150, "en": 155, "es": 160}


def _json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def _ler(caminho: str) -> str:
    return Path(caminho).read_text(encoding="utf-8-sig")


def cmd_diagnostico(_a) -> int:
    info: dict = {"python": sys.version.split()[0]}
    ok = True
    try:
        import torch

        info["torch"] = torch.__version__
        info["cuda"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            info["gpu"] = f"{p.name} ({p.total_memory / 2**30:.1f} GB)"
        info["mps"] = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except Exception as e:  # noqa: BLE001
        info["torch"] = f"ERRO: {e}"
        ok = False
    try:
        from importlib.metadata import version

        info["omnivoice"] = version("omnivoice")
        import omnivoice  # noqa: F401
    except Exception as e:  # noqa: BLE001
        info["omnivoice"] = f"ERRO: {e}"
        ok = False
    try:
        from huggingface_hub import try_to_load_from_cache

        from narrador import config

        modelo = config.carregar().motor["modelo"]
        info["modelo_baixado"] = isinstance(try_to_load_from_cache(modelo, "config.json"), str)
    except Exception:  # noqa: BLE001
        info["modelo_baixado"] = False
    from narrador import vozes

    vs = vozes.listar()
    info["vozes"] = {v.id: ("ok" if v.utilizavel else "; ".join(v.problemas)) for v in vs}
    info["ok"] = ok
    _json(info)
    return 0 if ok else 1


def cmd_baixar_modelo(_a) -> int:
    from huggingface_hub import snapshot_download

    from narrador import config

    modelo = config.carregar().motor["modelo"]
    print(f"Baixando {modelo}...", file=sys.stderr)
    caminho = snapshot_download(modelo)
    _json({"modelo": modelo, "pasta": caminho})
    return 0


def cmd_estimar(a) -> int:
    from narrador import texto
    from narrador.idioma import detectar

    bruto = _ler(a.roteiro)
    lang = detectar(bruto).codigo
    palavras = sum(len(p.split()) for p in texto.limpar(bruto))
    ppm = PALAVRAS_MIN.get(lang, 150)
    _json({"idioma": lang, "palavras": palavras, "palavras_por_minuto": ppm,
           "minutos_estimados": round(palavras / ppm, 1)})
    return 0


def cmd_idioma(a) -> int:
    from narrador.idioma import detectar

    _json(asdict(detectar(_ler(a.roteiro))))
    return 0


def cmd_vozes(a) -> int:
    from narrador import vozes

    _json([v.para_dict() for v in vozes.listar(idioma=a.idioma)])
    return 0


def cmd_partes(a) -> int:
    from narrador import config, texto
    from narrador.idioma import detectar

    bruto = _ler(a.roteiro)
    lang = detectar(bruto).codigo
    partes = texto.preparar(bruto, lang, int(config.carregar().divisao["max_caracteres"]))
    _json([asdict(p) for p in partes])
    return 0


def cmd_narrar(a) -> int:
    from narrador.narrar import narrar

    refazer = {int(x) for x in a.refazer.split(",") if x.strip()} if a.refazer else set()
    r = narrar(Path(a.roteiro), a.voz, a.saida, refazer, True if a.verificar else None)
    _json(asdict(r))
    return 0


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(prog="narrador", description="Narração local com OmniVoice")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("diagnostico").set_defaults(f=cmd_diagnostico)
    sub.add_parser("baixar-modelo").set_defaults(f=cmd_baixar_modelo)
    for nome, f in (("estimar", cmd_estimar), ("idioma", cmd_idioma), ("partes", cmd_partes)):
        p = sub.add_parser(nome)
        p.add_argument("roteiro")
        p.set_defaults(f=f)
    p = sub.add_parser("vozes")
    p.add_argument("--idioma")
    p.set_defaults(f=cmd_vozes)
    p = sub.add_parser("narrar")
    p.add_argument("roteiro")
    p.add_argument("--voz", required=True, help="id da voz, ex.: pt_joana")
    p.add_argument("--saida", help="nome do arquivo final (padrão: nome do roteiro)")
    p.add_argument("--refazer", help="partes a regenerar, ex.: 3,7,12")
    p.add_argument("--verificar", action="store_true", help="conferir cada parte com Whisper")
    p.set_defaults(f=cmd_narrar)
    a = ap.parse_args(argv)
    try:
        return a.f(a)
    except (ValueError, FileNotFoundError) as e:
        _json({"erro": str(e)})
        return 2
