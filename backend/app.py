from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import cv2
import base64
import requests
import threading
import time
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import asyncio
from av import VideoFrame

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
# Variables
RTSP_URL = "rtsp://your_camera_ip_address"
AI_SERVER_URL = "https://equally-in-glowworm.ngrok-free.app/fire-detect"

# Function to send the image and receive response
def send_image_to_ai_server(base64_image):
    headers = {"Content-Type": "application/json"}
    data = {"image": base64_image}
    try:
        response = requests.post(AI_SERVER_URL, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.status_code, "message": response.text}
    except Exception as e:
        return {"error": "exception", "message": str(e)}

# Stream video using WebRTC
class CameraStreamTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(RTSP_URL)
        self.loop = asyncio.get_event_loop()

    async def recv(self):
        if not self.cap.isOpened():
            print("Error: Cannot open video stream.")
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # Convert frame to Base64 for AI server
        _, buffer = cv2.imencode('.jpg', frame)
        img_bytes = buffer.tobytes()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # Get response from AI server
        response = send_image_to_ai_server(img_base64)
        
        # Draw AI response (bounding boxes) on the frame if detection is positive
        if response.get("status"):
            for detection in response["result"]:
                class_id = int(detection["class"])
                score = detection["confidence_score"]
                x1, y1, x2, y2 = map(int, detection["coords"])
                color = (0, 0, 255) if class_id == 1 else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"Fire {score:.2f}" if class_id == 1 else f"No Fire {score:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Convert frame for WebRTC
        frame = VideoFrame.from_ndarray(frame, format="bgr24")
        frame.pts, frame.time_base = await self.next_timestamp()
        return frame

# WebRTC endpoint
@app.route("/offer", methods=["POST"])
async def offer():
    params = await request.json
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc.addTrack(CameraStreamTrack())

    @pc.on("icecandidate")
    def on_icecandidate(event):
        socketio.emit("icecandidate", event.candidate)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return jsonify({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    socketio.run(app, debug=True)
