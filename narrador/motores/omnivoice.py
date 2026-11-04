"""Motor OmniVoice (k2-fsa/OmniVoice) — clonagem de voz zero-shot, local."""

from __future__ import annotations

import numpy as np


def escolher_dispositivo(preferido: str = "auto") -> str:
    import torch

    if preferido != "auto":
        return preferido
    if torch.cuda.is_available():
        return "cuda:0"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class MotorOmniVoice:
    def __init__(self, cfg_motor: dict):
        self.cfg = cfg_motor
        self.modelo = None
        self.dispositivo = escolher_dispositivo(cfg_motor.get("dispositivo", "auto"))

    @property
    def sample_rate(self) -> int:
        return int(getattr(self.modelo, "sampling_rate", 24000))

    def carregar(self) -> None:
        import torch
        from omnivoice import OmniVoice

        dtype = torch.float16 if self.dispositivo.startswith("cuda") else torch.float32
        self.modelo = OmniVoice.from_pretrained(
            self.cfg["modelo"], device_map=self.dispositivo, dtype=dtype
        )

    def preparar_voz(self, audio: str, texto: str):
        """Processa a voz de referência uma única vez (timbre estável em todas as partes)."""
        return self.modelo.create_voice_clone_prompt(ref_audio=audio, ref_text=texto)

    def gerar(self, texto: str, voz, idioma: str | None, semente: int) -> np.ndarray:
        import torch

        torch.manual_seed(semente)
        np.random.seed(semente % (2**32))
        velocidade = self.cfg.get("velocidade", 1.0)
        with torch.inference_mode():
            saida = self.modelo.generate(
                text=texto,
                language=idioma,
                voice_clone_prompt=voz,
                speed=None if velocidade in (None, 1.0) else float(velocidade),
                num_step=int(self.cfg.get("num_step", 32)),
                guidance_scale=float(self.cfg.get("guidance_scale", 2.0)),
                # as partes já chegam com ~15 s; desliga a divisão interna
                audio_chunk_threshold=1e9,
            )
        return np.asarray(saida[0], dtype=np.float32).reshape(-1)
