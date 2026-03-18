import pyaudio
import base64
import logging

class B64PCMPlayer:
    def __init__(self, pya: pyaudio.PyAudio, sample_rate: int = 24000):
        self.pya = pya
        self.sample_rate = sample_rate
        self.stream = None
        self.is_playing = False
        self.audio_queue = []
    
    def start(self):
        if not self.stream:
            self.stream = self.pya.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True
            )
        self.is_playing = True
    
    def add_data(self, audio_b64: str):
        try:
            audio_data = base64.b64decode(audio_b64)
            if self.stream and self.is_playing:
                self.stream.write(audio_data)
        except Exception as e:
            logging.error(f"Play audio error: {e}")
    
    def stop(self):
        self.is_playing = False
        if self.stream:
            self.stream.stop_stream()
    
    def cancel(self):
        self.audio_queue = []
        self.stop()
    
    def shutdown(self):
        self.stop()
        if self.stream:
            self.stream.close()
            self.stream = None