import logging
from typing import Tuple, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger("IBKR-MCP.Safety")


class SafetyGuardrails:
    """Enforces institutional safety controls and human-in-the-loop validation."""

    def __init__(self, cfg=settings):
        self.cfg = cfg

    def validate_action(
        self,
        action: str,
        order_value_usd: float = 0.0,
        confirm: bool = False,
        is_live_account: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a mutating action (place order, cancel order, modify) is permitted.
        Returns: (is_allowed: bool, reason_if_blocked: str | None)
        """
        # 1. Read-Only check (previews are non-mutating and permitted in read-only mode)
        if self.cfg.read_only and not action.startswith("PREVIEW"):
            msg = (
                f"🛡️ SAFETY INTERCEPT: Cannot execute action '{action}'. "
                f"IBKR-MCP server is currently configured in READ-ONLY mode. "
                f"To enable paper executions, set IBKR_READ_ONLY=false in .env."
            )
            logger.warning(msg)
            return False, msg

        # 2. Live trading prohibition
        if is_live_account and not self.cfg.allow_live_trading:
            msg = (
                f"🛑 LIVE TRADING BLOCKED: Action '{action}' was routed to a LIVE Interactive Brokers account "
                f"or live port ({self.cfg.port}), but ALLOW_LIVE_TRADING is set to false. "
                f"Live autonomous execution is disabled by default to protect capital."
            )
            logger.error(msg)
            return False, msg

        # 3. Explicit human-in-the-loop confirmation requirement
        if self.cfg.require_explicit_confirm and not confirm:
            msg = (
                f"⚠️ HUMAN CONFIRMATION REQUIRED: Execution '{action}' requires explicit confirmation. "
                f"Please preview the order first using 'preview_order', then provide 'confirm=True' to execute."
            )
            logger.info(msg)
            return False, msg

        # 4. Maximum order value threshold
        if order_value_usd > self.cfg.max_order_value_usd:
            msg = (
                f"🚨 RISK LIMIT EXCEEDED: Calculated order value (${order_value_usd:,.2f}) "
                f"exceeds single-order threshold (${self.cfg.max_order_value_usd:,.2f}). "
                f"Reduce order size or update MAX_ORDER_VALUE_USD in configuration."
            )
            logger.warning(msg)
            return False, msg

        return True, None


guardrails = SafetyGuardrails()
