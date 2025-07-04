from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import cv2
import numpy as np
import os
import datetime
from utils.config import DRONE_MODEL_PATH, MAQUETE_MODEL_PATH, OUTPUT_DIR

def compensar_movimento_camera(prev_gray, curr_gray):
    flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None,
                                        pyr_scale=0.5, levels=3, winsize=15,
                                        iterations=3, poly_n=5, poly_sigma=1.2, flags=0)
    media_flow = np.mean(flow.reshape(-1, 2), axis=0)
    return media_flow

def calcular_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = area1 + area2 - inter_area
    if union_area == 0:
        return 0
    return inter_area / union_area

MIN_W, MAX_W = 15, 200  # Ajuste para sua escala
MIN_H, MAX_H = 15, 200

class DetectorDeVeiculos:
    def __init__(self):

        self.model_yolo = YOLO(DRONE_MODEL_PATH).to('cuda')
        self.tracker = DeepSort(max_age=40)
        self.CLASSES_VEICULOS = [3, 4, 5, 8, 9]

    def detectar_e_trackear(self, frame):
        # Passo 1: YOLO
        results = self.model_yolo.predict(source=frame, conf=0.6, classes=self.CLASSES_VEICULOS, stream=False)
        detections = []
        infos = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                w = x2 - x1
                h = y2 - y1
                
                if cls in self.CLASSES_VEICULOS and conf > 0.5 and MIN_W < w < MAX_W and MIN_H < h < MAX_H:
                    x_center = x1 + w / 2
                    y_center = y1 + h / 2
                    detections.append(([x_center, y_center, w, h], conf, cls))
                    infos.append({
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "conf": conf,
                        "cls": cls,
                        "matched": False,   
                        "track_id": None,
                    })

        # Passo 2: DeepSort
        tracks = self.tracker.update_tracks(detections, frame=frame)

        # Passo 3: Associação - para cada track confirmado, associe ao bbox mais próximo (IoU)
        for track in tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            track_bbox = track.to_ltrb()
            best_iou = 0
            best_info = None
            for info in infos:
                iou = calcular_iou(track_bbox, info["bbox"])
                if iou > best_iou and not info["matched"]:
                    best_iou = iou
                    best_info = info
            if best_info and best_iou > 0.1:  # threshold para considerar a associação
                best_info["track_id"] = track.track_id
                track.conf = best_info["conf"]
                track.cls = best_info["cls"]
                best_info["matched"] = True
            else:
                track.conf = None
                track.cls = None
        infos = [info for info in infos if "track_id" in info]
        return tracks, infos

