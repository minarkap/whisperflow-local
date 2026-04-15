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
                text = self._filter_segments(segments)
                if text != raw_text:
                    print(f"Texto filtrado por segmentos: {text!r}")
            else:
                text = raw_text

            # Verificación final sobre el texto ensamblado completo.
            # Necesaria porque los segmentos individuales son muy cortos
            # para que _is_hallucination los detecte (< 8 palabras).
            if self._is_hallucination(text):
                print("Alucinación detectada en texto final, descartando.")
                return ""

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
        """Detecta alucinaciones de Whisper por tokens o frases repetidas."""
        words = text.split()
        if len(words) < 8:
            return False

        # Palabra única repetida (Plus Plus Plus...)
        _, count = Counter(words).most_common(1)[0]
        if count / len(words) > 0.6:
            return True

        # Frase corta repetida (Momentum e Momentum e...)
        for n in (2, 3):
            if len(words) < n * 4:
                continue
            ngrams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
            _, ng_count = Counter(ngrams).most_common(1)[0]
            if ng_count / len(ngrams) > 0.4:
                return True

        return False
