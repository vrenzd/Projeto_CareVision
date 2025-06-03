import sys
import cv2
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QScrollArea,
    QCheckBox, QLabel, QHBoxLayout, QMenuBar, QMenu, QAction, QFrame,
    QPushButton, QInputDialog
)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap


class VideoWindow(QWidget):
    janela_fechada = pyqtSignal(int)

    def __init__(self, cap, nome_camera, cam_index):
        super().__init__()
        self.cap = cap
        self.cam_index = cam_index
        self.setWindowTitle(f"Visualização - {nome_camera}")

        self.label_video = QLabel()
        self.label_video.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label_video)
        self.setLayout(layout)

        self.resize(900, 600)
        self.setMinimumSize(640, 480)

        self.running = True
        self.start_video_thread()

        self.show()

    def start_video_thread(self):
        import threading
        thread = threading.Thread(target=self.update_frame, daemon=True)
        thread.start()

    def update_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

                pixmap = QPixmap.fromImage(qt_image).scaled(
                    self.label_video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.label_video.setPixmap(pixmap)
            else:
                break
            cv2.waitKey(30)

    def closeEvent(self, event):
        # Apenas para parar o thread e emitir o sinal, mas NÃO liberar o cap aqui
        if self.running:
            self.running = False
            self.janela_fechada.emit(self.cam_index)
        event.accept()

class AllCamerasWindow(QWidget):
    def __init__(self, cameras_indices, settings):
        super().__init__()
        self.setWindowTitle("Visualização de Todas as Câmeras")
        self.settings = settings
        self.cameras_indices = cameras_indices
        self.capturas = {}
        self.labels = {}

        layout = QHBoxLayout(self)
        self.setLayout(layout)

        # Para cada câmera, abre e adiciona QLabel para exibir o vídeo
        for idx in cameras_indices:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                self.capturas[idx] = cap
                label = QLabel()
                label.setFixedSize(320, 240)
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
                self.labels[idx] = label

        self.running = True
        self.start_video_thread()

        self.resize(1000, 400)
        self.show()

    def start_video_thread(self):
        import threading
        thread = threading.Thread(target=self.update_frames, daemon=True)
        thread.start()

    def update_frames(self):
        while self.running:
            for idx, cap in self.capturas.items():
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame_rgb.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image).scaled(
                        self.labels[idx].size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.labels[idx].setPixmap(pixmap)
            cv2.waitKey(30)

    def closeEvent(self, event):
        self.running = False
        for cap in self.capturas.values():
            cap.release()
        event.accept()


class MainWindow(QMainWindow):
    alerta_movimento_signal = pyqtSignal(int)  # sinal para emitir alerta

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Care Vision")
        self.setGeometry(100, 100, 900, 700)

        self.settings = QSettings("CareVision", "UserSettings")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Menu de temas
        menubar = QMenuBar(self)
        menu_temas = QMenu("Temas", self)
        self.action_tema_claro = QAction("Claro", self)
        self.action_tema_escuro = QAction("Escuro", self)
        self.action_tema_claro.triggered.connect(lambda: self.salvar_e_aplicar_tema("claro"))
        self.action_tema_escuro.triggered.connect(lambda: self.salvar_e_aplicar_tema("escuro"))
        menu_temas.addAction(self.action_tema_claro)
        menu_temas.addAction(self.action_tema_escuro)
        menubar.addMenu(menu_temas)
        self.setMenuBar(menubar)

        # Área das câmeras com scroll
        self.scroll_container = QFrame()
        self.scroll_container.setMaximumWidth(500)
        self.scroll_layout = QVBoxLayout(self.scroll_container)

        self.scroll = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout_inner = QVBoxLayout(self.scroll_widget)

        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scroll_widget)

        self.scroll_layout.addWidget(self.scroll)
        self.main_layout.addWidget(self.scroll_container)

        # Botão Visualizar Todas as câmeras
        self.btn_visualizar_todas = QPushButton("Visualizar Todas")
        self.btn_visualizar_todas.setFixedWidth(150)
        self.btn_visualizar_todas.clicked.connect(self.abrir_todas_cameras)
        self.main_layout.addWidget(self.btn_visualizar_todas)

        # Área de alertas (nova)
        self.alertas_container = QFrame()
        self.alertas_container.setFrameShape(QFrame.StyledPanel)
        self.alertas_container.setMaximumHeight(400)  # Aumentado de 200 para 400 px
        self.alertas_layout = QVBoxLayout(self.alertas_container)
        self.alertas_layout.setContentsMargins(10, 10, 10, 10)
        self.alertas_layout.setSpacing(5)

        label_alertas = QLabel("Alertas de Movimento")
        label_alertas.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.main_layout.addWidget(label_alertas)
        self.main_layout.addWidget(self.alertas_container)

        self.alertas_widget_layout = QVBoxLayout()
        self.alertas_layout.addLayout(self.alertas_widget_layout)
        self.alertas_ativos = {}

        self.checkboxes = {}
        self.btn_editar_nomes = {}
        cameras = self.detectar_cameras_disponiveis()

        if not cameras:
            label = QLabel("Nenhuma câmera detectada.")
            self.scroll_layout_inner.addWidget(label)
        else:
            for cam_index in cameras:
                num_cam = cam_index + 1
                nome_salvo = self.settings.value(f"camera_nome_{num_cam}", f"Câmera {num_cam}")

                checkbox = QCheckBox(nome_salvo)
                checkbox.stateChanged.connect(self.atualizar_visualizacao_cameras)

                btn_editar = QPushButton("Editar Nome")
                btn_editar.setFixedWidth(90)
                btn_editar.clicked.connect(lambda checked, idx=cam_index: self.editar_nome_camera(idx))

                self.checkboxes[cam_index] = checkbox
                self.btn_editar_nomes[cam_index] = btn_editar

                hbox = QHBoxLayout()
                hbox.addWidget(checkbox)
                hbox.addSpacing(10)
                hbox.addWidget(btn_editar)
                hbox.addStretch()

                container = QWidget()
                container.setLayout(hbox)

                self.scroll_layout_inner.addWidget(container)

        self.scroll_widget.setLayout(self.scroll_layout_inner)

        self.capturas = {}
        self.janelas_camera = {}

        tema_salvo = self.settings.value("tema", "claro")
        if tema_salvo == "escuro":
            self.aplicar_tema_escuro()
        else:
            self.aplicar_tema_claro()

        # Conecta sinal do alerta para mostrar na interface
        self.alerta_movimento_signal.connect(self.adicionar_alerta)

        # Flag para controlar o monitoramento do movimento
        self.monitorar_movimento = True

        # Inicia thread de monitoramento das câmeras para movimento
        import threading
        self.thread_monitoramento = threading.Thread(target=self.monitorar_movimentos_cameras, daemon=True)
        self.thread_monitoramento.start()

    def editar_nome_camera(self, cam_index):
        num_cam = cam_index + 1
        nome_atual = self.settings.value(f"camera_nome_{num_cam}", f"Câmera {num_cam}")
        novo_nome, ok = QInputDialog.getText(self, "Editar Nome", f"Nome da câmera {num_cam}:", text=nome_atual)
        if ok and novo_nome.strip():
            self.settings.setValue(f"camera_nome_{num_cam}", novo_nome.strip())
            self.checkboxes[cam_index].setText(novo_nome.strip())
            if cam_index in self.janelas_camera:
                self.janelas_camera[cam_index].setWindowTitle(f"Visualização - {novo_nome.strip()}")

    def salvar_e_aplicar_tema(self, tema):
        self.settings.setValue("tema", tema)
        if tema == "escuro":
            self.aplicar_tema_escuro()
        else:
            self.aplicar_tema_claro()

    def detectar_cameras_disponiveis(self):
        cameras = []
        for index in range(10):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                cameras.append(index)
            cap.release()
        return cameras

    def aplicar_tema_claro(self):
        estilo_claro = """
            QWidget {
                background-color: #fdfdfd;
                color: #202020;
                font-family: "Segoe UI", sans-serif;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #e6e6e6;
                border: 1px solid #aaa;
                padding: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #d6d6d6;
            }
            QCheckBox {
                padding: 5px;
            }
            QMenuBar {
                background-color: #f0f0f0;
            }
            QMenuBar::item {
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #cccccc;
            }
            QMenu {
                background-color: #f0f0f0;
                border: 1px solid #aaa;
            }
            QMenu::item:selected {
                background-color: #d0d0d0;
            }
            QFrame {
                background-color: #eef3f7;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """
        QApplication.instance().setStyleSheet(estilo_claro)

    def aplicar_tema_escuro(self):
        estilo_escuro = """
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: "Segoe UI", sans-serif;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #5a5a5a;
                padding: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #4c5052;
            }
            QCheckBox {
                padding: 5px;
            }
            QMenuBar {
                background-color: #2b2b2b;
            }
            QMenuBar::item {
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #444;
            }
            QMenu {
                background-color: #3c3f41;
                border: 1px solid #5a5a5a;
            }
            QMenu::item:selected {
                background-color: #505354;
            }
            QFrame {
                background-color: #3a3f44;
                border: 1px solid #555;
                border-radius: 8px;
            }
        """
        QApplication.instance().setStyleSheet(estilo_escuro)

    def atualizar_visualizacao_cameras(self):
        for index, checkbox in self.checkboxes.items():
            if checkbox.isChecked() and index not in self.capturas:
                self.abrir_camera(index)
            elif not checkbox.isChecked() and index in self.capturas:
                self.fechar_camera(index)

    def abrir_camera(self, index):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            self.capturas[index] = cap
            nome_camera = self.settings.value(f"camera_nome_{index+1}", f"Câmera {index+1}")
            janela = VideoWindow(cap, nome_camera, index)
            janela.janela_fechada.connect(self.on_janela_camera_fechada)
            self.janelas_camera[index] = janela
        else:
            print(f"Não foi possível abrir a câmera {index + 1}.")

    def abrir_todas_cameras(self):
        cameras = list(self.checkboxes.keys())
        if hasattr(self, 'janela_todas_cameras') and self.janela_todas_cameras.isVisible():
            self.janela_todas_cameras.activateWindow()
            return
        self.janela_todas_cameras = AllCamerasWindow(cameras, self.settings)
        self.janela_todas_cameras.show()

    def fechar_camera(self, index):
        cap = self.capturas.pop(index, None)
        if cap:
            cap.release()
            print(f"Câmera {index + 1} fechada.")
        if index in self.janelas_camera:
            # Desconecta para evitar emitir sinal duplo
            janela = self.janelas_camera.pop(index)
            janela.janela_fechada.disconnect(self.on_janela_camera_fechada)
            janela.close()

    def on_janela_camera_fechada(self, cam_index):
        if cam_index in self.checkboxes:
            self.checkboxes[cam_index].setChecked(False)
            if cam_index in self.capturas:
                cap = self.capturas.pop(cam_index)
                cap.release()
            if cam_index in self.janelas_camera:
                del self.janelas_camera[cam_index]

    def detectar_movimento(self, cap):
        # Método simples de detecção de movimento por diferença de frames
        ret, frame1 = cap.read()
        ret2, frame2 = cap.read()
        if not ret or not ret2:
            return False
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, 65, 255, cv2.THRESH_BINARY)
        contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contorno in contornos:
            if cv2.contourArea(contorno) > 1500:  # área mínima para considerar movimento
                return True
        return False

    def monitorar_movimentos_cameras(self):
        caps = {}
        for cam_index in self.checkboxes.keys():
            cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
            if cap.isOpened():
                caps[cam_index] = cap

        while self.monitorar_movimento:
            for cam_index, cap in caps.items():
                if not cap.isOpened():
                    continue
                movimento = self.detectar_movimento(cap)
                if movimento and cam_index not in self.alertas_ativos:
                    self.alerta_movimento_signal.emit(cam_index)
                time.sleep(0.1)
            time.sleep(0.5)

        for cap in caps.values():
            cap.release()

    def adicionar_alerta(self, cam_index):
        nome_camera = self.settings.value(f"camera_nome_{cam_index+1}", f"Câmera {cam_index+1}")
        alerta_widget = QWidget()
        layout = QHBoxLayout(alerta_widget)
        label = QLabel(f"Movimento detectado na {nome_camera}")
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(50)
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(btn_ok)

        def remover_alerta():
            self.alertas_widget_layout.removeWidget(alerta_widget)
            alerta_widget.deleteLater()
            if cam_index in self.alertas_ativos:
                del self.alertas_ativos[cam_index]

        btn_ok.clicked.connect(remover_alerta)

        self.alertas_widget_layout.addWidget(alerta_widget)
        self.alertas_ativos[cam_index] = alerta_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())