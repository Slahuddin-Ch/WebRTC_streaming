# README.md for WebRTC ROS Video Streaming Application

## Overview

This application allows for streaming video over WebRTC using ROS topics. It comprises three main components:

1. **WebRTC Stream Publisher:** Streams a ROS topic video stream using WebRTC.
2. **Signaling Server:** Manages signaling for WebRTC connections.
3. **Receiver:** Receives the WebRTC video stream and displays it.

---

## WebRTC Stream Publisher

### Dependencies:
- Python 3.6+
- `aiortc`, `av`, `opencv-python`, `websockets`

### Description:
This script captures video from a specified ROS topic or a local video device and streams it using WebRTC. It can be configured to change the source, resolution, and framerate.

### Usage:
- Run the script with Python.
- Ensure the ROS topic or local video device is correctly configured.

### Key Components:
- `CameraStreamTrack` class: Captures video from a local device.
- `VideoStreamFromPort` class: Captures video from a ROS topic.
- Functions for handling WebRTC connections and ICE candidates.

---

## Signaling Server

### Dependencies:
- Python 3.6+
- `websockets`

### Description:
This server facilitates the exchange of WebRTC signaling data between the publisher and the receiver. It maintains a list of connected clients and relays messages between them.

### Usage:
- Run the script with Python.
- The server will listen on `ws://localhost:8765`.

### Key Components:
- `handler` coroutine: Manages WebSocket connections and messages.
- `clients` set: Tracks connected clients.

---

## Receiver

### Dependencies:
- Python 3.6+
- `aiortc`, `flask`, `opencv-python`, `websockets`

### Description:
This script establishes a WebRTC connection with the publisher to receive the video stream. It also runs a Flask server to display the received video stream in a web browser.

### Usage:
- Run the script with Python.
- Access the stream via a web browser at `http://38.242.137.75:5000`.

### Key Components:
- Flask app: Serves the web page for video display.
- Functions for handling WebRTC tracks and connections.

---

## Installation

1. **Clone the repository:**
   ```
   git clone [repository-url]
   ```

2. **Install dependencies:**
   ```
   pip install aiortc av opencv-python websockets flask
   ```

3. **Run the components:**
   - Start the signaling server: `python signaling_server.py`
   - Run the WebRTC stream publisher: `python webrtc_stream_publisher.py`
   - Run the receiver: `python receiver.py`

4. **Access the stream:**
   - Open a web browser and go to `http://38.242.137.75:5000`.

---

## Configuration

- Modify the source URL in the WebRTC stream publisher for different ROS topics or video devices.
- Adjust the resolution and framerate in the `CameraStreamTrack` class as needed.
- Ensure the signaling server URL is correctly set in both the publisher and receiver scripts.

---

## Notes
- Change the IPs with your system IPs
- Ensure that all components are running on the same network for proper connectivity.
- The application is designed for educational and demonstration purposes and may require further optimization for production use.
