import time
import numpy as np
import mlx.core as mx
from mlx_voxtral import VoxtralProcessor, load_voxtral_model


class Transcriber:
    def __init__(self, model_repo: str, language: str | None = "es"):
        self.model_repo = model_repo
        self.language = language
        self._model = None
        self._processor = None

    def load(self):
        print(f"Cargando modelo {self.model_repo}...")
        t0 = time.time()
        self._model, _ = load_voxtral_model(self.model_repo, dtype=mx.bfloat16)
        self._processor = VoxtralProcessor.from_pretrained(self.model_repo)
        print(f"Modelo cargado en {time.time() - t0:.1f}s")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if self._model is None:
            self.load()

        t0 = time.time()

        inputs = self._processor.apply_transcrition_request(
            audio=audio,
            language=self.language,
            sampling_rate=sample_rate,
        )

        mlx_inputs = {
            "input_ids": inputs.input_ids,
            "input_features": inputs.input_features,
        }

        output_ids = self._model.generate(
            **mlx_inputs,
            max_new_tokens=1024,
            temperature=0.0,
        )

        generated_tokens = output_ids[0, inputs.input_ids.shape[1]:]
        text = self._processor.decode(generated_tokens, skip_special_tokens=True)

        print(f"Transcripción en {time.time() - t0:.2f}s: {text!r}")
        return text.strip()
