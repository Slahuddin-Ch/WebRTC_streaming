import asyncio
import websockets
import json
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
import threading
from flask import Flask, render_template, Response





# Shared variables for the latest frame
app = Flask(__name__)
latest_frame = None
frame_lock = threading.Lock()



@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



async def on_track(track):
    global latest_frame
    if track.kind == "video":
        frame_count = 0
        while True:
            try:
                frame = await track.recv()
                frame_count +=1
                print(f"FRAME RECEIVED: {frame_count}")
                image = frame.to_ndarray(format="bgr24")

                with frame_lock:
                    latest_frame = image

            except Exception as e:
                print(f"Error processing frame: {e}")
                break


async def receive_video(pc, signaling):
    @pc.on("datachannel")
    def on_datachannel(channel):
        print("Data channel opened")

    @pc.on("iceconnectionstatechange")
    def on_iceconnectionstatechange():
        print("ICE Connection State is now", pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            print("ICE Connection has failed, attempting to restart ICE")
            asyncio.create_task(pc.restartIce())

    @pc.on("connectionstatechange")
    def on_connectionstatechange():
        print("Connection State is now", pc.connectionState)

    @pc.on("track")
    async def track_handler(track):
        print("Track received:", track.kind)
        if track.kind == "video":
            await on_track(track)

    print("Waiting for offer")
    offer = json.loads(await signaling.recv())
    print("Offer received:", offer['offer'])

    await pc.setRemoteDescription(RTCSessionDescription(offer['offer'], 'offer'))
    print("Remote description set")

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await signaling.send(json.dumps({"answer": pc.localDescription.sdp}))
    print("Answer sent:", pc.localDescription.sdp)

    while True:
        candidate = json.loads(await signaling.recv())
        if candidate and candidate['candidate']:
            print(f"Adding ICE candidate: {candidate}")
            candidate = RTCIceCandidate(candidate['candidate'])
            await pc.addIceCandidate(candidate)
        else:
            print("No more ICE candidates, breaking out of loop")
            break


async def main():
    global latest_frame
    # Connect to the signaling server
    signaling = await websockets.connect('ws://38.242.137.75:8765')
    pc = RTCPeerConnection()

    # Set up event handlers for the peer connection
    @pc.on("track")
    async def on_track_handler(track):
        await on_track(track)

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate:
            print("New ICE candidate:", candidate)

    try:
        await asyncio.gather(receive_video(pc, signaling))
    finally:
        print("Closing connection")
        await signaling.close()


# Running Flask in a separate thread
def run_flask():
    app.run(host='38.242.137.75', port=5000, threaded=True, debug=True, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(main())

~                                            