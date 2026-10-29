# 🚀 CryptoPriceList

A self-updating cryptocurrency price table for your GitHub README. A scheduled GitHub Action fetches prices and 24-hour changes from CoinGecko, regenerates the table, and commits it back to the repository — no server and no API key.

## Features

- 🤖 **Automated Updates**: Refreshed hourly via GitHub Actions (best effort; GitHub may delay scheduled runs)
- 📊 **Readable Table**: USD prices, 24h changes, and consistent trend/status labels
- 📈 **Clear Signals**: Emoji and status indicators derived from one set of thresholds
- 🔧 **Customizable**: Change the tracked coins in `update_prices.py`
- 🛡️ **Failure-Safe**: Network timeouts, retries, tests before writing, and failed runs leave the README untouched
- 💻 **README Display**: Prices shown directly in this repository's README
- 🆓 **Free to Use**: No API keys required, runs entirely on GitHub
- 🧪 **Tested**: Offline unit tests run on every push and pull request

## Tracked Cryptocurrencies

- Bitcoin (BTC)
- Ethereum (ETH)
- Litecoin (LTC)
- Solana (SOL)
- Cardano (ADA)

<!-- PRICE_TABLE_START -->

<div align="center">

### 💰 Live Cryptocurrency Prices

<table>
<thead>
<tr>
<th align="left">🪙 Cryptocurrency</th>
<th align="right">💵 Price (USD)</th>
<th align="right">📊 24h Change</th>
<th align="center">📈 Trend</th>
<th align="center">🎯 Status</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Bitcoin</strong></td>
<td align="right"><code>$79,913</code></td>
<td align="right"><strong>-1.21%</strong></td>
<td align="center">📉</td>
<td align="center">DOWN</td>
</tr>
<tr>
<td><strong>Ethereum</strong></td>
<td align="right"><code>$2,308</code></td>
<td align="right"><strong>-2.09%</strong></td>
<td align="center">📉</td>
<td align="center">DOWN</td>
</tr>
<tr>
<td><strong>Litecoin</strong></td>
<td align="right"><code>$58.35</code></td>
<td align="right"><strong>+1.79%</strong></td>
<td align="center">📈</td>
<td align="center">UP</td>
</tr>
<tr>
<td><strong>Solana</strong></td>
<td align="right"><code>$99.75</code></td>
<td align="right"><strong>-1.85%</strong></td>
<td align="center">📉</td>
<td align="center">DOWN</td>
</tr>
<tr>
<td><strong>Cardano</strong></td>
<td align="right"><code>$0.1976</code></td>
<td align="right"><strong>-4.42%</strong></td>
<td align="center">📉</td>
<td align="center">DOWN</td>
</tr>
</tbody>
</table>

---

**📊 Market Summary:** 5/5 coins tracked | **📈 Avg 24h Change:** -1.56%  
**🕐 Data as of:** 2026-10-29 02:24 UTC | **🔄 Refreshed hourly (best effort)**  
**🤖 Last checked:** 2026-10-29 02:24 UTC

