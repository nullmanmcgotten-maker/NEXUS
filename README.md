# NEXUS live trading engine

NEXUS now includes the authenticated account, risk-gate, order-lifecycle, journal, and Telegram paths.

## Added live components

- `account_validator.py`: signed Binance account validation and trade-permission checks.
- `live/binance_futures.py`: signed REST requests using the required `X-MBX-APIKEY` header.
- `live_models.py`: explicit account, risk-gate, execution-gate, and order-state models.
- `risk_governor.py`: daily loss, per-trade risk, open-position, and reward/risk gates.
- `order_lifecycle.py`: account validation → risk gate → journal → Telegram approval → live order → lifecycle update.
- `journal.py`: SQLite order journal for restart-safe lifecycle tracking.
- `telegram_notifier.py`: live approval and lifecycle notifications.

## Environment

```bash
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"
export BINANCE_TESTNET="false"
export NEXUS_SYMBOL="BTCUSDT"
export NEXUS_ACCOUNT_CAPITAL="10000"
export NEXUS_MAX_RISK_PER_TRADE="0.004"
export NEXUS_MAX_DAILY_LOSS="0.02"
export NEXUS_MAX_OPEN_POSITIONS="3"
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export NEXUS_ENABLE_LIVE_ORDERS="false"
```

## Account validation

```bash
python account_check.py
```

The command performs a signed account request. It does not place an order.

## Operational order lifecycle

`execute_entry()` will:

1. Validate the signed Binance account response.
2. Apply the risk gate.
3. Create a durable SQLite order record.
4. Send a Telegram approval event.
5. Submit a Binance MARKET order only when live orders are explicitly enabled.
6. Persist the exchange response or an `UNKNOWN` state for reconciliation.

Never expose API secrets in Telegram, source control, logs, or issue comments. Use a Binance key restricted to Futures trading and IP allowlisting; do not enable withdrawals.
