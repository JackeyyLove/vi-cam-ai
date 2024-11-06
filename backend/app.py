import cv2
import base64
import requests
import json
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading

# Initialize Flask app and Flask-SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# RTSP URL for IP camera
RTSP_URL = "rtsp://admin:OINVHA@192.168.122.32:554/ch1/main"

# AI server URL
AI_SERVER_URL = "https://equally-in-glowworm.ngrok-free.app/fire-detect"

# Function to send image to AI server asynchronously
def send_image_to_api_async(base64_image):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "image": base64_image  # The Base64 encoded image string
    }

    # Send request in a separate thread
    def send_request():
        try:
            response = requests.post(AI_SERVER_URL, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                print("AI Response Success:", result)
                # Emit the AI result to the connected clients
                socketio.emit('ai_result', result)
            else:
                print("AI Response Error:", response.status_code, response.text)
        except Exception as e:
            print("Exception occurred while calling AI server:", str(e))

    threading.Thread(target=send_request).start()

# Function to process and send frames
def capture_and_process_stream():
    cap = cv2.VideoCapture(RTSP_URL)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Resize the frame for easier handling and encoding
        resized_frame = cv2.resize(frame, (640, 480))

        # Convert frame to JPEG format and encode as base64 for WebSocket
        _, buffer = cv2.imencode('.jpg', resized_frame)
        img_bytes = buffer.tobytes()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # Send the frame to the WebSocket clients
        socketio.emit('frame', {'image': img_base64})

        # Call the asynchronous API function
        #send_image_to_api_async(img_base64)

        # Frame delay to control stream rate (adjust as needed)
        time.sleep(1)

    cap.release()

# Endpoint for the web interface
@app.route('/')
def index():
    return render_template('index.html')

# Start capturing stream in a background thread
@socketio.on('connect')
def on_connect():
    print("Client connected")
    socketio.start_background_task(target=capture_and_process_stream)

@socketio.on('disconnect')
def on_disconnect():
    print("Client disconnected")

# Run the app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
