"""Montagem do áudio final: une as partes, insere pausas e ajusta o volume."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


def unir(partes: list[np.ndarray], fins_paragrafo: list[bool], sr: int,
         pausa_frase: float, pausa_paragrafo: float) -> np.ndarray:
    blocos: list[np.ndarray] = []
    for i, (audio, fim) in enumerate(zip(partes, fins_paragrafo)):
        blocos.append(audio.astype(np.float32))
        if i < len(partes) - 1:
            pausa = pausa_paragrafo if fim else pausa_frase
            blocos.append(np.zeros(int(sr * pausa), dtype=np.float32))
    return np.concatenate(blocos) if blocos else np.zeros(0, dtype=np.float32)


def limitar(audio: np.ndarray, sr: int, teto_db: float, lookahead_ms: float = 5.0) -> tuple[np.ndarray, float]:
    """Limitador de picos com lookahead: reduz só os transientes acima do teto, sem distorcer.

    O ganho é o mínimo numa janela de 2L suavizado por média móvel de L, o que garante que
    nenhuma amostra passe do teto e que a curva de ganho não tenha degraus audíveis.
    """
    from scipy.ndimage import minimum_filter1d, uniform_filter1d

    teto = 10 ** (teto_db / 20)
    picos = np.abs(audio)
    if picos.max() <= teto:
        return audio, 0.0
    bruto = np.minimum(1.0, teto / np.maximum(picos, 1e-12))
    L = max(3, int(sr * lookahead_ms / 1000))
    ganho = minimum_filter1d(bruto, size=2 * L + 1)
    ganho = uniform_filter1d(ganho, size=L)
    ganho = np.minimum(ganho, bruto)       # segurança numérica nas bordas
    saida = audio * ganho
    return saida.astype(np.float32), float(20 * np.log10(ganho.min()))


def normalizar(audio: np.ndarray, sr: int, lufs: float, pico_max_db: float,
               max_limitacao_db: float = 6.0) -> tuple[np.ndarray, dict]:
    """Ganho único até o volume alvo; um limitador suave segura só os picos isolados.

    Se fosse preciso limitar mais que max_limitacao_db, o volume alvo é reduzido em vez de
    espremer a voz.
    """
    import pyloudnorm as pyln

    medidor = pyln.Meter(sr)
    antes = float(medidor.integrated_loudness(audio))
    ganho_db = lufs - antes
    pico_db = 20 * np.log10(float(np.max(np.abs(audio))) or 1e-9)
    excesso = pico_db + ganho_db - pico_max_db
    if excesso > max_limitacao_db:
        ganho_db -= excesso - max_limitacao_db
    saida = audio * (10 ** (ganho_db / 20))
    saida, reducao = limitar(saida, sr, pico_max_db - 0.5)   # 0,5 dB de margem (true peak / MP3)
    depois = float(medidor.integrated_loudness(saida))
    return saida.astype(np.float32), {
        "lufs_original": round(antes, 1),
        "lufs_final": round(depois, 1),
        "pico_final_db": round(20 * np.log10(float(np.max(np.abs(saida))) or 1e-9), 1),
        "ganho_db": round(ganho_db, 1),
        "limitador_max_db": round(reducao, 1),
    }


def salvar_wav(audio: np.ndarray, sr: int, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(caminho), audio, sr, subtype="PCM_24")


def salvar_mp3(audio: np.ndarray, sr: int, caminho: Path, kbps: int = 192) -> None:
    import lameenc

    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2").tobytes()
    enc = lameenc.Encoder()
    enc.set_bit_rate(kbps)
    enc.set_in_sample_rate(sr)
    enc.set_channels(1)
    enc.set_quality(2)          # 2 = alta qualidade
    dados = enc.encode(pcm) + enc.flush()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(dados)
