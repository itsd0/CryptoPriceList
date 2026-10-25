"""Update README.md with cryptocurrency prices from CoinGecko."""

from __future__ import annotations

import html
import math
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

COIN_IDS = ["bitcoin", "ethereum", "litecoin", "solana", "cardano"]
README_PATH = Path(__file__).resolve().parent / "README.md"
START_MARKER = "<!-- PRICE_TABLE_START -->"
END_MARKER = "<!-- PRICE_TABLE_END -->"

API_URL = "https://api.coingecko.com/api/v3/simple/price"
USER_AGENT = "CryptoPriceList/2.0"
HTTP_TIMEOUT = (5, 15)
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 2, 4)


class PriceFetchError(RuntimeError):
    """Raised when CoinGecko data cannot be retrieved."""


class ReadmeUpdateError(RuntimeError):
    """Raised when README.md is missing or its price-table markers are invalid."""


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def fetch_prices(
    coin_ids: list[str], session: requests.Session | None = None
) -> dict[str, dict[str, Any]]:
    """Fetch prices and 24h changes, retrying transient failures."""
    client = session or requests.Session()
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    }

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(
                API_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=HTTP_TIMEOUT,
            )
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(
                    f"HTTP {response.status_code}", response=response
                )
            if 400 <= response.status_code < 500:
                raise PriceFetchError(f"HTTP {response.status_code}")
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("unexpected response shape")
            prices = {
                coin: data
                for coin, data in payload.items()
                if isinstance(data, dict)
            }
            if not any(_is_number(data.get("usd")) for data in prices.values()):
                raise ValueError("response contained no usable prices")
            return prices
        except PriceFetchError:
            raise
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt == MAX_ATTEMPTS:
                break
            delay = BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]
            error_response = getattr(exc, "response", None)
            retry_after = (
                error_response.headers.get("Retry-After")
                if error_response is not None
                else None
            )
            if retry_after and str(retry_after).isdigit():
                delay = min(int(retry_after), 30)
            print(
                f"Fetch attempt {attempt}/{MAX_ATTEMPTS} failed: {exc}; "
                f"retrying in {delay}s",
                file=sys.stderr,
            )
            time.sleep(delay)

    raise PriceFetchError(
        f"could not fetch prices after {MAX_ATTEMPTS} attempts: {last_error}"
    )


def format_price(price: Any) -> str:
    """Format a USD price for display."""
    if not _is_number(price) or price <= 0:
        return "N/A"
    if price >= 1000:
        return f"${price:,.0f}"
    if price >= 1:
        return f"${price:,.2f}"
    return f"${price:.4f}"


def classify_change(change: Any) -> tuple[str, str]:
    """Return the trend emoji and status label for a 24h change."""
    if not _is_number(change):
        return "❔", "NO DATA"
    if change >= 5:
        return "🚀", "HOT"
    if change > 0.5:
        return "📈", "UP"
    if change >= -0.5:
        return "➖", "FLAT"
    if change >= -5:
        return "📉", "DOWN"
    return "💥", "COLD"


