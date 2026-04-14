import time
import threading
from collections import Counter
import numpy as np


class Transcriber:
    def __init__(self, engine: str, model_repo: str, language: str | None = "es"):
        self.engine = engine
        self.model_repo = model_repo
        self.language = language
        self._session = None
        self._lock = threading.Lock()

    def load(self):
        print(f"Cargando modelo {self.model_repo}...")
        t0 = time.time()
        import mlx_whisper  # noqa: F401 — verifica que está instalado
        self._session = self.model_repo
        print(f"Modelo listo en {time.time() - t0:.1f}s")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if self._session is None:
            self.load()

        with self._lock:
            t0 = time.time()
            import mlx_whisper
            result = mlx_whisper.transcribe(
                audio,
                path_or_hf_repo=self._session,
                language=self.language or None,
                initial_prompt=(
                    "Transcripción con puntuación y mayúsculas correctas. "
                    "Siglas técnicas en mayúsculas: JSON, CSV, API, SQL, HTML, PDF. "
                    "Si hay una lista: - Primer elemento. - Segundo elemento. - Tercer elemento."
                ),
            )
            elapsed = time.time() - t0
            raw_text = result["text"].strip()
            print(f"Transcripción en {elapsed:.2f}s: {raw_text!r}")

            segments = result.get("segments", [])
            if segments:
                # Filtra segmento a segmento para conservar el texto bueno
                # aunque haya alucinación al final
                text = self._filter_segments(segments)
                if text != raw_text:
                    print(f"Texto filtrado: {text!r}")
            else:
                # Sin info de segmentos: descarta solo si TODO es alucinación
                text = "" if self._is_hallucination(raw_text) else raw_text

            return text

    @classmethod
    def _filter_segments(cls, segments: list) -> str:
        """Devuelve solo el texto de segmentos válidos, descartando alucinaciones y silencio."""
        good = []
        for seg in segments:
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue
            # Whisper considera este segmento sin voz → saltar
            if seg.get("no_speech_prob", 0) > 0.6:
                continue
            # Texto repetitivo → alucinación → saltar
            if cls._is_hallucination(seg_text):
                continue
            good.append(seg_text)
        return " ".join(good)

    @staticmethod
    def _is_hallucination(text: str) -> bool:
        """Detecta alucinaciones de Whisper por tokens repetidos."""
        words = text.split()
        if len(words) < 8:
            return False
        _, count = Counter(words).most_common(1)[0]
        return count / len(words) > 0.6
