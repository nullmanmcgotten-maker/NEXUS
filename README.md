# NEXUS live trading engine

This repository is a live-data-first engine for Binance Futures. It does not include demo mode, paper trading, or placeholder simulation flows.

What is included:
- Binance Futures REST adapter for market data and account access
- risk governor with risk caps and kill switches
- execution manager with strict live-order gating
- engine loop that validates connectivity and approves or rejects a trade
- environment-driven configuration

Important:
- live trading is disabled by default
- you must supply Binance API keys and explicit environment flags
- production execution requires exchange permissions, position sizing controls, and final validation

## Required env vars

```bash
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"
export NEXUS_SYMBOL="BTCUSDT"
export NEXUS_ACCOUNT_CAPITAL="10000"
export NEXUS_MAX_RISK_PER_TRADE="0.004"
export NEXUS_ENABLE_LIVE_ORDERS="false"
export BINANCE_TESTNET="false"
```

## Run the live engine

```bash
python live_main.py
```

This does not place orders unless `NEXUS_ENABLE_LIVE_ORDERS=true` and the credentials are valid.
