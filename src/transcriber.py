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
            print(f"Transcripción en {time.time() - t0:.2f}s: {text!r}")
            return text
