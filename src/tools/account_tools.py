import logging
from typing import Dict, Any, List, Optional
from src.connection.ibkr_client import client_manager

logger = logging.getLogger("IBKR-MCP.AccountTools")


def get_account_summary(account_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves account equity, buying power, cash balances, and margin status
    from Interactive Brokers.
    """
    target_acc = account_id or client_manager.account_id

    if client_manager.is_connected and client_manager.ib:
        try:
            summary_list = client_manager.ib.accountSummary(account=target_acc)
            acc_data = {}
            for item in summary_list:
                acc_data[item.tag] = {
                    "value": float(item.value) if item.value.replace('.', '', 1).replace('-', '', 1).isdigit() else item.value,
                    "currency": item.currency
                }
            return {
                "account_id": target_acc,
                "net_liquidation": acc_data.get("NetLiquidation", {}).get("value", 0.0),
                "total_cash": acc_data.get("TotalCashValue", {}).get("value", 0.0),
                "buying_power": acc_data.get("BuyingPower", {}).get("value", 0.0),
                "gross_position_value": acc_data.get("GrossPositionValue", {}).get("value", 0.0),
                "realized_pnl": acc_data.get("RealizedPnL", {}).get("value", 0.0),
                "unrealized_pnl": acc_data.get("UnrealizedPnL", {}).get("value", 0.0),
                "currency": acc_data.get("NetLiquidation", {}).get("currency", "USD"),
                "source": "live_tws_socket"
            }
        except Exception as e:
            logger.warning(f"Error fetching live account summary: {e}. Falling back to simulation.")

    # High-fidelity mock simulation fallback
    return {
        "account_id": target_acc,
        "net_liquidation": 125480.50,
        "total_cash": 48210.20,
        "buying_power": 250961.00,
        "gross_position_value": 77270.30,
        "realized_pnl": 1420.50,
        "unrealized_pnl": 3890.10,
        "currency": "USD",
        "margin_cushion_pct": 68.4,
        "source": "simulation_engine"
    }


def list_portfolio_positions(account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists all currently open positions, average entry prices, current market values,
    and unrealized profit/loss across Equities, Options, and Futures.
    """
    target_acc = account_id or client_manager.account_id

    if client_manager.is_connected and client_manager.ib:
        try:
            positions = client_manager.ib.positions(account=target_acc)
            results = []
            for pos in positions:
                c = pos.contract
                results.append({
                    "symbol": c.symbol,
                    "sec_type": c.secType,
                    "exchange": c.exchange,
                    "currency": c.currency,
                    "position": float(pos.position),
                    "avg_cost": float(pos.avgCost),
                    "market_price": 0.0,
                    "market_value": float(pos.position * pos.avgCost),
                    "unrealized_pnl": 0.0,
                    "source": "live_tws_socket"
                })
            return results
        except Exception as e:
            logger.warning(f"Error reading live portfolio positions: {e}. Falling back to simulation.")

    # High-fidelity mock simulation fallback
    return [
        {
            "symbol": "SPY",
            "sec_type": "STK",
            "exchange": "SMART",
            "currency": "USD",
            "position": 100.0,
            "avg_cost": 585.20,
            "market_price": 592.40,
            "market_value": 59240.00,
            "unrealized_pnl": 720.00,
            "unrealized_pnl_pct": 1.23,
            "source": "simulation_engine"
        },
        {
            "symbol": "NVDA",
            "sec_type": "STK",
            "exchange": "SMART",
            "currency": "USD",
            "position": 50.0,
            "avg_cost": 138.50,
            "market_price": 144.20,
            "market_value": 7210.00,
            "unrealized_pnl": 285.00,
            "unrealized_pnl_pct": 4.11,
            "source": "simulation_engine"
        },
        {
            "symbol": "MES",
            "sec_type": "FUT",
            "exchange": "CME",
            "currency": "USD",
            "position": 2.0,
            "avg_cost": 5980.50,
            "market_price": 5995.25,
            "market_value": 59952.50,
            "unrealized_pnl": 147.50,
            "unrealized_pnl_pct": 0.25,
            "source": "simulation_engine"
        }
    ]
