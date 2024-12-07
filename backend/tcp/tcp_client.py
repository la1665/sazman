import json
import uuid
import hmac
import hashlib
import asyncio
from twisted.internet import protocol

from settings import settings
from database.engine import async_session
from socket_management import emit_to_requested_sids


async def fetch_lpr_settings(lpr_id: int):
    from sqlalchemy.future import select
    from models.lpr import DBLpr

    async with async_session() as session:
        query = await session.execute(select(DBLpr).where(DBLpr.id == lpr_id))
        lpr = query.scalar_one_or_none()
        if not lpr:
            raise ValueError(f"LPR with ID {lpr_id} not found.")
        # Prepare data for cameras and their settings
        cameras_data = []
        for camera in lpr.cameras:
            camera_data = {
                "camera_id": camera.id,
                "settings": []
            }
            for setting in camera.settings:
                if setting.setting_type.value == "int":
                    value = int(setting.value)
                elif setting.setting_type.value == "float":
                    value = float(setting.value)
                elif setting.setting_type.value == "string":
                    value = str(setting.value)
                else:
                    value = setting.value
                setting_data = {
                    "name": setting.name,
                    "value": value
                }
                camera_data["settings"].append(setting_data)
            cameras_data.append(camera_data)

        settings_data = []
        for setting in lpr.settings:
            if setting.setting_type.value == "int":
                value = int(setting.value)
            elif setting.setting_type.value == "float":
                value = float(setting.value)
            elif setting.setting_type.value == "string":
                value = str(setting.value)
            else:
                value = setting.value
            setting_data = {
                "name": setting.name,
                "value": value
            }
            settings_data.append(setting_data)

        return {"lpr_id": lpr.id, "settings": settings_data, "cameras_data": cameras_data}


