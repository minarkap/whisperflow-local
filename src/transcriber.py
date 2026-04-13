import time
import threading
import numpy as np
import mlx.core as mx


class Transcriber:
    def __init__(self, engine: str, model_repo: str, language: str | None = "es"):
        self.engine = engine
        self.model_repo = model_repo
        self.language = language
        self._session = None
        self._lock = threading.Lock()

    def load(self):
        print(f"Cargando modelo {self.model_repo} (engine: {self.engine})...")
        t0 = time.time()

        if self.engine == "qwen3-asr":
            self._load_qwen3()
        elif self.engine == "voxtral-mini-3b":
            self._load_voxtral()
        elif self.engine == "whisper":
            self._load_whisper()
        else:
            raise ValueError(f"Engine desconocido: {self.engine}")

        print(f"Modelo cargado en {time.time() - t0:.1f}s")

    def _load_qwen3(self):
        from mlx_qwen3_asr import Session
        self._session = Session(self.model_repo, dtype=mx.float16)

    def _load_voxtral(self):
        from mlx_voxtral import VoxtralProcessor, load_voxtral_model
        model, _ = load_voxtral_model(self.model_repo, dtype=mx.bfloat16)
        processor = VoxtralProcessor.from_pretrained(self.model_repo)
        # Warmup: compilar kernels de Metal con silencio
        try:
            silence = np.zeros(16000, dtype=np.float32)
            inputs = processor.apply_transcrition_request(
                audio=silence, language=self.language, sampling_rate=16000
            )
            model.generate(
                input_ids=inputs.input_ids,
                input_features=inputs.input_features,
                max_new_tokens=1, temperature=0.0,
            )
            mx.eval()
        except Exception:
            pass
        self._session = (model, processor)

    def _load_whisper(self):
        import mlx_whisper
        # mlx_whisper no tiene objeto Session; guardamos el repo
        self._session = self.model_repo

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        if self._session is None:
            self.load()

        with self._lock:
            t0 = time.time()

            if self.engine == "qwen3-asr":
                text = self._transcribe_qwen3(audio, sample_rate)
            elif self.engine == "voxtral-mini-3b":
                text = self._transcribe_voxtral(audio, sample_rate)
            elif self.engine == "whisper":
                text = self._transcribe_whisper(audio, sample_rate)
            else:
                raise ValueError(f"Engine desconocido: {self.engine}")

            print(f"Transcripción en {time.time() - t0:.2f}s: {text!r}")
            return text.strip()

    def _transcribe_qwen3(self, audio: np.ndarray, sample_rate: int) -> str:
        result = self._session.transcribe(
            (audio, sample_rate),
            language=self.language,
            max_new_tokens=1024,
        )
        return result.text

    def _transcribe_voxtral(self, audio: np.ndarray, sample_rate: int) -> str:
        model, processor = self._session
        inputs = processor.apply_transcrition_request(
            audio=audio, language=self.language, sampling_rate=sample_rate
        )
        output_ids = model.generate(
            input_ids=inputs.input_ids,
            input_features=inputs.input_features,
            max_new_tokens=1024,
            temperature=0.0,
        )
        mx.eval(output_ids)
        tokens = output_ids[0, inputs.input_ids.shape[1]:]
        return processor.decode(tokens, skip_special_tokens=True)

    def _transcribe_whisper(self, audio: np.ndarray, sample_rate: int) -> str:
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
        return result["text"]
