import asyncio
import websockets
import uuid

class Client:
    def __init__(self, websocket):
        self.websocket = websocket
        self.id = str(uuid.uuid4())
        self.active = True

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

clients = set()

async def handler(websocket, path):
    client = Client(websocket)
    clients.add(client)
    print(f"New client connected: {client.id}. Total clients: {len(clients)}")

    try:
        while True:
            message = await websocket.recv()
            print(f"Received message from client {client.id}: {message}")

            for other_client in clients:
                if other_client != client and other_client.active:
                    print(f"Sending message to client {other_client.id}.")
                    await other_client.websocket.send(message)
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client.id} disconnected.")
        # Here, instead of removing the client, mark as inactive
        client.active = False
        # Optionally, you can implement a reconnection timeout mechanism

async def clean_inactive_clients():
    while True:
        inactive_clients = {client for client in clients if not client.active}
        for client in inactive_clients:
            # Here you can check if the client has been inactive for too long and remove them
            pass
        await asyncio.sleep(10)  # Check every 10 seconds, for example

clients = set()
start_server = websockets.serve(handler, "38.242.137.75", 8765)

print("Starting signaling server on ws://localhost:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().create_task(clean_inactive_clients())
asyncio.get_event_loop().run_forever()

~                                                                                                                