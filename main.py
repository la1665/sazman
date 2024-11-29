from tcp import reactor_setup
import uvicorn
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lifespan import lifespan
from router.base import include_router
from router.auth import auth_router
from router.user import user_router
from router.lpr import lpr_router
from socket_management import sio

# start_reactor()

app = FastAPI(
    title="Sazman",
    description="License Plate Reader",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

include_router(app, auth_router)
include_router(app, user_router)
include_router(app, lpr_router)

@app.get("/")
async def root():
    """
    Root endpoint for health check.
    """
    return {"message": "Welcome to the Sazman API!"}



app_socket = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)

def main():
    """
    Main entry point for running the FastAPI app.
    """
    uvicorn.run("main:app_socket", host="0.0.0.0", port=8000, log_level="debug")
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="debug")


if __name__ == "__main__":
    main()
