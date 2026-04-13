import gc
import time
import threading
import numpy as np
import mlx.core as mx
from mlx_voxtral import VoxtralProcessor, load_voxtral_model


class Transcriber:
    def __init__(self, model_repo: str, language: str | None = "es"):
        self.model_repo = model_repo
        self.language = language
        self._model = None
        self._processor = None
        # MLX no es thread-safe: serializar todas las llamadas de inferencia
        self._lock = threading.Lock()

    def load(self):
        print(f"Cargando modelo {self.model_repo}...")
        t0 = time.time()
        self._model, _ = load_voxtral_model(self.model_repo, dtype=mx.bfloat16)
        self._processor = VoxtralProcessor.from_pretrained(self.model_repo)
        # Warmup: una pasada vacía para que Metal compile los kernels
        self._warmup()
        print(f"Modelo cargado en {time.time() - t0:.1f}s")

    def _warmup(self):
        try:
            silence = np.zeros(16000, dtype=np.float32)
            inputs = self._processor.apply_transcrition_request(
                audio=silence, language=self.language, sampling_rate=16000
            )
            self._model.generate(
                input_ids=inputs.input_ids,
                input_features=inputs.input_features,
                max_new_tokens=1,
                temperature=0.0,
            )
            mx.eval()
        except Exception:
            pass

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if self._model is None:
            self.load()

        with self._lock:
            t0 = time.time()

            inputs = self._processor.apply_transcrition_request(
                audio=audio,
                language=self.language,
                sampling_rate=sample_rate,
            )

            output_ids = self._model.generate(
                input_ids=inputs.input_ids,
                input_features=inputs.input_features,
                max_new_tokens=1024,
                temperature=0.0,
            )

            # Forzar evaluación lazy de MLX antes de decodificar
            mx.eval(output_ids)

            generated_tokens = output_ids[0, inputs.input_ids.shape[1]:]
            text = self._processor.decode(generated_tokens, skip_special_tokens=True)

            # Limpiar caché de Metal entre llamadas
            mx.metal.clear_cache()
            gc.collect()

            print(f"Transcripción en {time.time() - t0:.2f}s: {text!r}")
            return text.strip()
