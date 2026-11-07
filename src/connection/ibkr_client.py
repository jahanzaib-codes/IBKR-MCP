import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from config.settings import settings

logger = logging.getLogger("IBKR-MCP.Client")

try:
    from ib_insync import IB, Stock, Option, Future, Forex, MarketOrder, LimitOrder, Contract
    IB_INSYNC_AVAILABLE = True
except ImportError:
    IB_INSYNC_AVAILABLE = False


class IBKRClientManager:
    """
    Manages socket connectivity to Interactive Brokers TWS or IB Gateway.
    Provides automatic reconnection, socket diagnostic health checks,
    and a realistic simulation fallback when TWS is offline or closed.
    """

    def __init__(self, cfg=settings):
        self.cfg = cfg
        self.ib: Optional[Any] = None
        self.is_connected: bool = False
        self.last_heartbeat: float = 0.0
        self.account_id: str = "SIM_DU8391024"
        self._init_ib()

    def _init_ib(self):
        if IB_INSYNC_AVAILABLE:
            try:
                self.ib = IB()
            except Exception as e:
                logger.warning(f"Failed to instantiate ib_insync IB: {e}")
                self.ib = None

    def connect(self) -> bool:
        """Attempts connection to TWS/Gateway socket."""
        if not IB_INSYNC_AVAILABLE or self.ib is None:
            logger.info("ib_insync not initialized. Operating in simulation mode.")
            self.is_connected = False
            return False

        if self.ib.isConnected():
            self.is_connected = True
            return True

        try:
            logger.info(f"Connecting to IBKR TWS at {self.cfg.host}:{self.cfg.port} (Client ID: {self.cfg.client_id})...")
            self.ib.connect(
                host=self.cfg.host,
                port=self.cfg.port,
                clientId=self.cfg.client_id,
                timeout=self.cfg.timeout_sec,
                readonly=self.cfg.read_only
            )
            self.is_connected = self.ib.isConnected()
            if self.is_connected:
                managed_accounts = self.ib.managedAccounts()
                if managed_accounts:
                    self.account_id = managed_accounts[0]
                self.last_heartbeat = time.time()
                logger.info(f"Connected to IBKR successfully. Managed Account: {self.account_id}")
            return self.is_connected
        except Exception as e:
            logger.warning(f"Could not connect to TWS at {self.cfg.host}:{self.cfg.port} ({e}).")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnects socket cleanly."""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            self.is_connected = False
            logger.info("Disconnected from IBKR TWS.")

    def is_live_account(self) -> bool:
        """Returns True if the connected account or port is for LIVE trading."""
        if self.cfg.port in (7496, 4001):
            return True
        if self.account_id.startswith("U") and not self.account_id.startswith("DU"):
            return True
        return False

    def get_health_status(self) -> Dict[str, Any]:
        """Provides full connection diagnostic information matching TWS settings."""
        connected = self.ib.isConnected() if (self.ib and IB_INSYNC_AVAILABLE) else False
        return {
            "connected": connected,
            "host": self.cfg.host,
            "port": self.cfg.port,
            "client_id": self.cfg.client_id,
            "account_id": self.account_id,
            "is_live_account": self.is_live_account(),
            "read_only_mode": self.cfg.read_only,
            "mock_fallback_enabled": self.cfg.mock_fallback,
            "mode": "TWS Live Socket" if connected else ("Simulation / Mock" if self.cfg.mock_fallback else "Disconnected"),
            "timestamp": time.time()
        }


client_manager = IBKRClientManager()
