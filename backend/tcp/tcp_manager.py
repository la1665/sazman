from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning

from database.engine import async_session
from models.lpr import DBLpr
from models.camera import DBCamera
from tcp.tcp_client import ReconnectingTCPClientFactory
from shared_resources import connections

# Dictionary to store active LPR connections

async def add_connection(session: AsyncSession, camera_id: int):
    """
    Add a new connection for the LPR.
    """
    global connections
    camera_query = await session.execute(select(DBCamera).where(DBCamera.id == camera_id))
    db_camera = camera_query.unique().scalar_one_or_none()
    if db_camera and db_camera.is_active:
        lpr = db_camera.lpr
        if lpr:
            if lpr.id not in connections:
                factory = ReconnectingTCPClientFactory(lpr.id,  lpr.ip, lpr.port, lpr.auth_token)
                connections[lpr.id] = factory
                # Connect to the server
                reactor.callFromThread(factory._attempt_reconnect)
                print(f"[INFO] Added connection for LPR ID {lpr.id}")
            else:
                print(f"Connection for LPR ID {lpr.id} already exists.")
        else:
            print(f"No lpr object found for this camera: {db_camera.id}: {db_camera.name}")
    else:
        print("INFO] could not create connection for LPR related to this camera")
    print(f"all connections: {connections}")



async def update_connection(lpr_id: int, server_ip: str, port: int, auth_token: str):
    """
    Update an existing connection with new settings.
    """
    if lpr_id in connections:
        remove_connection(lpr_id)  # Remove the old connection

    await add_connection(lpr_id, server_ip, port, auth_token)
    print(f"[INFO] Updated connection for LPR ID {lpr_id}")

def remove_connection(lpr_id: int):
    """
    Remove an existing connection.
    """
    if lpr_id in connections:
        factory = connections.pop(lpr_id)
        reactor.callFromThread(factory.stopTrying)  # Stop reconnection attempts
        print(f"[INFO] Removed connection for LPR ID {lpr_id}")
    else:
        raise ValueError(f"No connection found for LPR ID {lpr_id}")

def shutdown_all_connections():
    """
    Shutdown all active connections.
    """
    try:
        for lpr_id in list(connections.keys()):
            remove_connection(lpr_id)
        reactor.stop()
        print("[INFO] All connections stopped.")
    except ReactorNotRunning:
        print("[INFO] Reactor is already stopped.")
