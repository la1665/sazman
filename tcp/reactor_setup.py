import asyncio
from twisted.internet import asyncioreactor

# Ensure the reactor is installed only once
try:
    asyncioreactor.install(asyncio.get_event_loop())
    print("[INFO] Twisted reactor installed successfully.")
except RuntimeError:
    print("[WARN] Reactor already installed.")
