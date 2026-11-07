#!/usr/bin/env python3
"""
==============================================================================
IBKR-MCP: Institutional Model Context Protocol Server for Interactive Brokers
Connecting Claude Desktop, Cursor, and Autonomous AI Agents to TWS / IB Gateway.
==============================================================================
"""

import sys
import json
import logging
from typing import Optional, Dict, Any, List

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("IBKR-MCP")

from config.settings import settings
from src.connection.ibkr_client import client_manager
from src.safety.guardrails import guardrails
from src.tools.account_tools import get_account_summary, list_portfolio_positions
from src.tools.market_tools import get_market_quote, get_options_chain_snapshot
from src.tools.order_tools import preview_order, place_paper_order, cancel_order, get_open_orders
from src.prompts.templates import (
    get_portfolio_risk_prompt,
    get_trade_idea_prompt,
    get_premarket_briefing_prompt
)

from mcp.server.mcpserver import MCPServer

# Initialize MCP Server
app = MCPServer(
    name="ibkr-mcp",
    description="Interactive Brokers Model Context Protocol Server for AI Agents"
)

# ------------------------------------------------------------------------------
# 1. MCP Tools Registration
# ------------------------------------------------------------------------------

@app.tool(
    name="get_system_health",
    description="Check Interactive Brokers TWS/Gateway socket connection, latency, port status (7497/7496), and safety guardrails."
)
def tool_system_health() -> str:
    """Returns real-time connection and diagnostic health."""
    data = client_manager.get_health_status()
    return json.dumps(data, indent=2)


@app.tool(
    name="get_account_summary",
    description="Retrieve account equity, cash balance, buying power, realized and unrealized PnL, and margin cushion from IBKR."
)
def tool_account_summary(account_id: Optional[str] = None) -> str:
    """Fetches high-level account capital summary."""
    data = get_account_summary(account_id=account_id)
    return json.dumps(data, indent=2)


@app.tool(
    name="list_portfolio_positions",
    description="List all active portfolio positions with symbol, security type, quantity, average cost, market price, and unrealized PnL."
)
def tool_portfolio_positions(account_id: Optional[str] = None) -> str:
    """Lists current holdings across Equities, Options, and Futures."""
    data = list_portfolio_positions(account_id=account_id)
    return json.dumps(data, indent=2)


@app.tool(
    name="get_market_quote",
    description="Fetch live or snapshot market quote (Bid, Ask, Last, Volume, VWAP, High/Low) for US Equities, ETFs, or Futures."
)
def tool_market_quote(
    symbol: str,
    sec_type: str = "STK",
    exchange: str = "SMART",
    currency: str = "USD"
) -> str:
    """Queries quote data for a symbol."""
    data = get_market_quote(symbol=symbol, sec_type=sec_type, exchange=exchange, currency=currency)
    return json.dumps(data, indent=2)


@app.tool(
    name="get_options_chain",
    description="Get options chain analytics including Implied Volatility (IV), IV Rank, Delta, Gamma, Theta, and Vega for SPX/SPY/Equities."
)
def tool_options_chain(symbol: str, target_strike: Optional[float] = None) -> str:
    """Returns options chain and Black-Scholes Greeks."""
    data = get_options_chain_snapshot(symbol=symbol, target_strike=target_strike)
    return json.dumps(data, indent=2)


@app.tool(
    name="preview_order",
    description="Calculate notional value, margin requirement, estimated commissions, and safety checks BEFORE placing any order."
)
def tool_preview_order(
    symbol: str,
    action: str,
    quantity: float,
    order_type: str = "MKT",
    limit_price: Optional[float] = None,
    sec_type: str = "STK"
) -> str:
    """Pre-flight risk and capital preview for proposed trade."""
    data = preview_order(
        symbol=symbol,
        action=action,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        sec_type=sec_type
    )
    return json.dumps(data, indent=2)


@app.tool(
    name="place_paper_order",
    description="Submit an order to the Interactive Brokers PAPER account. Requires confirm=True. Live trading is strictly blocked."
)
def tool_place_paper_order(
    symbol: str,
    action: str,
    quantity: float,
    order_type: str = "MKT",
    limit_price: Optional[float] = None,
    sec_type: str = "STK",
    confirm: bool = False
) -> str:
    """Executes a paper order with human-in-the-loop safety verification."""
    data = place_paper_order(
        symbol=symbol,
        action=action,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        sec_type=sec_type,
        confirm=confirm
    )
    return json.dumps(data, indent=2)


@app.tool(
    name="cancel_order",
    description="Cancel an active or working order by order ID. Requires confirm=True."
)
def tool_cancel_order(order_id: int, confirm: bool = False) -> str:
    """Cancels working order."""
    data = cancel_order(order_id=order_id, confirm=confirm)
    return json.dumps(data, indent=2)


@app.tool(
    name="get_open_orders",
    description="Retrieve all working, pending, and partially filled orders currently open on the account."
)
def tool_open_orders() -> str:
    """Retrieves active orders list."""
    data = get_open_orders()
    return json.dumps(data, indent=2)


# ------------------------------------------------------------------------------
# 2. MCP Resources Registration
# ------------------------------------------------------------------------------

@app.resource("ibkr://account/summary")
def resource_account_summary() -> str:
    """Direct resource link to current account equity state."""
    return json.dumps(get_account_summary(), indent=2)


@app.resource("ibkr://portfolio/positions")
def resource_portfolio_positions() -> str:
    """Direct resource link to active portfolio holdings."""
    return json.dumps(list_portfolio_positions(), indent=2)


@app.resource("ibkr://system/diagnostics")
def resource_diagnostics() -> str:
    """Direct resource link to socket diagnostics."""
    return json.dumps(client_manager.get_health_status(), indent=2)


# ------------------------------------------------------------------------------
# 3. MCP Prompts Registration
# ------------------------------------------------------------------------------

@app.prompt(name="portfolio_risk_review")
def prompt_portfolio_risk() -> str:
    """Guidance prompt for LLM evaluating portfolio risk."""
    return get_portfolio_risk_prompt()


@app.prompt(name="trade_idea_evaluation")
def prompt_trade_idea(symbol: str, action: str) -> str:
    """Guidance prompt for evaluating a prospective trade idea."""
    return get_trade_idea_prompt(symbol=symbol, proposed_action=action)


@app.prompt(name="premarket_briefing")
def prompt_premarket_briefing() -> str:
    """Premarket daily briefing prompt template."""
    return get_premarket_briefing_prompt()


# ------------------------------------------------------------------------------
# Server Entrypoint
# ------------------------------------------------------------------------------

def main():
    logger.info("Initializing Interactive Brokers MCP Server (v1.0.0)...")
    logger.info(f"Configuration: Host={settings.host}, Port={settings.port}, ReadOnly={settings.read_only}")
    
    # Try connecting to TWS/Gateway
    connected = client_manager.connect()
    if connected:
        logger.info(f"Socket successfully established with TWS at port {settings.port}.")
    else:
        logger.warning(
            f"TWS socket at {settings.host}:{settings.port} is offline or unreachable. "
            f"Operating in SIMULATION mode with realistic market data."
        )

    # Run MCP server on specified transport
    logger.info(f"Starting MCP transport: {settings.transport}...")
    if settings.transport.lower() == "sse":
        app.run(transport="sse", host=settings.sse_host, port=settings.sse_port)
    else:
        app.run(transport="stdio")


if __name__ == "__main__":
    main()
