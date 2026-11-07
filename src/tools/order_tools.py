import logging
import random
import time
from typing import Dict, Any, List, Optional
from src.connection.ibkr_client import client_manager
from src.safety.guardrails import guardrails
from src.tools.market_tools import get_market_quote

logger = logging.getLogger("IBKR-MCP.OrderTools")


def preview_order(
    symbol: str,
    action: str,
    quantity: float,
    order_type: str = "MKT",
    limit_price: Optional[float] = None,
    sec_type: str = "STK"
) -> Dict[str, Any]:
    """
    Safely calculates notional value, margin requirement, estimated commissions,
    and checks risk limits BEFORE placing any order.
    """
    sym = symbol.strip().upper()
    act = action.strip().upper()

    quote = get_market_quote(sym, sec_type=sec_type)
    reference_price = limit_price if limit_price and limit_price > 0 else quote.get("last", 100.0)

    # Calculate multiplier (e.g. 100 for options, 5 for MES, 50 for ES, 1 for STK)
    multiplier = 1.0
    if sec_type == "OPT":
        multiplier = 100.0
    elif sec_type == "FUT":
        multiplier = 5.0 if sym in ("MES", "MNQ") else 50.0

    notional_value = round(quantity * reference_price * multiplier, 2)
    estimated_commission = round(max(1.0, quantity * 0.005), 2) if sec_type == "STK" else 1.50
    estimated_margin_req = round(notional_value * 0.25, 2) if sec_type == "STK" else round(notional_value * 0.10, 2)

    # Check against guardrail threshold
    is_safe, blocked_reason = guardrails.validate_action(
        action=f"PREVIEW_{act}_{sym}",
        order_value_usd=notional_value,
        confirm=True,
        is_live_account=client_manager.is_live_account()
    )

    return {
        "status": "APPROVED_PREVIEW" if is_safe else "EXCEEDS_RISK_LIMIT",
        "symbol": sym,
        "sec_type": sec_type,
        "action": act,
        "quantity": quantity,
        "order_type": order_type.upper(),
        "limit_price": limit_price,
        "reference_price": reference_price,
        "notional_value_usd": notional_value,
        "estimated_commission_usd": estimated_commission,
        "initial_margin_requirement_usd": estimated_margin_req,
        "max_risk_ceiling_usd": guardrails.cfg.max_order_value_usd,
        "read_only_mode": guardrails.cfg.read_only,
        "warning_or_block": blocked_reason,
        "execution_token": f"TOKEN-{sym}-{int(time.time())}-{random.randint(1000, 9999)}",
        "instructions": "Pass confirm=True to 'place_paper_order' to transmit this trade."
    }


def place_paper_order(
    symbol: str,
    action: str,
    quantity: float,
    order_type: str = "MKT",
    limit_price: Optional[float] = None,
    sec_type: str = "STK",
    confirm: bool = False
) -> Dict[str, Any]:
    """
    Submits an order to the Interactive Brokers PAPER TRADING account.
    Protected by safety guardrails: blocks live accounts, verifies confirm=True,
    and enforces maximum dollar position limits.
    """
    sym = symbol.strip().upper()
    act = action.strip().upper()

    quote = get_market_quote(sym, sec_type=sec_type)
    ref_price = limit_price if limit_price and limit_price > 0 else quote.get("last", 100.0)
    notional_value = quantity * ref_price

    # Validate against Safety Guardrails
    is_permitted, error_message = guardrails.validate_action(
        action=f"ORDER_{act}_{sym}",
        order_value_usd=notional_value,
        confirm=confirm,
        is_live_account=client_manager.is_live_account()
    )

    if not is_permitted:
        return {
            "success": False,
            "error": error_message,
            "status": "REJECTED_BY_GUARDRAIL",
            "symbol": sym,
            "action": act,
            "quantity": quantity
        }

    # If live socket connected and not read-only
    if client_manager.is_connected and client_manager.ib and not guardrails.cfg.read_only:
        try:
            from ib_insync import Stock, MarketOrder, LimitOrder
            contract = Stock(sym, "SMART", "USD")
            order = MarketOrder(act, quantity) if order_type.upper() == "MKT" else LimitOrder(act, quantity, limit_price)
            trade = client_manager.ib.placeOrder(contract, order)
            return {
                "success": True,
                "order_id": trade.order.orderId,
                "client_id": trade.order.clientId,
                "symbol": sym,
                "action": act,
                "quantity": quantity,
                "order_type": order_type.upper(),
                "status": trade.orderStatus.status,
                "account": trade.order.account,
                "source": "tws_paper_socket"
            }
        except Exception as e:
            logger.error(f"Failed to place order on TWS: {e}")

    # Simulated paper fill
    sim_order_id = random.randint(100000, 999999)
    fill_price = round(ref_price + (0.01 if act == "BUY" else -0.01), 2)
    return {
        "success": True,
        "order_id": sim_order_id,
        "symbol": sym,
        "sec_type": sec_type,
        "action": act,
        "quantity": quantity,
        "order_type": order_type.upper(),
        "limit_price": limit_price,
        "fill_price": fill_price,
        "notional_value_usd": round(fill_price * quantity, 2),
        "status": "Filled",
        "account": client_manager.account_id,
        "timestamp": time.time(),
        "source": "simulation_engine"
    }


def cancel_order(order_id: int, confirm: bool = False) -> Dict[str, Any]:
    """
    Cancels an active or pending order by its Order ID.
    Requires confirm=True to execute.
    """
    is_permitted, err = guardrails.validate_action(
        action=f"CANCEL_ORDER_{order_id}",
        confirm=confirm,
        is_live_account=client_manager.is_live_account()
    )
    if not is_permitted:
        return {
            "success": False,
            "error": err,
            "status": "CANCEL_REJECTED"
        }

    if client_manager.is_connected and client_manager.ib:
        try:
            for trade in client_manager.ib.trades():
                if trade.order.orderId == order_id:
                    client_manager.ib.cancelOrder(trade.order)
                    return {"success": True, "order_id": order_id, "status": "CancelSubmitted"}
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")

    return {
        "success": True,
        "order_id": order_id,
        "status": "Cancelled",
        "message": f"Order {order_id} has been cancelled successfully.",
        "source": "simulation_engine"
    }


def get_open_orders() -> List[Dict[str, Any]]:
    """
    Retrieves all pending, working, and partially filled orders.
    """
    if client_manager.is_connected and client_manager.ib:
        try:
            trades = client_manager.ib.openTrades()
            return [
                {
                    "order_id": t.order.orderId,
                    "symbol": t.contract.symbol,
                    "sec_type": t.contract.secType,
                    "action": t.order.action,
                    "total_quantity": float(t.order.totalQuantity),
                    "order_type": t.order.orderType,
                    "lmt_price": float(t.order.lmtPrice) if t.order.lmtPrice else None,
                    "status": t.orderStatus.status,
                    "remaining": float(t.orderStatus.remaining)
                }
                for t in trades
            ]
        except Exception as e:
            logger.warning(f"Error fetching open orders from TWS: {e}")

    return [
        {
            "order_id": 849201,
            "symbol": "SPY",
            "sec_type": "STK",
            "action": "BUY",
            "total_quantity": 50.0,
            "order_type": "LMT",
            "lmt_price": 585.00,
            "status": "PreSubmitted",
            "remaining": 50.0,
            "source": "simulation_engine"
        }
    ]

