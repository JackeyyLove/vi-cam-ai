from flask import Flask, render_template, Response, request, jsonify
from aiortc import RTCPeerConnection, RTCSessionDescription
import cv2
import json
import uuid
import asyncio
import logging
import time
import threading
import requests
import base64
from flask_cors import CORS  # Import CORS

# Create a Flask app instance
app = Flask(__name__, static_url_path='/static')
CORS(app)

# Set to keep track of RTCPeerConnection instances
pcs = set()
camera_id = "rtsp://admin:OINVHA@192.168.1.180:554/ch1/main"  # Replace with your camera's RTSP URL
AI_ADULT_DETECT = "https://equally-in-glowworm.ngrok-free.app/adult-child-detect"
AI_FIRE_DETECT = "https://equally-in-glowworm.ngrok-free.app/fire-detect"

# Global variables to store the latest full response from AI servers
latest_adult_child_response = {}
latest_fire_response = {}


# Function to continuously request adult-child detection and store the full response
def continuous_adult_child_detection():
    global latest_adult_child_response
    while True:
        # Capture the frame and encode to Base64
        camera = cv2.VideoCapture(camera_id, cv2.CAP_FFMPEG)
        success, frame = camera.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        img_bytes = buffer.tobytes()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # Prepare request data
        headers = {"Content-Type": "application/json"}
        data = {"image": img_base64}
        # Send request to AI server
        try:
            response = requests.post(AI_ADULT_DETECT, json=data, headers=headers)
            if response.status_code == 200:
                # Update the latest full response
                latest_adult_child_response = response.json()

        except Exception as e:
            print("Exception in adult-child detection:", e)

        time.sleep(0.5)  # Optional delay to reduce API call frequency


# Function to continuously request fire detection and store the full response
def continuous_fire_detection():
    global latest_fire_response
    while True:
        # Capture the frame and encode to Base64
        camera = cv2.VideoCapture(camera_id, cv2.CAP_FFMPEG)
        success, frame = camera.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        img_bytes = buffer.tobytes()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # Prepare request data
        headers = {"Content-Type": "application/json"}
        data = {"image": img_base64}

        # Send request to AI server
        try:
            response = requests.post(AI_FIRE_DETECT, json=data, headers=headers)
            if response.status_code == 200:
                # Update the latest full response
                latest_fire_response = response.json()
        except Exception as e:
            print("Exception in fire detection:", e)

        time.sleep(0.5)  # Optional delay to reduce API call frequency


# Start the continuous detection functions in separate threads
threading.Thread(target=continuous_adult_child_detection, daemon=True).start()
threading.Thread(target=continuous_fire_detection, daemon=True).start()


# Function to generate video frames from the camera
def generate_frames():
    camera = cv2.VideoCapture(camera_id, cv2.CAP_FFMPEG)
    while True:
        success, frame = camera.read()
        if not success:
            break
            # Draw rectangles for adult-child detection
        if "result" in latest_adult_child_response:
            for detection in latest_adult_child_response["result"]:
                coords = detection["coords"]
                # Draw the rectangle based on coords: [x1, y1, x2, y2]
                cv2.rectangle(frame, (int(coords[0]), int(coords[1])), (int(coords[2]), int(coords[3])),
                              (0, 255, 0), 2)
                # Optional: add label for "adult/child" with confidence score
                label = f"Class: {int(detection['class'])}, Conf: {detection['confidence_score']:.2f}"
                cv2.putText(frame, label, (int(coords[0]), int(coords[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 2)

        # Draw rectangles for fire detection
        if "result" in latest_fire_response:
            for detection in latest_fire_response["result"]:
                coords = detection["coords"]
                # Draw the rectangle based on coords: [x1, y1, x2, y2]
                cv2.rectangle(frame, (int(coords[0]), int(coords[1])), (int(coords[2]), int(coords[3])),
                              (0, 0, 255), 2)
                # Optional: add label for "fire" with confidence score
                label = f"Fire, Conf: {detection['confidence_score']:.2f}"
                cv2.putText(frame, label, (int(coords[0]), int(coords[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 0, 255), 2)

        # Encode frame to JPEG and yield for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# Route to render the HTML template
@app.route('/')
def index():
    return render_template('index.html')


# Asynchronous function to handle offer exchange
async def offer_async():
    params = await request.json
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    # Create an RTCPeerConnection instance
    pc = RTCPeerConnection()

    # Generate a unique ID for the RTCPeerConnection
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pc_id = pc_id[:8]

    # Create and set the local description
    await pc.createOffer(offer)
    await pc.setLocalDescription(offer)

    # Prepare the response data with local SDP and type
    response_data = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

    return jsonify(response_data)


# Wrapper function for running the asynchronous offer function
def offer():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    future = asyncio.run_coroutine_threadsafe(offer_async(), loop)
    return future.result()


# Route to handle the offer request
@app.route('/offer', methods=['POST'])
def offer_route():
    return offer()


# Route to stream video frames
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Combined endpoint to get both adult-child and fire detection responses
@app.route('/detect', methods=['GET'])
def get_combined_detection_response():
    response_data = {
        "adult_child_detection": latest_adult_child_response,
        "fire_detection": latest_fire_response
    }
    print(response_data)
    return jsonify(response_data)


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
