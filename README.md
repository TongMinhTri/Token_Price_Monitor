# 🪙 Token Price Monitor

A Python-based monitoring tool that tracks token prices from BSC (or other EVM chains) in real-time or over historical blocks. It supports both PancakeSwap V2 and V3-style pools, stores data in MongoDB, and exports metrics to Prometheus.

---

## 📦 Features

- ⛓️ Supports both Uniswap V2 and V3-style pools
- 🕒 Monitor live blocks or historical block ranges
- 📊 Export real-time token prices and deviation metrics to Prometheus
- 🧠 Automatic symbol detection using token contract
- 💾 Store token prices and block timestamps in MongoDB

---

## 🧱 Project Structure

```
src/
├── price_monitor/         # Core monitoring logic
│   ├── abis.py
│   ├── block_processor.py
│   ├── monitor.py
│   ├── price_calculator.py
│   ├── prometheus_exporter.py
│   └── token_utils.py
├── db/
│   └── mongo.py
├── config.py              # Loads config.json
├── logger.py              # Logger setup
├── main.py                # CLI entry point
```

---

## ⚙️ Configuration

Edit `src/config.json`:

```json
{
  "mongo_url": "mongodb://localhost:27017",
  "database_name": "price_monitor",
  "collection_name": "token_prices",
  "rpc_url": "https://bsc-dataseed.binance.org",
  "stable_coins": ["USDT", "USDC", "BUSD"],
  "token_pairs": {
    "WBNB-USDT-V2": {
      "pool_address": "0x...",
      "pool_type": "v2"
    },
    "WBNB-USDT-V3": {
      "pool_address": "0x...",
      "pool_type": "v3"
    }
  }
}
```

---

## 🚀 Usage

Install dependencies:

```bash
poetry install
```

Run the price monitor:

```bash
poetry run python src/main.py --pair WBNB-USDT-V2 WBNB-USDT-V3 --from_block 12345678 --to_block 12345678
```

Optional arguments:
- `--to_block`: Stop after reaching this block
- `--from_block`: Start from this block (default: latest)

---

## 📡 Prometheus Metrics

Metrics are served on `http://localhost:8000`:

- `token_price{pair_name="WBNB-USDT-V2"}`
- `price_deviation_pct{pair="WBNB-USDT-V2_WBNB-USDT_V3"}`

---

## 🐳 Docker

You can start Prometheus, MongoDB, and this monitor using Docker Compose:

```bash
docker-compose up
```

Make sure `prometheus.yml` is properly configured to scrape port 8000.

---

## 🧪 Testing

_Coming soon..._

---

## 📄 License

MIT License
