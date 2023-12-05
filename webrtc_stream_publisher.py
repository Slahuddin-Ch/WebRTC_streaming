

import asyncio
import json
import av
import cv2
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCIceCandidate, VideoStreamTrack
from av import VideoFrame
import websockets
from fractions import Fraction
import zlib
import sys
import time
import numpy as np
import re



class CameraStreamTrack(VideoStreamTrack):
    def __init__(self, device='/dev/video0'):
        super().__init__()
        self.device = device
        self.frame_counter = 0
        self.cap = av.open(self.device, format='video4linux2', mode='r')
        self.cap.streams.video[0].thread_type = "AUTO"  # Enable multi-threading
        self.cap.streams.video[0].width = 100  # Reduce resolution
        self.cap.streams.video[0].height = 100
        self.cap.streams.video[0].framerate = 5  # Reduce framerate

    async def recv(self):
        raw_frame = next(self.cap.decode(video=0))

        self.frame_counter += 1
        print(f"Received frame #{self.frame_counter} from the camera SIZE beofre #{sys.getsizeof(raw_frame)}")
        return raw_frame


class VideoStreamFromPort(VideoStreamTrack):
    def __init__(self, stream_url):
        super().__init__()
        self.stream_url = stream_url
        self.cap = cv2.VideoCapture(stream_url)
        self.frame_count = 0
    

    async def recv(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame from video source")
                return

            self.frame_count += 1
            print(f"Sending frame {self.frame_count}")

            video_frame = VideoFrame.from_ndarray(frame, format='bgr24')
            video_frame.pts, video_frame.time_base = await self.next_timestamp()
            return video_frame
        else:
            print("Video source not opened")

async def create_offer(pc):
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    logging.info("Created and set local offer")
    return offer

async def exchange_offer_answer(pc, signaling):
    offer = await create_offer(pc)
    await signaling.send(json.dumps({"offer": offer.sdp}))
    logging.info("Sent offer to signaling server")

    answer = json.loads(await signaling.recv())
    logging.info("Received answer from signaling server")
    await pc.setRemoteDescription(RTCSessionDescription(answer['answer'], 'answer'))
    logging.info("Set remote description with received answer")

async def handle_ice_candidates(pc, signaling):
    logging.info("Handling ICE candidates")
    pattern = re.compile(
        r'candidate:(?P<foundation>\S+) (?P<component>\d+) (?P<protocol>\S+) '
        r'(?P<priority>\d+) (?P<ip>\S+) (?P<port>\d+) typ (?P<type>\S+)(?: raddr (?P<raddr>\S+) rport (?P<rport>\d+))?'
    )

    while True:
        message = await signaling.recv()

        # Check if message is a string and needs to be parsed as JSON
        if isinstance(message, str):
            message_data = json.loads(message)
        else:
            message_data = message

        if 'candidate' in message_data:
            match = pattern.match(message_data['candidate']['candidate'])
            if not match:
                logging.error("Could not parse ICE candidate")
                continue

            candidate_data = match.groupdict()
            candidate = RTCIceCandidate(
                foundation=candidate_data['foundation'],
                component=int(candidate_data['component']),
                transport=candidate_data['protocol'],
                priority=int(candidate_data['priority']),
                ip=candidate_data['ip'],
                port=int(candidate_data['port']),
                type=candidate_data['type'],
                relatedAddress=candidate_data.get('raddr'),
                relatedPort=int(candidate_data['rport']) if candidate_data.get('rport') else None
            )
            await pc.addIceCandidate(candidate)
            logging.info("Added ICE candidate")
        elif message_data.get('end_of_candidates'):
            logging.info("End of ICE candidates")
            break


async def renegotiate(pc, signaling):
    logging.info("Renegotiating connection")
    await exchange_offer_answer(pc, signaling)
    await handle_ice_candidates(pc, signaling)

async def run(pc, video_track, signaling):
    pc.addTrack(video_track)
    logging.info("Video track added to peer connection")

    await renegotiate(pc, signaling)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        logging.info(f"ICE Connection State changed to {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            logging.warning("ICE Connection failed, attempting renegotiation")
            await renegotiate(pc, signaling)

async def main():
    logging.info("Starting main function")

    #if you want to use laptop camera stream uncoment the code below and comment the stream_url

    # video_track = CameraStreamTrack()
    stream_url = 'http://localhost:8080/stream?topic=/kinect_ir/kinect/image_raw' # Replace with your actual stream URL
    video_track = VideoStreamFromPort(stream_url)
    logging.info("Camera stream source created")


    signaling = await websockets.connect('ws://38.242.137.75:8765')
    logging.info("Connected to WebSocket signaling server")

    pc = RTCPeerConnection()
    # Define ICE servers
    ice_servers = [
        RTCIceServer(
            urls="stun:stun.relay.metered.ca:80",  # Use Google's public STUN server
        ),
        RTCIceServer(
            urls="turn:a.relay.metered.ca:80",
            username="e25b7d6ecf765b145095080c",
            credential="izRXsAYFq1epa503",
        ),
        RTCIceServer(
            urls="turn:a.relay.metered.ca:80?transport=tcp",
            username="e25b7d6ecf765b145095080c",
            credential="izRXsAYFq1epa503",
        ),
        RTCIceServer(
            urls="turn:a.relay.metered.ca:443",
            username="e25b7d6ecf765b145095080c",
            credential="izRXsAYFq1epa503",
        ),
        RTCIceServer(
            urls="turn:a.relay.metered.ca:443?transport=tcp",
            username="e25b7d6ecf765b145095080c",
            credential="izRXsAYFq1epa503",
        ),
    ]
    pc.iceServers = ice_servers
    print("ICE servers set")

    try:
        await run(pc, video_track, signaling)
    finally:
        await signaling.close()
        logging.info("Signaling closed")

if __name__ == "__main__":
    asyncio.run(main())