class SimpleTCPClient(protocol.Protocol):
    def __init__(self):
        self.auth_message_id = None
        self.incomplete_data = ""
        self.authenticated = False  # Track authentication status locally
        self.message_queue = asyncio.Queue()

    def connectionMade(self):
        """Called when a connection to the server is made."""
        print(f"[INFO] Connected to {self.transport.getPeer()}")
        self.authenticate()
        # Start processing the message queue
        asyncio.create_task(self.process_message_queue())
        # defer.ensureDeferred(self.process_message_queue())

    def authenticate(self):
        """Sends an authentication message with a secure token."""
        self.auth_message_id = str(uuid.uuid4())
        auth_message = self._create_auth_message(self.auth_message_id, self.factory.auth_token)
        self._send_message(auth_message)
        print(f"[INFO] Authentication message sent with ID: {self.auth_message_id}")

    def _create_auth_message(self, message_id, token):
        """Creates a JSON authentication message."""
        return json.dumps({
            "messageId": message_id,
            "messageType": "authentication",
            "messageBody": {"token": token}
        })

    def _send_message(self, message):
        """Sends a message to the server."""
        if self.transport and self.transport.connected:
            print(f"[INFO] Sending message: {message}")
            self.transport.write((message + '\n').encode('utf-8'))
        else:
            print("[ERROR] Transport is not connected. Message not sent.")

    def dataReceived(self, data):
        """Accumulates and processes data received from the server."""
        self.incomplete_data += data.decode('utf-8')
        while '<END>' in self.incomplete_data:
            full_message, self.incomplete_data = self.incomplete_data.split('<END>', 1)
            if full_message:
                # print(f"[DEBUG] Received message: {full_message[:100]}...")
                # Enqueue the complete message for asynchronous processing
                # defer.ensureDeferred(self.message_queue.put(full_message))
                asyncio.create_task(self.message_queue.put(full_message))


    async def process_message_queue(self):
        """Asynchronously processes messages from the queue."""
        try:
            while True:
                message = await self.message_queue.get()
                try:
                    await self._process_message(message)
                except Exception as e:
                    print(f"[ERROR] Exception in processing message: {e}")
                finally:
                    # if not self.message_queue.empty():
                    self.message_queue.task_done()
                    # self.message_queue.task_done()
        except asyncio.CancelledError:
            print("[INFO] Message processing task cancelled. Cleaning up...")
            # Ensure no unprocessed items are left in the queue
            while not self.message_queue.empty():
                self.message_queue.get_nowait()
                # self.message_queue.task_done()

    async def _process_message(self, message):
        """Processes each received message."""
        try:
            parsed_message = json.loads(message)
            message_type = parsed_message.get("messageType")
            handler = {
                "acknowledge": self._handle_acknowledgment,
                "command_response": self._handle_command_response,
                "plates_data": self._handle_plates_data,
                "live": self._handle_live_data
            }.get(message_type, self._handle_unknown_message)
            await handler(parsed_message)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse message: {e}")

    async def _handle_acknowledgment(self, message):
        reply_to = message["messageBody"].get("replyTo")
        if reply_to == self.auth_message_id:
            print("[INFO] Authentication successful.")
            self.authenticated = True
            self.factory.authenticated = True

            # Fetch and send LPR settings
            try:
                # Assuming LPR ID is passed in the factory or another way
                lpr_settings = await fetch_lpr_settings(self.factory.lpr_id)
                hmac_key = settings.HMAC_SECRET_KEY.encode()
                data_str = json.dumps(lpr_settings, separators=(',', ':'), sort_keys=True)
                hmac_signature = hmac.new(hmac_key, data_str.encode(), hashlib.sha256).hexdigest()
                settings_message = {
                    "messageId": self.auth_message_id,
                    "messageType": "lpr_settings",
                    "messageBody":
                        {
                            "data": lpr_settings,
                            "hmac": hmac_signature
                        }
                }
                self._send_message(json.dumps(settings_message))
                print("[INFO] LPR settings sent to the server.")
            except Exception as e:
                print(f"[ERROR] Failed to send LPR settings: {e}")

        else:
            print(f"[INFO] Received acknowledgment for message ID: {reply_to}")

    async def _broadcast_to_socketio(self, event_name, data, camera_id):
        """Efficiently broadcast a message to all subscribed clients for an event."""
        await emit_to_requested_sids(event_name, data, camera_id)

    async def _handle_plates_data(self, message):
        # print("Plate data recived")
        message_body = message["messageBody"]
        camera_id = message_body.get("camera_id")
        timestamp = message_body.get("timestamp")
        socketio_message = {
            "messageType": "plates_data",
            "timestamp": timestamp,
            "camera_id": camera_id,
            "full_image": message_body.get("full_image"),
            "cars": [
                {
                    "plate_number": car.get("plate", {}).get("plate", "Unknown"),
                    "plate_image": car.get("plate", {}).get("plate_image", ""),
                    "ocr_accuracy": car.get("ocr_accuracy", "Unknown"),
                    "vision_speed": car.get("vision_speed", 0.0),
                    "vehicle_class": car.get("vehicle_class", {}),
                    "vehicle_type": car.get("vehicle_type", {}),
                    "vehicle_color": car.get("vehicle_color", {})
                }
                for car in message_body.get("cars", [])
            ]
        }
        # print(f"sending to socket ... {socketio_message['camera_id']}")
        asyncio.ensure_future(self._broadcast_to_socketio("plates_data", socketio_message, camera_id))


    async def _handle_command_response(self, message):
        """
        Handles the command response from the server.
        """
        pass

    async def _handle_live_data(self, message):
        message_body = message["messageBody"]
        camera_id = message_body.get("camera_id")
        live_data = {
            "messageType": "live",
            "live_image": message_body.get("live_image"),
            "camera_id": camera_id
        }

        print(f"sending live to socket ... {live_data['camera_id']}")
        asyncio.ensure_future(self._broadcast_to_socketio("live", live_data, camera_id))

    async  def _handle_unknown_message(self, message):
        print(f"[WARN] Received unknown message type: {message.get('messageType')}")

    def send_command(self, command_data):
        if self.authenticated:
            command_message = self._create_command_message(command_data)
            self._send_message(command_message)
        else:
            print("[ERROR] Cannot send command: client is not authenticated.")

    def _create_command_message(self, command_data):
        """Creates and signs a command message with HMAC for integrity."""
        hmac_key = settings.HMAC_SECRET_KEY.encode()
        data_str = json.dumps(command_data, separators=(',', ':'), sort_keys=True)
        hmac_signature = hmac.new(hmac_key, data_str.encode(), hashlib.sha256).hexdigest()
        return json.dumps({
            "messageId": str(uuid.uuid4()),
            "messageType": "command",
            "messageBody": {
                "data": command_data,
                "hmac": hmac_signature
            }
        })

    def connectionLost(self, reason):
        print(f"[INFO] Connection lost: {reason}")
        if self.factory:
            self.factory.clientConnectionLost(self.transport.connector, reason)
        else:
            print("[ERROR] Connection lost without factory reference.")
        # Cancel the message queue processing task
        for task in asyncio.all_tasks():
            if task.get_coro().__name__ == "process_message_queue":
                task.cancel()

