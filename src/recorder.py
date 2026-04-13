import queue
import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, device=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self._queue: queue.Queue = queue.Queue()
        self._stream: sd.InputStream | None = None

    def start(self):
        self._queue = queue.Queue()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        chunks = []
        while not self._queue.empty():
            chunks.append(self._queue.get_nowait())

        if not chunks:
            return np.zeros(0, dtype="float32")

        audio = np.concatenate(chunks, axis=0)
        return audio.flatten()

    def _callback(self, indata, frames, time, status):
        self._queue.put(indata.copy())
