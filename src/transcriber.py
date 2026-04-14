import time
import threading
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
            text = result["text"].strip()
            elapsed = time.time() - t0
            print(f"Transcripción en {elapsed:.2f}s: {text!r}")

            # 1) Silencio detectado por Whisper (no_speech_prob por segmento)
            segments = result.get("segments", [])
            if segments:
                avg_no_speech = sum(s.get("no_speech_prob", 0) for s in segments) / len(segments)
                if avg_no_speech > 0.6:
                    print(f"Sin voz detectado (no_speech_prob={avg_no_speech:.2f}), descartando.")
                    return ""

            # 2) Alucinación por tokens repetidos (red de seguridad)
            if self._is_hallucination(text):
                print("Alucinación detectada (texto repetido), descartando.")
                return ""

            return text

    @staticmethod
    def _is_hallucination(text: str) -> bool:
        """Detecta alucinaciones de Whisper por tokens repetidos."""
        words = text.split()
        if len(words) < 8:
            return False
        from collections import Counter
        _, count = Counter(words).most_common(1)[0]
        return count / len(words) > 0.6