from twisted.internet import reactor, ssl

class ReconnectingTCPClientFactory(protocol.ReconnectingClientFactory):
    def __init__(self, lpr_id, server_ip, port, auth_token):
        self.lpr_id = lpr_id
        self.auth_token = auth_token
        self.authenticated = False
        self.active_protocol = None  # Track the active protocol instance
        self.server_ip = server_ip
        self.port = port
        self.reconnecting = False  # Flag to manage reconnections
        self.connection_in_progress = False  # Prevent overlapping connection attempts

    def buildProtocol(self, addr):
        # Always create a new protocol but manage its lifecycle
        print(f"[INFO] Connected to {addr}")
        self.resetDelay()  # Reset reconnection delay on successful connection
        self.reconnecting = False  # Clear reconnecting flag
        self.connection_in_progress = False  # Clear connection-in-progress flag
        client = SimpleTCPClient()
        client.factory = self
        self.active_protocol = client  # Set the active protocol instance
        return client

    def clientConnectionLost(self, connector, reason):
        print(f"[INFO] Connection lost: {reason}. Scheduling reconnect.")
        self.active_protocol = None  # Clear the active protocol on disconnect
        if not self.connection_in_progress:
            self._attempt_reconnect()  # Only attempt reconnect if not already in progress

    def clientConnectionFailed(self, connector, reason):
        print(f"[ERROR] Connection failed: {reason}. Scheduling reconnect.")
        self.active_protocol = None  # Clear the active protocol on failure
        if not self.connection_in_progress:
            self._attempt_reconnect()  # Only attempt reconnect if not already in progress

    def _attempt_reconnect(self):
        """Reconnect with a fixed interval and ensure single connection attempt."""
        if self.connection_in_progress:
            print("[DEBUG] Connection already in progress. Skipping reconnect.")
            return

        if self.active_protocol is not None:
            print("[DEBUG] Client is already connected. No need to reconnect.")
            return

        self.connection_in_progress = True  # Mark connection as in progress
        print(f"[INFO] Attempting to reconnect to {self.server_ip}:{self.port}...")

        # Create SSL context for secure connection
        class ClientContextFactory(ssl.ClientContextFactory):
            def getContext(self):
                context = ssl.SSL.Context(ssl.SSL.TLSv1_2_METHOD)
                context.use_certificate_file(settings.CLIENT_CERT_PATH)
                context.use_privatekey_file(settings.CLIENT_KEY_PATH)
                context.load_verify_locations(settings.CA_CERT_PATH)
                context.set_verify(ssl.SSL.VERIFY_PEER, lambda conn, cert, errno, depth, ok: ok)
                return context

        try:
            reactor.connectSSL(self.server_ip, self.port, self, ClientContextFactory())
        except Exception as e:
            print(f"[ERROR] Reconnection failed: {e}")
        finally:
            # Schedule the next reconnect attempt after 60 seconds
            reactor.callLater(60, self._reset_connection_state_and_retry)

    def _reset_connection_state_and_retry(self):
        if self.active_protocol is not None:
            print("[INFO] Client is already connected. Skipping retry.")
            return
        self.connection_in_progress = False  # Allow new connection attempt
        print("[INFO] Retrying connection...")
        self._attempt_reconnect()






# def connect_to_server(server_ip, port, auth_token):
#     factory = ReconnectingTCPClientFactory(server_ip, port, auth_token)
#     factory._attempt_reconnect()  # Start initial connection attempt
#     return factory



def send_command_to_server(factory, command_data):
    if factory.authenticated and factory.active_protocol:
        print(f"[INFO] Sending command to server: {command_data}")
        factory.active_protocol.send_command(command_data)
    else:
        print("[ERROR] Cannot send command: Client is not authenticated or connected.")

# def graceful_shutdown(signal, frame):
#     print("Shutting down gracefully...")
#     reactor.stop()


# def start_reactor():
#     reactor.run()


# if __name__ == "__main__":
#     server_ip = "185.81.99.23"
#     port = 45

#     # Connect to the server and start reactor
#     factory = connect_to_server(server_ip, port)
#     start_reactor()
