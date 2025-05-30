from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import cv2
import numpy as np

model_yolo = YOLO("Modelo-PréTreinado/best.pt")
FRAMES_PARADO = 10
LIMIAR_VELOCIDADE = 1.0
CLASSES_VEICULOS = [3, 4, 5, 8, 9]

tracker = DeepSort(max_age=30)
historico = {}  # {track_id: {'pos': (x, y), 'parado': 0}}

# === FUNÇÃO DETECÇÃO + TRACKING ===
def detectar_e_trackear_veiculos(frame, model_yolo, tracker, classes_veiculos):
    results = model_yolo.predict(source=frame, conf=0.5, classes=classes_veiculos, stream=True)
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            if cls in classes_veiculos:
                detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls))
    tracks = tracker.update_tracks(detections, frame=frame)
    return tracks

def compensar_movimento_camera(prev_gray, curr_gray):
    """
    Calcula o movimento médio global entre dois frames (optical flow).
    Retorna vetor (dx, dy) a ser subtraído do movimento dos objetos.
    """
    flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None,
                                        pyr_scale=0.5, levels=3, winsize=15,
                                        iterations=3, poly_n=5, poly_sigma=1.2, flags=0)
    media_flow = np.mean(flow.reshape(-1, 2), axis=0)
    return media_flow

# === FUNÇÃO DE VÍDEO ===
def rodar_video(video_path):
    cap = cv2.VideoCapture(video_path)
    prev_gray = None
    media_flow = np.array([0, 0])
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
    
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            media_flow = compensar_movimento_camera(prev_gray, gray)
        prev_gray = gray

        tracks = detectar_e_trackear_veiculos(frame, model_yolo, tracker, CLASSES_VEICULOS)

        for track in tracks:
                    if not track.is_confirmed():
                        continue
                    track_id = track.track_id
                    ltrb = track.to_ltrb()
                    x1, y1, x2, y2 = map(int, ltrb)
                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

                    # Calcular velocidade
                    if track_id in historico:
                        px, py = historico[track_id]['pos']
                        dx = (cx - px) - media_flow[0]
                        dy = (cy - py) - media_flow[1]
                        velocidade = np.linalg.norm([dx, dy])
                        if velocidade < LIMIAR_VELOCIDADE:
                            historico[track_id]['parado'] += 1
                        else:
                            historico[track_id]['parado'] = 0
                    else:
                        velocidade = -1
                        historico[track_id] = {'pos': (cx, cy), 'parado': 0}

                    historico[track_id]['pos'] = (cx, cy)

                    # Desenhar caixas e alertas
                    cor = (0, 255, 0)
                    if historico[track_id]['parado'] >= FRAMES_PARADO:
                        cor = (0, 0, 255)
                        cv2.putText(frame, "VEICULO PARADO!", (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2)
                    cv2.putText(frame, f"ID {track_id} V:{velocidade:.1f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor, 2)

        cv2.imshow("YOLO + Rastreamento + Compensação Drone", frame)        

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# === FUNÇÃO DE WEBCAM ===
def rodar_webcam():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break


        results = model_yolo.predict(source=frame, conf=0.5, stream=True)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# === INTERFACE DE USUÁRIO ===
def iniciar_sess():
    print("Escolha uma opção:")
    print("1 - Rodar vídeo gravado")
    print("2 - Usar webcam")

    numero = input("Digite 1 ou 2: ")

    if numero == "1":
        caminho_video = input("Digite o caminho do vídeo (ex: video.mp4): ")
        rodar_video(caminho_video)
    elif numero == "2":
        rodar_webcam()
    else:
        print("Opção inválida.")

iniciar_sess()