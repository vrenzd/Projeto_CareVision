from ultralytics import YOLO
import cv2
from matplotlib import pyplot as plt

model = YOLO("Modelos/best.pt")

def rodar_video(video_path):
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(source=frame, conf=0.5, stream=True)

        for r in results:
            annotated_frame = r.plot()
            cv2.imshow("YOLOv11 - Vídeo", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def rodar_webcam():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(source=frame, conf=0.5, stream=True)

        for r in results:
            annotated_frame = r.plot()
            cv2.imshow("YOLOv11 - Webcam", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def testar_imagem(caminho_imagem):
    # Faz a predição
    results = model.predict(caminho_imagem, conf=0.5, show=False)  # show=False para não abrir janela do cv2

    # Pega a imagem anotada do primeiro resultado
    annotated_img = results[0].plot()

    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.show()

def iniciar_sess():
    print("Escolha uma opção:")
    print("1 - Rodar vídeo gravado")
    print("2 - Usar webcam")
    print("3 - Testar imagem")

    numero = input("Digite: ")

    if numero == "1":
        caminho_video = input("Digite o caminho do vídeo (ex: video.mp4): ")
        rodar_video(caminho_video)
    elif numero == "2":
        rodar_webcam()
    elif numero == '3':
        caminho_imagem = input('Digite o caminho da imagem: ')
        testar_imagem(caminho_imagem)
    else:
        print("Opção inválida.")

iniciar_sess()