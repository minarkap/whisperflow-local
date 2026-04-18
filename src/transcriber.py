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
                condition_on_previous_text=False,
                temperature=0.0,
                initial_prompt=(
                    "Transcripción con puntuación y mayúsculas correctas. "
                    "Siglas técnicas en mayúsculas: JSON, CSV, API, SQL, HTML, PDF. "
                    "Si hay una lista: - Primer elemento. - Segundo elemento. - Tercer elemento."
                ),
            )
            elapsed = time.time() - t0

            segments = result.get("segments", [])
            if segments:
                text = self._filter_segments(segments)
            else:
                text = result["text"].strip()

            print(f"Transcripción en {elapsed:.2f}s: {text!r}")

            if self._is_hallucination(text):
                print("Alucinación detectada en texto final, descartando.")
                return ""

            return text

    @classmethod
    def _filter_segments(cls, segments: list) -> str:
        """Devuelve texto de segmentos válidos, parando al primer signo de looping."""
        good = []
        for seg in segments:
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue
            # Sin voz detectada → Whisper está rellenando, parar aquí
            if seg.get("no_speech_prob", 0) > 0.6:
                break
            # Texto repetitivo → Whisper en loop, parar aquí
            if cls._is_hallucination(seg_text):
                break
            good.append(seg_text)

        text = " ".join(good)

        # Detectar loop en el texto ensamblado (ej: frase real + looping al final)
        return cls._truncate_loop(text)

    @staticmethod
    def _truncate_loop(text: str) -> str:
        """Trunca el texto en el punto donde empieza un loop de n-gramas."""
        words = text.split()
        if len(words) < 20:
            return text

        # Busca la primera ventana de 10 palabras con ratio de repetición alto
        for n in (2, 3):
            seen: dict[tuple, int] = {}
            ngrams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
            for idx, ng in enumerate(ngrams):
                seen[ng] = seen.get(ng, 0) + 1
                # Si este n-grama ya apareció ≥3 veces, truncar antes de la primera repetición
                if seen[ng] >= 3:
                    first_pos = next(
                        i for i, g in enumerate(ngrams) if g == ng
                    )
                    return " ".join(words[:first_pos + n])
        return text

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
