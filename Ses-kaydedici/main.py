import sys
import numpy as np
import sounddevice as sd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QGroupBox, QFileDialog, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
import wave

class AudioRecorder(QThread):
    data_ready = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.samplerate = 44100
        self.frames = []
        self.is_recording = False

    def run(self):
        self.is_recording = True
        with sd.InputStream(samplerate=self.samplerate, channels=1, dtype='int16', callback=self.callback):
            while self.is_recording:
                sd.sleep(100)

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        if indata.size > 0:
            self.frames.append(indata.copy())
            self.data_ready.emit(indata)

    def stop(self):
        self.is_recording = False

class AudioLevelMonitor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ses Kaydedici")
        self.setGeometry(100, 100, 600, 400)

        # Stil dosyasını yükleyin
        self.load_stylesheet("style.css")

        main_layout = QVBoxLayout()

        recording_group = QGroupBox("  ")
        recording_layout = QVBoxLayout()

        self.record_button = QPushButton("Kaydı Başlat")
        self.record_button.clicked.connect(self.start_recording)

        self.toggle_button = QPushButton("Durdur")
        self.toggle_button.clicked.connect(self.toggle_recording)
        self.toggle_button.setEnabled(False)

        self.save_button = QPushButton("Kaydı Kaydet")
        self.save_button.clicked.connect(self.save_recording)
        self.save_button.setEnabled(False)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_recording)
        self.reset_button.setEnabled(False)

        # Kayıt süresi etiketi
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 24px;")  # Boyutu büyüt

        recording_layout.addWidget(self.record_button)
        recording_layout.addWidget(self.toggle_button)
        recording_layout.addWidget(self.save_button)
        recording_layout.addWidget(self.reset_button)
        recording_layout.addWidget(self.time_label)
        recording_group.setLayout(recording_layout)

        main_layout.addWidget(recording_group)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.audio_recorder = AudioRecorder()
        self.audio_recorder.data_ready.connect(self.update_slider)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.recording_time = 0

    def load_stylesheet(self, filename):
        with open(filename, "r") as f:
            stylesheet = f.read()
            self.setStyleSheet(stylesheet)

    def start_recording(self):
        self.record_button.setEnabled(False)
        self.toggle_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.reset_button.setEnabled(False)

        self.audio_recorder.start()
        self.recording_time = 0
        self.timer.start(1000)

    def toggle_recording(self):
        if self.audio_recorder.is_recording:
            self.audio_recorder.stop()
            self.timer.stop()
            self.toggle_button.setText("Devam Et")
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)
        else:
            self.audio_recorder.start()
            self.timer.start(1000)
            self.toggle_button.setText("Durdur")

    def update_slider(self, frames):
        if frames.size > 0:
            rms = np.sqrt(np.mean(np.square(frames)))  # RMS hesaplama
            # Ses seviyesini 0-1000 aralığına normalize et
            if rms > 0:
                level = int(np.clip(rms * 1000 / np.iinfo(np.int16).max, 0, 1000))
            else:
                level = 0

    def update_time(self):
        self.recording_time += 1
        hours = self.recording_time // 3600
        minutes = (self.recording_time % 3600) // 60
        seconds = self.recording_time % 60
        self.time_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")

    def save_recording(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Kaydet", "", "WAV Files (*.wav)")
        if file_path:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono ses
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.audio_recorder.samplerate)  # 44.1 kHz
                wf.writeframes(b''.join(self.audio_recorder.frames))

            print(f"Kaydedildi: {file_path}")

    def reset_recording(self):
        self.audio_recorder.frames = []
        self.audio_recorder.stop()  # Kayıt varsa durdur
        self.timer.stop()  # Zamanlayıcıyı durdur
        self.recording_time = 0  # Süreyi sıfırla
        self.time_label.setText("00:00:00")

        # Butonları başlangıç hallerine döndür
        self.record_button.setEnabled(True)
        self.toggle_button.setEnabled(False)
        self.toggle_button.setText("Durdur")
        self.save_button.setEnabled(False)
        self.reset_button.setEnabled(False)

        print("Kayıt sıfırlandı.")

    def closeEvent(self, event):
        self.audio_recorder.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioLevelMonitor()
    window.show()
    sys.exit(app.exec_())