def render_table(
    prices: dict[str, dict[str, Any]],
    coin_ids: list[str],
    now: datetime | None = None,
) -> str:
    """Render the price table that is inserted into README.md."""
    now = now or datetime.now(timezone.utc)
    rows: list[str] = []
    changes: list[float] = []
    data_timestamps: list[float] = []
    tracked = 0

    for coin_id in coin_ids:
        data = prices.get(coin_id, {})
        price = data.get("usd")
        change = data.get("usd_24h_change")
        name = html.escape(coin_id.replace("-", " ").title())

        if _is_number(data.get("last_updated_at")):
            data_timestamps.append(float(data["last_updated_at"]))

        if _is_number(price) and price > 0:
            tracked += 1
            if _is_number(change):
                change_text = f"{change:+.2f}%"
                changes.append(float(change))
            else:
                change_text = "n/a"
            emoji, status = classify_change(change)
            rows.append(
                "<tr>\n"
                f"<td><strong>{name}</strong></td>\n"
                f'<td align="right"><code>{format_price(price)}</code></td>\n'
                f'<td align="right"><strong>{change_text}</strong></td>\n'
                f'<td align="center">{emoji}</td>\n'
                f'<td align="center">{status}</td>\n'
                "</tr>"
            )
        else:
            rows.append(
                "<tr>\n"
                f"<td><strong>{name}</strong></td>\n"
                '<td align="right"><code>N/A</code></td>\n'
                '<td align="right">--</td>\n'
                '<td align="center">❔</td>\n'
                '<td align="center">NO DATA</td>\n'
                "</tr>"
            )

    average = f"{sum(changes) / len(changes):+.2f}%" if changes else "n/a"
    data_time = (
        datetime.fromtimestamp(max(data_timestamps), tz=timezone.utc)
        if data_timestamps
        else now
    )
    data_time_text = data_time.strftime("%Y-%m-%d %H:%M UTC")
    checked_time = now.strftime("%Y-%m-%d %H:%M UTC")
    rows_html = "\n".join(rows)

    return f"""<div align="center">

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
{rows_html}
</tbody>
</table>

---

**📊 Market Summary:** {tracked}/{len(coin_ids)} coins tracked | **📈 Avg 24h Change:** {average}  
**🕐 Data as of:** {data_time_text} | **🔄 Refreshed hourly (best effort)**  
**🤖 Last checked:** {checked_time}

*Data provided by [CoinGecko API](https://www.coingecko.com/en/api) 🦎*

</div>"""


def display_prices(
    prices: dict[str, dict[str, Any]],
    coin_ids: list[str],
    now: datetime | None = None,
) -> None:
    """Print the current prices to the console."""
    now = now or datetime.now(timezone.utc)
    print("\n" + "=" * 60)
    print("🚀 CRYPTOCURRENCY PRICE TRACKER 🚀")
    print("=" * 60)

    for coin_id in coin_ids:
        data = prices.get(coin_id, {})
        price = data.get("usd")
        change = data.get("usd_24h_change")
        emoji, _ = classify_change(change)
        change_text = f"({change:+.2f}%)" if _is_number(change) else "(n/a)"
        name = coin_id.replace("-", " ").title()
        print(f"{emoji} {name:<12}: {format_price(price):>12} {change_text}")

    print(f"\n🕐 Last checked: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60 + "\n")


def splice_readme(content: str, table: str) -> str:
    """Replace the content between the price-table markers."""
    if content.count(START_MARKER) != 1 or content.count(END_MARKER) != 1:
        raise ReadmeUpdateError(
            "README must contain exactly one pair of price-table markers"
        )

    start = content.index(START_MARKER) + len(START_MARKER)
    end = content.index(END_MARKER)
    if start >= end:
        raise ReadmeUpdateError("price-table markers are out of order")

    return f"{content[:start]}\n\n{table.strip()}\n\n{content[end:]}"


def _write_text_atomic(path: Path, content: str) -> None:
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", text=True
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        if path.exists():
            os.chmod(tmp_path, path.stat().st_mode & 0o777)
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def update_readme(table: str, path: Path | None = None) -> bool:
    """Write the table to README.md, returning whether the file changed."""
    path = path or README_PATH
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReadmeUpdateError(f"could not read {path}: {exc}") from exc

    updated = splice_readme(content, table)
    if updated == content:
        return False

    try:
        _write_text_atomic(path, updated)
    except OSError as exc:
        raise ReadmeUpdateError(f"could not write {path}: {exc}") from exc
    return True


def main() -> int:
    """Fetch prices and update README.md."""
    try:
        prices = fetch_prices(COIN_IDS)
    except PriceFetchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    table = render_table(prices, COIN_IDS, now=now)
    try:
        changed = update_readme(table)
    except ReadmeUpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    display_prices(prices, COIN_IDS, now=now)
    print("README updated." if changed else "README already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
