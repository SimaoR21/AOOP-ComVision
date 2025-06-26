import cv2
import mediapipe as mp
import time
import os
import requests
from dotenv import load_dotenv
import threading
from unidecode import unidecode

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print(" ERRO: API Key do OpenRouter nao encontrada no .env!")
    exit()

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def get_llm_feedback(alerts):
    prompt = (
        "O utilizador tem os seguintes problemas de postura: "
        + ", ".join(alerts)
        + ". Para cada um desses problemas, dá apenas **uma ou duas** sugestões para corrigir, com no máximo 10 palavras cada. "
          "Não incluas sugestões para problemas que não estejam listados. "
          "Responde com uma frase por linha, uma por problema."
    )
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [
                    {"role": "system", "content": "És um assistente que dá conselhos simples e objetivos sobre postura corporal."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6,
                "max_tokens": 100
            }
        )
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(" ERRO ao contactar o LLM (OpenRouter):", e)
        return ""

def wrap_text(text, max_chars_per_line=40):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        while len(word) > max_chars_per_line:
            lines.append(word[:max_chars_per_line])
            word = word[max_chars_per_line:]
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            if current_line:
                current_line += ' ' + word
            else:
                current_line = word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

feedback_text = ""
alerts_to_send = []
lock = threading.Lock()

def feedback_worker():
    global feedback_text, alerts_to_send
    while True:
        time.sleep(0.1)
        with lock:
            if alerts_to_send:
                alerts_copy = alerts_to_send.copy()
                alerts_to_send.clear()
            else:
                alerts_copy = None
        if alerts_copy:
            feedback = get_llm_feedback(alerts_copy)
            feedback = unidecode(feedback)
            with lock:
                feedback_text = feedback

threading.Thread(target=feedback_worker, daemon=True).start()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print(" ERRO ao abrir a camera")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

last_feedback_time = 0
display_feedback_until = 0
last_alerts = []

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        alerts = []
        current_time = time.time()

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            img_h, img_w, _ = image.shape

            def get_coords(landmark):
                lm = landmarks[landmark]
                return int(lm.x * img_w), int(lm.y * img_h)

            l_shoulder = get_coords(mp_pose.PoseLandmark.LEFT_SHOULDER)
            r_shoulder = get_coords(mp_pose.PoseLandmark.RIGHT_SHOULDER)
            l_hip = get_coords(mp_pose.PoseLandmark.LEFT_HIP)
            r_hip = get_coords(mp_pose.PoseLandmark.RIGHT_HIP)
            nose = get_coords(mp_pose.PoseLandmark.NOSE)

            center_shoulder = ((l_shoulder[0] + r_shoulder[0]) // 2,
                               (l_shoulder[1] + r_shoulder[1]) // 2)
            center_hip = ((l_hip[0] + r_hip[0]) // 2,
                          (l_hip[1] + r_hip[1]) // 2)

            cv2.line(image, center_shoulder, nose, (255, 0, 0), 2)
            cv2.line(image, center_hip, center_shoulder, (0, 255, 0), 2)

            head_offset_x = abs(nose[0] - center_shoulder[0])
            if head_offset_x > 40:
                alerts.append("Cabeca inclinada")
                cv2.putText(image, "Cabeca inclinada", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            shoulder_diff = abs(l_shoulder[1] - r_shoulder[1])
            if shoulder_diff > 20:
                alerts.append("Ombros desnivelados")
                cv2.putText(image, "Ombros desnivelados", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

            spine_offset_x = abs(center_shoulder[0] - center_hip[0])
            if spine_offset_x > 40:
                alerts.append("Coluna desalinhada")
                cv2.putText(image, "Coluna desalinhada", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        # Atualizar feedback apenas se os alertas forem realmente diferentes e estáveis
        with lock:
            if set(alerts) != set(last_alerts):
                if current_time - last_feedback_time > 5:
                    alerts_to_send.clear()
                    alerts_to_send.extend(alerts)
                    last_feedback_time = current_time
                    last_alerts = alerts.copy()
                    display_feedback_until = current_time + 8
            elif alerts:
                display_feedback_until = current_time + 8
            else:
                if current_time > display_feedback_until:
                    feedback_text = ""
                    last_alerts = []

            text_to_show = feedback_text

        # Desenhar feedback no ecrã
        if text_to_show:
            lines = wrap_text(text_to_show, max_chars_per_line=40)
            y0 = 150
            line_height = 25
            box_height = line_height * len(lines) + 10
            box_width = 600
            overlay = image.copy()
            cv2.rectangle(overlay, (5, y0 - 20), (5 + box_width, y0 + box_height), (0, 0, 0), -1)
            alpha = 0.6
            image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

            for i, line in enumerate(lines):
                y = y0 + i * line_height
                cv2.putText(image, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 255), 2)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.imshow('Posture Monitoring + LLM Feedback (OpenRouter)', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
