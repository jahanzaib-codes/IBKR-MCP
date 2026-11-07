import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load local .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class IBKRSettings(BaseModel):
    """Configuration settings for Interactive Brokers MCP Server."""
    
    # TWS / IB Gateway connection params
    host: str = Field(default_factory=lambda: os.getenv("IBKR_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("IBKR_PORT", "7497")))
    client_id: int = Field(default_factory=lambda: int(os.getenv("IBKR_CLIENT_ID", "42")))
    timeout_sec: int = Field(default_factory=lambda: int(os.getenv("IBKR_TIMEOUT_SEC", "15")))
    mock_fallback: bool = Field(default_factory=lambda: os.getenv("IBKR_MOCK_FALLBACK", "true").lower() in ("true", "1", "yes"))
    
    # Risk & Guardrails (Human-in-the-Loop)
    read_only: bool = Field(default_factory=lambda: os.getenv("IBKR_READ_ONLY", "true").lower() in ("true", "1", "yes"))
    max_order_value_usd: float = Field(default_factory=lambda: float(os.getenv("MAX_ORDER_VALUE_USD", "10000.0")))
    allow_live_trading: bool = Field(default_factory=lambda: os.getenv("ALLOW_LIVE_TRADING", "false").lower() in ("true", "1", "yes"))
    require_explicit_confirm: bool = Field(default_factory=lambda: os.getenv("REQUIRE_EXPLICIT_CONFIRM", "true").lower() in ("true", "1", "yes"))

    # Server transport
    transport: str = Field(default_factory=lambda: os.getenv("MCP_TRANSPORT", "stdio"))
    sse_host: str = Field(default_factory=lambda: os.getenv("MCP_SSE_HOST", "127.0.0.1"))
    sse_port: int = Field(default_factory=lambda: int(os.getenv("MCP_SSE_PORT", "8000")))


settings = IBKRSettings()
