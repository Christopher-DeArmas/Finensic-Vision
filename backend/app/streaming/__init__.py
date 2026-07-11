"""Real-time streaming: WebSocket connection manager + transaction simulator."""

from app.streaming.connection_manager import ConnectionManager
from app.streaming.simulator import TransactionSimulator

# Shared singletons used by the app + WebSocket route.
manager = ConnectionManager()
simulator = TransactionSimulator(manager)

__all__ = ["ConnectionManager", "TransactionSimulator", "manager", "simulator"]
