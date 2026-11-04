"""Pipeline completo: roteiro -> partes -> OmniVoice -> conferência -> áudio final."""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from narrador import config as cfgmod
from narrador import montar, qualidade, texto, vozes
from narrador.idioma import detectar


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


@dataclass
class Resultado:
    wav: str
    mp3: str
    duracao_s: float
    partes: int
    regeneradas: list[int]
    suspeitas: list[dict]
    volume: dict
    idioma: str
    voz: str
    tempo_s: float


def _assinatura(parte: str, voz: vozes.Voz, cfg: cfgmod.Config, idioma: str) -> str:
    chave = json.dumps([parte, voz.id, voz.texto, Path(voz.audio).stat().st_mtime, idioma,
                        cfg.motor], sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(chave.encode("utf-8")).hexdigest()[:16]


def narrar(roteiro: Path, id_voz: str, nome_saida: str | None = None,
           refazer: set[int] | None = None, verificar: bool | None = None,
           cfg: cfgmod.Config | None = None) -> Resultado:
    inicio = time.time()
    cfg = cfg or cfgmod.carregar()
    refazer = refazer or set()
    if verificar is None:
        verificar = bool(cfg.qualidade["verificar_transcricao"])

    bruto = roteiro.read_text(encoding="utf-8-sig")
    lang = detectar(bruto).codigo
    voz = vozes.obter(id_voz)
    if voz.idioma != lang:
        log(f"AVISO: roteiro em '{lang}', voz em '{voz.idioma}'. O sotaque da voz vai aparecer.")

    partes = texto.preparar(bruto, lang, int(cfg.divisao["max_caracteres"]))
    if not partes:
        raise ValueError("O roteiro não tem texto narrável.")
    nome = nome_saida or roteiro.stem
    pasta = cfgmod.TRABALHO / nome
    pasta.mkdir(parents=True, exist_ok=True)
    manifesto_arq = pasta / "manifesto.json"
    manifesto = json.loads(manifesto_arq.read_text(encoding="utf-8")) if manifesto_arq.exists() else {}

    from narrador.motores import MotorOmniVoice

    motor = MotorOmniVoice(cfg.motor)
    log(f"Carregando OmniVoice em {motor.dispositivo}...")
    motor.carregar()
    sr = motor.sample_rate
    prompt = motor.preparar_voz(voz.audio, voz.texto)
    log(f"Voz '{voz.id}' pronta. {len(partes)} partes em '{lang}'.")

    audios: list[np.ndarray] = []
    cps_medidos: list[float] = []
    regeneradas: list[int] = []
    suspeitas: list[dict] = []
    semente_base = int(cfg.motor.get("semente", 1234))
    tentativas = max(1, int(cfg.qualidade["tentativas"]))

    for p in partes:
        arq = pasta / f"parte_{p.indice:04d}.wav"
        assinatura = _assinatura(p.texto, voz, cfg, lang)
        reg = manifesto.get(str(p.indice), {})
        if arq.exists() and reg.get("assinatura") == assinatura and p.indice not in refazer:
            audio, _ = sf.read(str(arq), dtype="float32")
            audios.append(audio)
            cps_medidos.append(len(p.texto) / max(len(audio) / sr, 0.1))
            continue

        cps_ref = statistics.median(cps_medidos) if len(cps_medidos) >= 3 else None
        melhor, melhor_probs = None, None
        deslocamento = 1000 if p.indice in refazer else 0
        for t in range(tentativas):
            semente = semente_base + p.indice * 7919 + t * 104729 + deslocamento
            audio = motor.gerar(p.texto, prompt, lang, semente)
            probs = qualidade.inspecionar(audio, sr, p.texto, cps_ref)
            if not probs and verificar:
                transcrito = qualidade.transcrever(audio, sr, lang, cfg.qualidade["modelo_whisper"],
                                                   motor.dispositivo)
                # Whisper escreve "1977"; o texto tem "mil novecentos..." -> normaliza os dois
                erro = qualidade.taxa_erro(p.texto, texto.numeros_por_extenso(transcrito, lang))
                if erro > float(cfg.qualidade["max_erro_palavras"]):
                    probs = [f"Whisper divergiu do texto ({erro:.0%}): '{transcrito}'"]
            if melhor is None or len(probs) < len(melhor_probs):
                melhor, melhor_probs = audio, probs
            if not probs:
                break
            log(f"  parte {p.indice}: {'; '.join(probs)} -> tentando de novo")
        if t > 0:
            regeneradas.append(p.indice)
        if melhor_probs:
            suspeitas.append({"parte": p.indice, "texto": p.texto, "problemas": melhor_probs})
        sf.write(str(arq), melhor, sr, subtype="FLOAT")
        manifesto[str(p.indice)] = {"assinatura": assinatura, "texto": p.texto,
                                    "fim_paragrafo": p.fim_paragrafo}
        manifesto_arq.write_text(json.dumps(manifesto, ensure_ascii=False, indent=1), encoding="utf-8")
        audios.append(melhor)
        cps_medidos.append(len(p.texto) / max(len(melhor) / sr, 0.1))
        decorrido = time.time() - inicio
        log(f"[{p.indice}/{len(partes)}] ok ({len(melhor) / sr:.1f}s) — {decorrido:.0f}s decorridos")

    m = cfg.montagem
    final = montar.unir(audios, [p.fim_paragrafo for p in partes], sr,
                        float(m["pausa_frase"]), float(m["pausa_paragrafo"]))
    final, volume = montar.normalizar(final, sr, float(m["lufs"]), float(m["pico_max_db"]))
    wav = cfgmod.NARRACOES / f"{nome}.wav"
    mp3 = cfgmod.NARRACOES / f"{nome}.mp3"
    montar.salvar_wav(final, sr, wav)
    montar.salvar_mp3(final, sr, mp3, int(m["mp3_kbps"]))
    (pasta / "relatorio.json").write_text(json.dumps(
        {"suspeitas": suspeitas, "regeneradas": regeneradas, "volume": volume},
        ensure_ascii=False, indent=1), encoding="utf-8")

    return Resultado(
        wav=str(wav), mp3=str(mp3), duracao_s=round(len(final) / sr, 1), partes=len(partes),
        regeneradas=regeneradas, suspeitas=suspeitas, volume=volume, idioma=lang, voz=voz.id,
        tempo_s=round(time.time() - inicio, 1),
    )
