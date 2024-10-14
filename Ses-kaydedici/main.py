import sys
import numpy as np
import sounddevice as sd
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QGroupBox, QFileDialog, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
import wave

class SesKaydedici(QThread):
    veri_hazir = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.samplerate = 44100
        self.kareler = []
        self.kayit_var = False

    def run(self):
        self.kayit_var = True
        with sd.InputStream(samplerate=self.samplerate, channels=1, dtype='int16', callback=self.callback):
            while self.kayit_var:
                sd.sleep(100)

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        if indata.size > 0:
            self.kareler.append(indata.copy())
            self.veri_hazir.emit(indata)

    def durdur(self):
        self.kayit_var = False

class SesSeviyeGozlemcisi(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ses Kaydedici")
        self.setGeometry(100, 100, 600, 400)

        self.load_stylesheet("style.css")

        ana_duzen = QVBoxLayout()

        kayit_grubu = QGroupBox("  ")
        kayit_duzeni = QVBoxLayout()

        self.kayit_butonu = QPushButton("Kaydı Başlat")
        self.kayit_butonu.clicked.connect(self.kayit_baslat)

        self.toggle_butonu = QPushButton("Durdur")
        self.toggle_butonu.clicked.connect(self.kayit_toggle)
        self.toggle_butonu.setEnabled(False)

        self.kaydet_butonu = QPushButton("Kaydı Kaydet")
        self.kaydet_butonu.clicked.connect(self.kaydi_kaydet)
        self.kaydet_butonu.setEnabled(False)

        self.sifirla_butonu = QPushButton("Sıfırla")
        self.sifirla_butonu.clicked.connect(self.kaydi_sifirla)
        self.sifirla_butonu.setEnabled(False)

        self.zaman_label = QLabel("00:00:00")
        self.zaman_label.setAlignment(Qt.AlignCenter)
        self.zaman_label.setStyleSheet("font-size: 24px;")

        kayit_duzeni.addWidget(self.kayit_butonu)
        kayit_duzeni.addWidget(self.toggle_butonu)
        kayit_duzeni.addWidget(self.kaydet_butonu)
        kayit_duzeni.addWidget(self.sifirla_butonu)
        kayit_duzeni.addWidget(self.zaman_label)
        kayit_grubu.setLayout(kayit_duzeni)

        ana_duzen.addWidget(kayit_grubu)

        konteyner = QWidget()
        konteyner.setLayout(ana_duzen)
        self.setCentralWidget(konteyner)

        self.ses_kaydedici = SesKaydedici()
        self.ses_kaydedici.veri_hazir.connect(self.slideri_guncelle)

        self.zamanlayici = QTimer(self)
        self.zamanlayici.timeout.connect(self.zaman_guncelle)
        self.kayit_suresi = 0

    def load_stylesheet(self, filename):
        with open(filename, "r") as f:
            stylesheet = f.read()
            self.setStyleSheet(stylesheet)

    def kayit_baslat(self):
        self.kayit_butonu.setEnabled(False)
        self.toggle_butonu.setEnabled(True)
        self.kaydet_butonu.setEnabled(False)
        self.sifirla_butonu.setEnabled(False)

        self.ses_kaydedici.start()
        self.kayit_suresi = 0
        self.zamanlayici.start(1000)

    def kayit_toggle(self):
        if self.ses_kaydedici.kayit_var:
            self.ses_kaydedici.durdur()
            self.zamanlayici.stop()
            self.toggle_butonu.setText("Devam Et")
            self.kaydet_butonu.setEnabled(True)
            self.sifirla_butonu.setEnabled(True)
        else:
            self.ses_kaydedici.start()
            self.zamanlayici.start(1000)
            self.toggle_butonu.setText("Durdur")

    def slideri_guncelle(self, kareler):
        if kareler.size > 0:
            rms = np.sqrt(np.mean(np.square(kareler)))
            if rms > 0:
                seviye = int(np.clip(rms * 1000 / np.iinfo(np.int16).max, 0, 1000))
            else:
                seviye = 0

    def zaman_guncelle(self):
        self.kayit_suresi += 1
        saat = self.kayit_suresi // 3600
        dakika = (self.kayit_suresi % 3600) // 60
        saniye = self.kayit_suresi % 60
        self.zaman_label.setText(f"{saat:02}:{dakika:02}:{saniye:02}")

    def kaydi_kaydet(self):
        dosya_yolu, _ = QFileDialog.getSaveFileName(self, "Kaydet", "", "WAV Files (*.wav)")
        if dosya_yolu:
            with wave.open(dosya_yolu, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.ses_kaydedici.samplerate)
                wf.writeframes(b''.join(self.ses_kaydedici.kareler))

            print(f"Kaydedildi: {dosya_yolu}")

    def kaydi_sifirla(self):
        self.ses_kaydedici.kareler = []
        self.ses_kaydedici.durdur()
        self.zamanlayici.stop()
        self.kayit_suresi = 0
        self.zaman_label.setText("00:00:00")

        self.kayit_butonu.setEnabled(True)
        self.toggle_butonu.setEnabled(False)
        self.toggle_butonu.setText("Durdur")
        self.kaydet_butonu.setEnabled(False)
        self.sifirla_butonu.setEnabled(False)

        print("Kayıt sıfırlandı.")

    def closeEvent(self, event):
        self.ses_kaydedici.durdur()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = SesSeviyeGozlemcisi()
    pencere.show()
    sys.exit(app.exec_())
