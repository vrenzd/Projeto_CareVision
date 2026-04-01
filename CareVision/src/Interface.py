import sys, os
from detectors.Detector import DetectorDeVeiculos, DetectorDeAcidentes
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QScrollArea,
    QCheckBox, QLabel, QHBoxLayout, QMenuBar, QMenu, QAction, QFrame,
    QPushButton, QInputDialog,QGraphicsOpacityEffect, QFileDialog
)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal, QTimer, QUrl, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont, QColor, QPalette
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from utils.config import INPUT_DIR
from utils.envio_alerta import acionar_alerta_emergencia
import threading

class VideoWindow(QWidget):
    janela_fechada = pyqtSignal(int)
    acidente_detectado = pyqtSignal()

    def __init__(self, cap, nome_camera, cam_index):
        super().__init__()
        self.cap = cap
        self.cam_index = cam_index
        self.nome_camera = nome_camera
        self.setWindowTitle(f"Visualização - {nome_camera}")
        self.label_video = QLabel()
        self.label_video.setAlignment(Qt.AlignCenter)
        self.is_file = (cam_index == -1)
        self.frame_count = 0
        self.detector_veiculos = DetectorDeVeiculos()
        self.detector_acidentes = DetectorDeAcidentes()
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.label_video)
        self.setLayout(layout)

        self.resize(900, 600)
        self.setMinimumSize(640, 480)

        self.running = True
        self.start_video_thread()

        self.show()

    def start_video_thread(self):
        thread = threading.Thread(target=self.update_frame, daemon=True)
        thread.start()

    def update_frame(self):
        
        self.is_file = isinstance(self.cap, cv2.VideoCapture) and self.cam_index == -1  # ou outra lógica para diferenciar arquivos

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            tracks, infos = self.detector_veiculos.detectar_e_trackear(frame)
        
            bboxes_acidente, acidentes_ids = self.detector_acidentes.analisar(frame, tracks)
        
            for info in infos:
                x1, y1, x2, y2 = info['bbox']
                conf = info['conf']
                classe = info['cls']
                track_id = info['track_id']
                conf_text = f"{conf:.2f}" if conf is not None else "N/A"
                classe_text = f"{classe}" if classe is not None else "None"
                color = (0,0,255) if (track_id is not None and track_id in self.detector_acidentes.ids_acidentados) else (0,255,0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f'ID:{track_id} Conf:{conf_text} Cls:{classe_text}', (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            acidente_ativo = (len(self.detector_acidentes.ids_acidentados) > 0)
            if acidente_ativo and not getattr(self, '_acidente_em_andamento', False):
                self._acidente_em_andamento = True
                tipo = "frontal"
                envolvidos = len(acidentes_ids)
                fogo = 1
                local = self.nome_camera

            # Chama o alerta em uma nova thread
                threading.Thread(
                    target=acionar_alerta_emergencia, 
                    args=(tipo, envolvidos, fogo, local),
                    daemon=True
                ).start()
                self.acidente_detectado.emit()  # <-- dispara sinal
                
            if not acidente_ativo:
                self._acidente_em_andamento = False
            
            if acidente_ativo:
                if (self.frame_count // 10) % 2 == 0:
                    color = (0, 0, 255)  # Vermelho (BGR)
                else:
                    color = (255, 0, 0)  # Azul (BGR)
                texto = "Acidente"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 2
                thickness = 4                    
                (text_w, text_h), _ = cv2.getTextSize(texto, font, font_scale, thickness)
                x = frame.shape[1] - text_w - 40  # 40 pixels da borda direita
                y = 60  # topo

                cv2.putText(frame, texto, (x, y), font, font_scale, color, thickness, cv2.LINE_AA) 
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(qt_image).scaled(
                self.label_video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label_video.setPixmap(pixmap)
            self.frame_count += 1

            if not self.is_file:
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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CareVision")
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

        #Menu para Upload de Arquivo
        menu_arquivo = QMenu("Upload", self) # Crie um novo menu chamado "Upload"
        # Ação para Upload de Vídeo
        self.action_upload_video = QAction("Upload de Vídeo", self)
        # Conecta a uma nova função ou a uma que trate o tipo de arquivo
        self.action_upload_video.triggered.connect(lambda: self.abrir_arquivo_como_camera(file_type="video"))
        menu_arquivo.addAction(self.action_upload_video)

        # Ação para Upload de Imagem
        self.action_upload_image = QAction("Upload de Imagem", self)
        # Conecta a uma nova função ou a uma que trate o tipo de arquivo
        self.action_upload_image.triggered.connect(lambda: self.abrir_arquivo_como_camera(file_type="image"))
        menu_arquivo.addAction(self.action_upload_image)

        menubar.addMenu(menu_arquivo) # Adiciona o menu de upload à barra de menu

        self.setMenuBar(menubar) # Define a barra de menu na janela principal

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

    def abrir_arquivo_como_camera(self, file_type=None):
    # Abre uma caixa de diálogo para selecionar um arquivo de vídeo ou imagem
        options = QFileDialog.Options()
        fileName = ""

        if file_type == "video":
            fileName, _ = QFileDialog.getOpenFileName(self,
                                                        "Selecionar Vídeo",
                                                        "", # Diretório inicial
                                                        "Arquivos de Vídeo (*.mp4 *.avi *.mov *.mkv);;Todos os Arquivos (*)",
                                                        options=options)
        elif file_type == "imagem":
            fileName, _ = QFileDialog.getOpenFileName(self,
                                                    "Selecionar Imagem",
                                                    "", # Diretório inicial
                                                    "Arquivos de Imagem (*.jpg *.jpeg *.png *.bmp);;Todos os Arquivos (*)",
                                                    options=options)
        else: # Se nenhum tipo específico for fornecido (cairá aqui se chamada de outro lugar)
            fileName, _ = QFileDialog.getOpenFileName(self,
                                                    "Selecionar Vídeo ou Imagem",
                                                    "",
                                                    "Arquivos de Mídia (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp);;Vídeos (*.mp4 *.avi *.mov *.mkv);;Imagens (*.jpg *.jpeg *.png *.bmp);;Todos os Arquivos (*)",
                                                    options=options)
        if fileName:
            file_cam_index = -1 # Um índice arbitrário e alto para arquivos

            # Se já houver um arquivo aberto, feche-o primeiro
            if file_cam_index in self.capturas:
                self.fechar_camera(file_cam_index)

            cap = cv2.VideoCapture(fileName)
            if cap.isOpened():
                self.capturas[file_cam_index] = cap
                nome_arquivo = fileName.split('/')[-1] # Pega apenas o nome do arquivo
                janela = VideoWindow(cap, f"Arquivo - {nome_arquivo}", file_cam_index)
                janela.acidente_detectado.connect(self.abrir_alarme)
                # Conecte o sinal de fechamento da janela do arquivo também
                janela.janela_fechada.connect(self.on_janela_camera_fechada)
                self.janelas_camera[file_cam_index] = janela
                print(f"Arquivo '{nome_arquivo}' aberto como câmera.")
            else:
                print(f"Não foi possível abrir o arquivo: {fileName}")
                # Se for uma imagem, OpenCV pode ler mas o cap.read() só funcionará uma vez
                # Para tratar imagens, você precisaria de uma lógica diferente, talvez abrindo com cv2.imread
                # e exibindo estaticamente na VideoWindow.
                # Este exemplo foca mais em vídeos.
                try:
                    img = cv2.imread(fileName)
                    if img is not None:
                        # Se for uma imagem, cria um objeto VideoCapture falso ou um adaptador
                        # ou exibe diretamente na VideoWindow (que precisa de um ajuste para imagens estáticas)
                        # Para este exemplo, manteremos o foco em arquivos que o VideoCapture pode lidar
                        print(f"O arquivo '{fileName}' parece ser uma imagem. O tratamento de imagens estáticas requer ajustes adicionais na VideoWindow.")
                    else:
                        print(f"Formato de arquivo não suportado ou corrompido: {fileName}")
                except Exception as e:
                    print(f"Erro ao tentar abrir como imagem: {e}")

    def editar_nome_camera(self, cam_index):
        num_cam = cam_index + 1
        nome_atual = self.settings.value(f"camera_nome_{num_cam}", f"Câmera {num_cam}")
        novo_nome, ok = QInputDialog.getText(self, "Editar Nome", f"Nome da câmera {num_cam}:", text=nome_atual)
        if ok and novo_nome.strip():
            self.settings.setValue(f"camera_nome_{num_cam}", novo_nome.strip())
            self.checkboxes[cam_index].setText(novo_nome.strip())
            if cam_index in self.janelas_camera:
                self.janelas_camera[cam_index].setWindowTitle(f"Visualização - {novo_nome.strip()}")
        return novo_nome.strip()
        

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
            janela.acidente_detectado.connect(self.abrir_alarme)
            janela.janela_fechada.connect(self.on_janela_camera_fechada)
            self.janelas_camera[index] = janela

        else:
            print(f"Não foi possível abrir a câmera {index + 1}.")
        return nome_camera

    def abrir_alarme(self):
        self.alarm_window = AlarmApp()  # Salve em um atributo para não ser destruída
        self.alarm_window.show()
        self.alarm_window.activate_alarm()

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

class AlarmApp(QWidget):
    def __init__(self):
        super().__init__()
        self.alarm_active = False
        self.blink_state = True

        # Media setup
        self.player = QMediaPlayer()
        self.player.mediaStatusChanged.connect(self.replay_audio)

        # Timer for blinking
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.pulse_button)

        # Alarm button
        self.button = QPushButton('✓ Tráfego seguro')
        self.button.setMinimumSize(260, 85)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.clicked.connect(self.acknowledge_alarm)

        # Apply opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.button.setGraphicsEffect(self.opacity_effect)

        # Fade-in animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Frame layout
        self.frame = QFrame()
        self.frame_layout = QHBoxLayout()
        self.frame_layout.addWidget(self.button, alignment=Qt.AlignCenter)
        self.frame.setLayout(self.frame_layout)
        self.frame.setStyleSheet("border-radius: 12px; padding: 15px;")

        # Title label
        self.title_label = QLabel('🚨 Alerta de Colisão 🚨')
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont('Segoe UI', 22, QFont.Bold))

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.frame)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(25)

        self.setLayout(self.main_layout)
        self.setWindowTitle('Alerta de Colisão')
        self.setMinimumSize(420, 270)
        sinal = os.path.join(INPUT_DIR, 'sinal.png')
        self.setWindowIcon(QIcon(sinal))

        self.set_safe_style()

    def set_safe_style(self):
        self.button.setText('✓ Tráfego seguro')
        self.set_button_style()
        self.button.setStyleSheet(self.button.styleSheet() + """
            QPushButton {
                background-color: #28a745;
            }
        """)
        self.fade_animation.start()

    def set_alert_style(self):
        self.button.setText('⚠ INFRAÇÃO DETECTADA!')
        self.set_button_style()
        self.fade_animation.start()

    def set_button_style(self):
        base_color = "#28a745" if not self.alarm_active else "#dc3545"
        pulse_color = "#218838" if not self.alarm_active else "#c82333"
        hover_color = "#1e7e34" if not self.alarm_active else "#bd2130"
        text_color = "#ffffff"

        self.button.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: {text_color};
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: {pulse_color};
            }}
            QPushButton:pressed {{
                background-color: {hover_color};
            }}
        """)

    def activate_alarm(self):
        if not self.alarm_active:
            audio = os.path.join(INPUT_DIR, 'alarme.mp3')
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(audio)))
            self.player.setVolume(100)
            self.player.play()
            self.set_alert_style()
            self.blink_timer.start(600)
            self.alarm_active = True

    def pulse_button(self):
        self.blink_state = not self.blink_state
        pulse_color = "#e63946" if self.blink_state else "#dc3545"
        self.button.setStyleSheet(self.button.styleSheet().replace(
            "#dc3545", pulse_color
        ).replace("#e63946", pulse_color))

    def acknowledge_alarm(self):
        if self.alarm_active:
            self.blink_timer.stop()
            self.player.stop()
            self.set_safe_style()
            self.alarm_active = False
    
    def replay_audio(self, status):
        # Se o áudio terminou, reinicia se ainda estiver em alarme!
        if status == QMediaPlayer.EndOfMedia and self.alarm_active:
            self.player.setPosition(0)
            self.player.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
