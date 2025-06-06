import cv2
import mediapipe as mp

# Inicializar MediaPipe Drawing e Pose
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Abrir a câmera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Erro ao abrir a câmera")
    exit()

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Falha ao capturar o frame")
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Tamanho da imagem
            img_h, img_w, _ = image.shape

            # Obter coordenadas dos pontos relevantes
            def get_coords(landmark):
                lm = landmarks[landmark]
                return int(lm.x * img_w), int(lm.y * img_h)

            l_shoulder = get_coords(mp_pose.PoseLandmark.LEFT_SHOULDER)
            r_shoulder = get_coords(mp_pose.PoseLandmark.RIGHT_SHOULDER)
            l_hip = get_coords(mp_pose.PoseLandmark.LEFT_HIP)
            r_hip = get_coords(mp_pose.PoseLandmark.RIGHT_HIP)
            nose = get_coords(mp_pose.PoseLandmark.NOSE)

            # Centros médios
            center_shoulder = ((l_shoulder[0] + r_shoulder[0]) // 2,
                               (l_shoulder[1] + r_shoulder[1]) // 2)
            center_hip = ((l_hip[0] + r_hip[0]) // 2,
                          (l_hip[1] + r_hip[1]) // 2)

            # Verificação 1: Cabeça inclinada (desvio horizontal)
            head_offset_x = abs(nose[0] - center_shoulder[0])
            if head_offset_x > 40:  # margem ajustável
                cv2.putText(image, "Alerta: cabeca inclinada",
                            (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Verificação 2: Ombros desnivelados (desnível vertical)
            shoulder_diff = abs(l_shoulder[1] - r_shoulder[1])
            if shoulder_diff > 20:
                cv2.putText(image, "Alerta: ombros desnivelados",
                            (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            # Verificação 3: Coluna curvada (desvio horizontal entre ombros e quadris)
            spine_offset_x = abs(center_shoulder[0] - center_hip[0])
            if spine_offset_x > 40:
                cv2.putText(image, "Alerta: coluna curvada",
                            (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            # Linhas visuais
            cv2.line(image, center_shoulder, nose, (255, 0, 0), 2)
            cv2.line(image, center_hip, center_shoulder, (0, 255, 0), 2)

        # Desenhar os pontos
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.imshow('Posture Monitoring', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
