import cv2
import mediapipe as mp
import socket
import time

# ---------- UDP Setup ----------
UDP_IP, UDP_PORT = "127.0.0.1", 5055
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ---------- MediaPipe Setup ----------
mp_face = mp.solutions.face_mesh
face = mp_face.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ---------- OpenCV Setup ----------
cap = cv2.VideoCapture(0)
WINDOW_NAME = "Facial Input"
cv2.namedWindow(WINDOW_NAME)

# ---------- Blink Detection Parameters ----------
right_eye_indices = [33, 160, 158, 133, 153, 144]  # Right eye landmarks (Mediapipe)
left_eye_indices = [362, 385, 387, 263, 373, 380]  # Left eye landmarks

EAR_THRESH = 0.20      # Lowered threshold for eye closed
BLINK_MIN_FRAMES = 2   # Min frames eyes closed to count blink
BLINK_MAX_FRAMES = 6   # Max frames eyes closed to count blink

blink_counter = 0
blink_detected = False
blink_cooldown = 0
COOLDOWN_FRAMES = 10  # frames to wait after a blink detection

def eye_aspect_ratio(lm, eye_indices):
    p1 = lm[eye_indices[1]]
    p2 = lm[eye_indices[5]]
    p3 = lm[eye_indices[2]]
    p4 = lm[eye_indices[4]]
    p5 = lm[eye_indices[0]]
    p6 = lm[eye_indices[3]]

    vert1 = abs(p2.y - p4.y)
    vert2 = abs(p3.y - p5.y)
    horiz = abs(p1.x - p6.x)

    ear = (vert1 + vert2) / (2.0 * horiz) if horiz != 0 else 0
    return ear

def is_smiling(lm):
    left_mouth = lm[61]
    right_mouth = lm[291]
    top_lip = lm[13]
    bottom_lip = lm[14]

    mouth_width = right_mouth.x - left_mouth.x
    mouth_height = bottom_lip.y - top_lip.y

    if mouth_height == 0:
        return False

    smile_ratio = mouth_width / mouth_height

    return smile_ratio > 4.5  # Stricter smile threshold

def get_expression(lm):
    global blink_counter, blink_detected, blink_cooldown

    ear_right = eye_aspect_ratio(lm, right_eye_indices)
    ear_left = eye_aspect_ratio(lm, left_eye_indices)
    ear = (ear_right + ear_left) / 2.0


    if blink_cooldown > 0:
        blink_cooldown -= 1
        return "center"

    if ear < EAR_THRESH:
        blink_counter += 1
    else:
        if BLINK_MIN_FRAMES < blink_counter < BLINK_MAX_FRAMES:
            blink_detected = True
            blink_cooldown = COOLDOWN_FRAMES
            blink_counter = 0
            return "blink"
        blink_counter = 0

    if is_smiling(lm):
        return "smile"

    return "center"

def map_to_lane(expr):
    if expr == "blink":
        return "right"
    elif expr == "smile":
        return "left"
    return "center"

last_lane = "center"
last_send_time = 0
SEND_INTERVAL = 0.5  # seconds

# Send initial 'center' command to start forward motion
sock.sendto(b"center", (UDP_IP, UDP_PORT))
print("Sent: center")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face.process(rgb)

    lane = "center"

    if result.multi_face_landmarks:
        lm = result.multi_face_landmarks[0].landmark
        expr = get_expression(lm)
        lane = map_to_lane(expr)

        cv2.putText(frame, f"Expression: {expr}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    current_time = time.time()

    if lane != last_lane:
        sock.sendto(lane.encode(), (UDP_IP, UDP_PORT))
        print("Sent:", lane)
        last_lane = lane
        last_send_time = current_time
    elif lane == "center" and current_time - last_send_time > SEND_INTERVAL:
        sock.sendto(b"center", (UDP_IP, UDP_PORT))
        print("Sent: center (periodic)")
        last_send_time = current_time

    cv2.imshow(WINDOW_NAME, frame)
    if cv2.waitKey(5) & 0xFF == 27 or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
