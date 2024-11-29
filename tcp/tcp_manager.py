from sqlalchemy.future import select
from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning

from database.engine import async_session
from models.lpr import DBLpr
from tcp.tcp_client import ReconnectingTCPClientFactory

# Dictionary to store active LPR connections
connections = {}

async def add_connection(lpr_id: int, server_ip: str, port: int, auth_token: str):
    """
    Add a new connection for the LPR.
    """
    if lpr_id in connections:
        raise ValueError(f"Connection for LPR ID {lpr_id} already exists.")
    async with async_session() as session:
        query = await session.execute(select(DBLpr).where(DBLpr.id==lpr_id))
        db_lpr = query.unique().scalar_one_or_none()
        if db_lpr and db_lpr.is_active:
            factory = ReconnectingTCPClientFactory(server_ip, port, auth_token)
            connections[lpr_id] = factory

            # Connect to the server
            reactor.callFromThread(factory._attempt_reconnect)
            print(f"[INFO] Added connection for LPR ID {lpr_id}")
        else:
            print(f"INFO] could not create connection for LPR ID {lpr_id}, unactive lpr")
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