*Data provided by [CoinGecko API](https://www.coingecko.com/en/api) 🦎*

</div>

<!-- PRICE_TABLE_END -->

## 🚀 Quick Start - Fork This Repository

### Step 1: Fork the Repository

1. **Click the "Fork" button** at the top right of this repository
2. **Choose your GitHub account** as the destination
3. **Wait for the fork to complete** - you now have your own copy!

### Step 2: Enable GitHub Actions (IMPORTANT!)

⚠️ **This step is crucial for automatic price updates**

1. Go to **your forked repository** (not this one)
2. Click on the **"Actions" tab**
3. Click **"I understand my workflows, go ahead and enable them"**
4. The workflow is scheduled hourly; you can also run it manually at any time

### Step 3: Verify It's Working

1. Go to the **"Actions" tab** in your fork
2. You should see the **"Update Crypto Prices"** workflow
3. Click on a completed workflow run to view the logs
4. Scheduled runs are best-effort; if no run has happened yet, use **Run workflow** to trigger one

### Step 4: Customize Your Tracker (Optional)

**Want to track different cryptocurrencies?**

1. Edit the `update_prices.py` file in your fork
2. Find the `COIN_IDS` list near the top of the file
3. Replace with your preferred coins from [CoinGecko's list](https://api.coingecko.com/api/v3/coins/list)
4. Save and commit - GitHub Actions will handle the rest!

**Example customization:**

```python
COIN_IDS = ['bitcoin', 'ethereum', 'dogecoin', 'chainlink', 'polygon']
```

### Step 5: Manual Monitoring (Optional)

**Want to update prices immediately?**

1. Go to **Actions** → **"Update Crypto Prices"**
2. Click **"Run workflow"** → **"Run workflow"**
3. Wait for completion - your README will be updated with fresh prices!

---

## 🛠️ Troubleshooting

**Workflow not running?**

- Check that GitHub Actions are enabled for the repository
- Scheduled workflows are best-effort; GitHub may delay or skip runs under load. Trigger a run manually from the Actions tab if needed
- Open the latest run and check which step failed

**Workflow failing?**

- A failed CoinGecko request, a missing marker, or a failed test intentionally fails the run and leaves the README unchanged
- Re-run the workflow from the Actions tab; transient API failures are retried automatically
- If CoinGecko is rate-limiting the runner, wait and retry

**Table not changing?**

- The workflow commits only when the generated table changes. Prices can be unchanged, or the run may have failed
- Check the run logs for the generated table and timestamps

**Want to add more coins?**

- Use exact coin IDs from [CoinGecko API](https://api.coingecko.com/api/v3/coins/list)
- Keep the format: `['coin1', 'coin2', 'coin3']`

## How It Works

1. **GitHub Actions Workflow**: Runs hourly on a best-effort schedule and can be triggered manually
2. **API Call**: Fetches prices, 24h changes, and the last-updated timestamp from CoinGecko, with timeouts and retries
3. **Validation**: Checks the response and renders the table; missing coins are shown as `N/A` instead of crashing
4. **README Update**: Replaces only the content between the price-table markers
5. **Commit**: Runs the test suite, then commits `README.md` only when the table changed
6. **Failure Handling**: A failed fetch or invalid markers exits nonzero, so the Actions run shows as failed

## Requirements

- No API keys needed
- No local setup required for GitHub-hosted updates
- Python 3.12 (used by GitHub Actions)

## 💻 Local Development

**Want to run this locally or contribute?**

```bash
# Clone your forked repository
git clone https://github.com/yourusername/CryptoPriceList.git
cd CryptoPriceList

# Install runtime and test dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run the tests
pytest -q

# Fetch live prices and update README.md
python update_prices.py
```

**For development:**

- The script prints prices to the terminal and updates `README.md` in place; review changes with `git diff`
- Run `pytest -q` before pushing; the same tests run in the update workflow
- A failed CoinGecko request exits 1; invalid README markers exit 2

## 📁 File Structure

```
CryptoPriceList/
├── .github/
│   └── workflows/
│       ├── update_prices.yml    # 🤖 Hourly price update
│       └── tests.yml            # 🧪 Offline test suite
├── tests/
│   └── test_update_prices.py    # Fetcher, renderer, and README tests
├── update_prices.py             # 🐍 Price tracker script
├── requirements.txt             # 📦 Runtime dependencies
├── requirements-dev.txt         # 📦 Test dependencies
├── pyproject.toml               # ⚙️ Pytest configuration
├── README.md                    # 📖 Documentation with live price table
└── LICENSE                      # ⚖️ MIT License
```

**Key Files:**

- `update_prices.py` - Fetches prices, validates data, renders the table, and updates README
- `tests/test_update_prices.py` - Offline tests for formatting, fetching, retries, and README updates
- `.github/workflows/update_prices.yml` - Hourly price updates and commits
- `.github/workflows/tests.yml` - Runs the tests on pushes and pull requests
- `requirements.txt` / `requirements-dev.txt` - Runtime and test dependencies

## Limitations

- Scheduled workflows are best-effort. GitHub can delay or skip runs, so "hourly" is a target, not a guarantee.
- Prices come from CoinGecko's public API and can be delayed. They are for informational purposes only, not financial advice.
- The workflow commits at most once per run; an unchanged table produces no commit.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [CoinGecko API](https://www.coingecko.com/en/api) for providing free cryptocurrency data
- GitHub Actions for free automation

---