class DetectorDeAcidentes:
    def __init__(self):
        self.prev_gray = None
        self.colisoes_ativas = {}      # (id1, id2): frames_colidindo
        self.status_acidente = {}      # (id1, id2): True/False
        self.historico_pos = {}        # track_id: [(x, y)]
        self.frames_parado = {}        # track_id: frames parado
        self.frames_desvio = {}        # track_id: frames de desvio
        self.LIMIAR_IOU = 0.001
        self.FRAMES_COLISAO = 5
        self.FPS = 25  # coloque o FPS real do seu vídeo aqui!
        self.FRAMES_PARADO = 3 * self.FPS  # 3 segundos
        self.ANGULO_LIMIAR = 35
        self.modeloacidente = YOLO(MAQUETE_MODEL_PATH).to('cuda')
        self.ids_acidentados = set()
        self.acidentes_salvos = set()

    def analisar(self, frame, tracks):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        media_flow = np.array([0, 0])
        if self.prev_gray is not None:
            media_flow = compensar_movimento_camera(self.prev_gray, gray)
        self.prev_gray = gray

        boxes, ids = [], []
        for t in tracks:
            if not t.is_confirmed() or t.time_since_update > 1: continue
            x1, y1, x2, y2 = map(int, t.to_ltrb())
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            boxes.append((x1, y1, x2, y2, cx, cy))
            ids.append(t.track_id)

            # Histórico de posição
            if t.track_id not in self.historico_pos:
                self.historico_pos[t.track_id] = []
            self.historico_pos[t.track_id].append((cx, cy))
            if len(self.historico_pos[t.track_id]) > 10:
                self.historico_pos[t.track_id].pop(0)

        acidentes_ids = set()
        # 1. Colisão entre pares
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                box1, id1 = boxes[i][:4], ids[i]
                box2, id2 = boxes[j][:4], ids[j]
                key = tuple(sorted([id1, id2]))
                iou = calcular_iou(box1, box2)
                # Conta frames colidindo
                if iou > self.LIMIAR_IOU:
                    self.colisoes_ativas[key] = self.colisoes_ativas.get(key, 0) + 1
                    print(f"Frame: Colisão entre {id1}, {id2} | IoU={iou:.2f} | Frames colidindo: {self.colisoes_ativas[key]}")
                else:
                    self.colisoes_ativas[key] = 0
                    self.status_acidente[key] = False

                # Se colidiu por X frames, checar parada/desvio
                if self.colisoes_ativas[key] >= self.FRAMES_COLISAO:
                    for tid in [id1, id2]:
                        parado = self.checar_parado(tid, media_flow)
                        desvio = self.checar_desvio_angular(tid)
                        # Checa condições de acidente
                        if parado >= self.FRAMES_PARADO or desvio:

                            # roda o modelo de acidente nesse recorte
                            accident_results = self.modeloacidente.predict(frame, conf=0.7, stream=False)
                            for r in accident_results:
                                annotated_frame = r.plot()
                            found_accident = False
                            # Checa se encontrou algum acidente com confiança alta
                            for r in accident_results:
                                for box in r.boxes:
                                    acc_conf = float(box.conf[0])
                                    acc_cls = int(box.cls[0])
                                    # ajuste a classe para a do seu modelo, se necessário
                                    if acc_cls == 0 and acc_conf > 0.7:  # supondo classe 0=acidente
                                        found_accident = True
                                        
                            if found_accident:
                                self.status_acidente[key] = True
                                acidentes_ids.add(id1)
                                acidentes_ids.add(id2)
                                print(f"🚨 Acidente detectado! Veículos {id1} e {id2} VALIDADO pelo modelo!")
                                key_sorted = tuple(sorted([id1, id2]))  # pra não diferenciar (2,3) de (3,2)
                                if key_sorted not in self.acidentes_salvos:
                                    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                                    frame_path = os.path.join(OUTPUT_DIR, f"acidente_{id1}_{id2}_{now}_frame.jpg")
                                    cv2.imwrite(frame_path, annotated_frame)
                                    self.acidentes_salvos.add(key_sorted)   # Marca como salvo

                                for r in accident_results:
                                    for box in r.boxes:
                                        acc_x1, acc_y1, acc_x2, acc_y2 = box.xyxy[0].cpu().numpy().astype(int)
                                        # Guarda os track_ids que encostam na caixa de acidente
                                        ids_atingidos = set()
                                        for t in tracks:
                                            if not t.is_confirmed() or t.time_since_update > 1:
                                                continue
                                            vx1, vy1, vx2, vy2 = map(int, t.to_ltrb())
                                            iou = calcular_iou([acc_x1, acc_y1, acc_x2, acc_y2], [vx1, vy1, vx2, vy2])
                                            if iou > 0.03:  # teste para casos extremos
                                                ids_atingidos.add(t.track_id)
                                                print(f"ID {t.track_id} marcado como acidentado pelo IoU={iou:.2f}")

                                        # Se pelo menos um dos envolvidos foi atingido, marque ambos envolvidos no acidente!
                                        if id1 in ids_atingidos or id2 in ids_atingidos:
                                            self.ids_acidentados.add(id1)
                                            self.ids_acidentados.add(id2)
                                            print(f"IDs {id1} e {id2} marcados como acidentados devido ao acidente validado.")
                        else:
                                    print(f"⚠️ Falso positivo filtrado pelo modelo de acidente entre {id1} e {id2}")
        bboxes_acidentes = [boxes[i][:4] for i, tid in enumerate(ids) if tid in acidentes_ids]
        # Retorna apenas bounding boxes dos veículos acidentados
        return bboxes_acidentes, acidentes_ids

    def checar_parado(self, tid, media_flow):
        # Mede velocidade média nos últimos N frames. Se for baixa, conta como parado.
        if len(self.historico_pos[tid]) >= 2:
            p1 = np.array(self.historico_pos[tid][-1])
            p0 = np.array(self.historico_pos[tid][-2])
            desloc = (p1 - p0) - media_flow
            vel = np.linalg.norm(desloc)
            print(f"Track {tid}: vel={vel:.2f}")  # <-- AQUI PRINTA A VELOCIDADE FRAME A FRAME
            if vel < 10:  # ajuste conforme resolução
                self.frames_parado[tid] = self.frames_parado.get(tid, 0) + 1
                print(f"Veículo {tid} parado por {self.frames_parado[tid]} frames")
            else:
                self.frames_parado[tid] = 0
            return self.frames_parado[tid]
        return 0

    def checar_desvio_angular(self, tid):
        # Mede ângulo de direção entre dois vetores de movimento, usando últimos 4 frames
        if len(self.historico_pos[tid]) >= 4:
            v1 = np.array(self.historico_pos[tid][-1]) - np.array(self.historico_pos[tid][-4])
            v2 = np.array(self.historico_pos[tid][-2]) - np.array(self.historico_pos[tid][-5]) if len(self.historico_pos[tid]) >= 5 else v1
            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                ang = np.arccos(np.clip(cos_theta, -1, 1)) * 180 / np.pi
                if ang > self.ANGULO_LIMIAR:
                    return True
        return False