from typing import Dict, Any


def get_portfolio_risk_prompt() -> str:
    """Prompt template for LLM quantitative portfolio risk evaluation."""
    return """
You are a senior Quantitative Risk Officer evaluating the Interactive Brokers portfolio.
Review the following account data and positions:
1. Identify any single-position concentration exceeding 25% of net liquidation.
2. Evaluate buying power utilization and margin cushion margin of safety.
3. Assess exposure across asset classes (Equities vs Options vs Futures).
4. Provide 3 concrete risk-mitigation recommendations before market open.
"""


def get_trade_idea_prompt(symbol: str, proposed_action: str) -> str:
    """Prompt template for assessing a specific prospective trade."""
    return f"""
You are an algorithmic execution strategist evaluating a proposed {proposed_action} on {symbol}.
Using the IBKR-MCP tools:
1. Query get_market_quote for {symbol} to inspect current spread, VWAP, and volume.
2. If options, inspect get_options_chain_snapshot to assess IV rank and Delta/Theta decay.
3. Run preview_order to confirm notional value, margin requirement, and safety limits.
4. Issue a formal GO / NO-GO recommendation with stop-loss and profit-target levels.
"""


def get_premarket_briefing_prompt() -> str:
    """Prompt template for daily premarket overview."""
    return """
Generate an institutional premarket intelligence briefing for today's trading session:
1. Review ES / MES futures levels and VWAP deviation.
2. Review SPY and QQQ expected opening ranges and volatility indices.
3. Check open orders and existing portfolio positions for any overnight risk gap.
"""
