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
TELEGRAM_BOT_TOKEN = "" #Replace with actual bot token
TELEGRAM_CHAT_ID = "" # replace with actual chat id


# Set to keep track of RTCPeerConnection instances
pcs = set()
camera_id = 0 #"rtsp://admin:OINVHA@192.168.1.180:554/ch1/main"  # Replace with your camera's RTSP URL
AI_ADULT_DETECT = "https://equally-in-glowworm.ngrok-free.app/adult-child-detect"
AI_FIRE_DETECT = "https://equally-in-glowworm.ngrok-free.app/fire-detect"

# Global variables to store the latest full response from AI servers
latest_adult_child_response = {}
latest_fire_response = {}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(response.text)
    return response

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
                #latest_adult_child_response["image"] = img_base64

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
        print("Something")
        # Send request to AI server
        try:
            response = requests.post(AI_FIRE_DETECT, json=data, headers=headers)
            if response.status_code == 200:
                # Update the latest full response
                latest_fire_response = response.json()
                #latest_fire_response["image"] = img_base64

                # Check if fire is detected
                for result in latest_fire_response.get("result", []):
                    if result["class"] == 1.0:
                        message = f"Fire detected with confidence score: {result['confidence_score']}"
                        send_telegram_message(message)
                        break
            else: 
                send_telegram_message("Error in fire detection")
        except Exception as e:
            print("Exception in fire detection:", e)

        time.sleep(0.5)


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
