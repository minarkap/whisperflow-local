import time
import threading
from collections import Counter
import numpy as np

_SILENCE_THRESHOLD = 0.005
_SILENCE_PAD_S     = 0.15
_MIN_AUDIO_S       = 0.3


def _trim_silence(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    above = np.abs(audio) > _SILENCE_THRESHOLD
    if above.any():
        pad   = int(_SILENCE_PAD_S * sample_rate)
        start = max(0, np.argmax(above) - pad)
        end   = min(len(audio), len(audio) - np.argmax(above[::-1]) + pad)
        audio = audio[start:end]
    min_samples = int(_MIN_AUDIO_S * sample_rate)
    if len(audio) < min_samples:
        audio = np.concatenate([audio, np.zeros(min_samples - len(audio), dtype="float32")])
    return audio


class Transcriber:
    def __init__(self, engine: str, model_repo: str, language: str | None = "es"):
        self.engine      = engine
        self.model_repo  = model_repo
        self.language    = language
        self._session    = None
        self._warmup_done = threading.Event()

    def load(self):
        print(f"Cargando modelo {self.model_repo}...")
        t0 = time.time()
        import mlx_whisper
        self._mlx_whisper = mlx_whisper
        self._session     = self.model_repo
        print(f"Modelo listo en {time.time() - t0:.1f}s")

        def _warmup():
            t1 = time.time()
            try:
                self._mlx_whisper.transcribe(
                    np.zeros(16000, dtype="float32"),
                    path_or_hf_repo=self._session,
                    language=self.language or None,
                    condition_on_previous_text=False,
                    temperature=0.0,
                    word_timestamps=False,
                )
                print(f"Warm-up listo en {time.time() - t1:.1f}s")
            except Exception as e:
                print(f"Warm-up falló: {e}")
            finally:
                self._warmup_done.set()

        threading.Thread(target=_warmup, daemon=True).start()

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if self._session is None:
            self.load()

        if not self._warmup_done.is_set():
            print("⏳ Esperando warmup del modelo...")
            self._warmup_done.wait(timeout=8)

        audio = _trim_silence(audio, sample_rate)
        t0    = time.time()
        result = self._mlx_whisper.transcribe(
            audio,
            path_or_hf_repo=self._session,
            language=self.language or None,
            condition_on_previous_text=False,
            temperature=0.0,
            word_timestamps=False,
        )

        segments = result.get("segments", [])
        text     = self._filter_segments(segments) if segments else result["text"].strip()

        print(f"Transcripción en {time.time() - t0:.2f}s: {text!r}")

        if self._is_hallucination(text):
            print("Alucinación detectada, descartando.")
            return ""

        return text

    @classmethod
    def _filter_segments(cls, segments: list) -> str:
        good = []
        for seg in segments:
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue
            if seg.get("no_speech_prob", 0) > 0.85:
                break
            if cls._is_hallucination(seg_text):
                break
            good.append(seg_text)
        return cls._truncate_loop(" ".join(good))

    @staticmethod
    def _truncate_loop(text: str) -> str:
        words = text.split()
        if len(words) < 30:
            return text
        for n in (2, 3):
            first_seen: dict[tuple, int] = {}
            count:      dict[tuple, int] = {}
            for i in range(len(words) - n + 1):
                ng = tuple(words[i:i + n])
                if ng not in first_seen:
                    first_seen[ng] = i
                count[ng] = count.get(ng, 0) + 1
                if count[ng] >= 4:
                    return " ".join(words[:first_seen[ng] + n])
        return text

    @staticmethod
    def _is_hallucination(text: str) -> bool:
        words = text.split()
        if len(words) < 8:
            return False
        _, top = Counter(words).most_common(1)[0]
        if top / len(words) > 0.7:
            return True
        for n in (2, 3):
            if len(words) < n * 5:
                continue
            ngrams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
            _, ng_top = Counter(ngrams).most_common(1)[0]
            if ng_top / len(ngrams) > 0.5:
                return True
        return False
