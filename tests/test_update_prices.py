from datetime import datetime, timedelta, timezone

import pytest
import requests

import update_prices as prices


NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)
UPDATED_AT = int((NOW - timedelta(seconds=90)).timestamp())


def sample_prices():
    return {
        "bitcoin": {
            "usd": 80723,
            "usd_24h_change": 1.0,
            "last_updated_at": UPDATED_AT,
        },
        "ethereum": {
            "usd": 2355.82,
            "usd_24h_change": 2.0,
            "last_updated_at": UPDATED_AT,
        },
        "litecoin": {
            "usd": 57.03,
            "usd_24h_change": None,
            "last_updated_at": UPDATED_AT,
        },
        "solana": {
            "usd": 102.25,
            "usd_24h_change": -1.0,
            "last_updated_at": UPDATED_AT,
        },
        "cardano": {
            "usd": 0.2086,
            "usd_24h_change": 0.0,
            "last_updated_at": UPDATED_AT,
        },
    }


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.mark.parametrize(
    ("price", "expected"),
    [
        (0.2086, "$0.2086"),
        (0.9999, "$0.9999"),
        (1, "$1.00"),
        (57.03, "$57.03"),
        (999.99, "$999.99"),
        (1000, "$1,000"),
        (80723, "$80,723"),
        (None, "N/A"),
        (0, "N/A"),
        (-1, "N/A"),
        (float("nan"), "N/A"),
        (True, "N/A"),
    ],
)
def test_format_price(price, expected):
    assert prices.format_price(price) == expected


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (None, ("❔", "NO DATA")),
        (0, ("➖", "FLAT")),
        (0.5, ("➖", "FLAT")),
        (0.51, ("📈", "UP")),
        (4.99, ("📈", "UP")),
        (5, ("🚀", "HOT")),
        (-0.5, ("➖", "FLAT")),
        (-0.51, ("📉", "DOWN")),
        (-5, ("📉", "DOWN")),
        (-5.01, ("💥", "COLD")),
        (float("nan"), ("❔", "NO DATA")),
    ],
)
def test_classify_change(change, expected):
    assert prices.classify_change(change) == expected


def test_render_table_contains_expected_content():
    table = prices.render_table(sample_prices(), prices.COIN_IDS, now=NOW)

    assert "style=" not in table
    assert "color:" not in table
    assert table.count("<tr>") == 6
    for name in ("Bitcoin", "Ethereum", "Litecoin", "Solana", "Cardano"):
        assert f"<strong>{name}</strong>" in table
    assert "<code>$80,723</code>" in table
    assert "<code>$0.2086</code>" in table
    assert "5/5 coins tracked" in table
    assert "+0.50%" in table
    assert "2026-10-26 11:58 UTC" in table
    assert "2026-10-26 12:00 UTC" in table
    assert "Refreshed hourly (best effort)" in table
    assert "FLAT" in table
    assert "NO DATA" in table
    assert "<strong>n/a</strong>" in table


def test_render_table_handles_missing_coins():
    table = prices.render_table(
        {"bitcoin": sample_prices()["bitcoin"]},
        prices.COIN_IDS,
        now=NOW,
    )

    assert table.count("<code>N/A</code>") == 4
    assert table.count("NO DATA") == 4
    assert "1/5 coins tracked" in table
    assert "+1.00%" in table


def test_render_table_falls_back_to_check_time_without_api_timestamp():
    payload = {coin: {"usd": data["usd"]} for coin, data in sample_prices().items()}
    table = prices.render_table(payload, prices.COIN_IDS, now=NOW)

    assert "Data as of:** 2026-10-26 12:00 UTC" in table


def test_splice_readme_replaces_only_the_table():
    content = (
        "before\n"
        f"{prices.START_MARKER}\n"
        "old table\n"
        f"{prices.END_MARKER}\n"
        "after\n"
    )
    result = prices.splice_readme(content, "<table>new</table>")

    expected = (
        "before\n"
        f"{prices.START_MARKER}\n\n"
        "<table>new</table>\n\n"
        f"{prices.END_MARKER}\n"
        "after\n"
    )
    assert result == expected
    assert prices.splice_readme(result, "<table>new</table>") == result


@pytest.mark.parametrize(
    "content",
    [
        "no markers",
        f"{prices.START_MARKER}\nonly start",
        f"only end\n{prices.END_MARKER}",
        f"{prices.START_MARKER}\n{prices.START_MARKER}\n{prices.END_MARKER}",
        f"{prices.END_MARKER}\n{prices.START_MARKER}",
    ],
)
def test_splice_readme_rejects_invalid_markers(content):
    with pytest.raises(prices.ReadmeUpdateError):
        prices.splice_readme(content, "<table>new</table>")


def test_update_readme_writes_once_and_is_idempotent(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        f"before\n{prices.START_MARKER}\nold\n{prices.END_MARKER}\nafter\n",
        encoding="utf-8",
    )

    assert prices.update_readme("<table>new</table>", path=readme) is True
    assert "<table>new</table>" in readme.read_text(encoding="utf-8")
    assert prices.update_readme("<table>new</table>", path=readme) is False
    assert not list(tmp_path.glob(".README.md.*"))


def test_update_readme_missing_file(tmp_path):
    with pytest.raises(prices.ReadmeUpdateError):
        prices.update_readme("<table>new</table>", path=tmp_path / "missing.md")


def test_update_readme_missing_markers(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("no markers", encoding="utf-8")

    with pytest.raises(prices.ReadmeUpdateError):
        prices.update_readme("<table>new</table>", path=readme)


def test_fetch_prices_success():
    payload = {"bitcoin": {"usd": 80723, "usd_24h_change": 0.05}}
    session = FakeSession([FakeResponse(200, payload)])

    result = prices.fetch_prices(["bitcoin"], session=session)

    assert result == payload
    url, kwargs = session.calls[0]
    assert url == prices.API_URL
    assert kwargs["params"]["ids"] == "bitcoin"
    assert kwargs["params"]["include_24hr_change"] == "true"
    assert kwargs["params"]["include_last_updated_at"] == "true"
    assert kwargs["headers"] == {"User-Agent": prices.USER_AGENT}
    assert kwargs["timeout"] == prices.HTTP_TIMEOUT


def test_fetch_prices_retries_429(monkeypatch):
    payload = {"bitcoin": {"usd": 80723}}
    session = FakeSession(
        [
            FakeResponse(429, headers={"Retry-After": "0"}),
            FakeResponse(200, payload),
        ]
    )
    sleeps = []
    monkeypatch.setattr(prices.time, "sleep", sleeps.append)

    assert prices.fetch_prices(["bitcoin"], session=session) == payload
    assert len(session.calls) == 2
    assert sleeps == [0]


def test_fetch_prices_retries_500_then_fails(monkeypatch):
    session = FakeSession([FakeResponse(500), FakeResponse(500), FakeResponse(500)])
    sleeps = []
    monkeypatch.setattr(prices.time, "sleep", sleeps.append)

    with pytest.raises(prices.PriceFetchError):
        prices.fetch_prices(["bitcoin"], session=session)

    assert len(session.calls) == 3
    assert sleeps == [1, 2]


def test_fetch_prices_does_not_retry_404(monkeypatch):
    session = FakeSession([FakeResponse(404, text="not found")])
    monkeypatch.setattr(prices.time, "sleep", lambda seconds: None)

    with pytest.raises(prices.PriceFetchError):
        prices.fetch_prices(["bitcoin"], session=session)

    assert len(session.calls) == 1


def test_fetch_prices_rejects_response_without_prices(monkeypatch):
    session = FakeSession(
        [
            FakeResponse(200, {"bitcoin": {"usd": None}}),
            FakeResponse(200, {"bitcoin": {"usd": None}}),
            FakeResponse(200, {"bitcoin": {"usd": None}}),
        ]
    )
    monkeypatch.setattr(prices.time, "sleep", lambda seconds: None)

    with pytest.raises(prices.PriceFetchError):
        prices.fetch_prices(["bitcoin"], session=session)


def test_fetch_prices_retries_invalid_json(monkeypatch):
    session = FakeSession(
        [
            FakeResponse(200, ValueError("bad json")),
            FakeResponse(200, ValueError("bad json")),
            FakeResponse(200, ValueError("bad json")),
        ]
    )
    monkeypatch.setattr(prices.time, "sleep", lambda seconds: None)

    with pytest.raises(prices.PriceFetchError):
        prices.fetch_prices(["bitcoin"], session=session)


def test_main_success(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text(
        f"before\n{prices.START_MARKER}\nold\n{prices.END_MARKER}\nafter\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(prices, "README_PATH", readme)
    monkeypatch.setattr(prices, "fetch_prices", lambda coin_ids: sample_prices())
    monkeypatch.setattr(prices, "display_prices", lambda *args, **kwargs: None)

    assert prices.main() == 0
    assert "Live Cryptocurrency Prices" in readme.read_text(encoding="utf-8")


def test_main_fetch_failure(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    original = f"before\n{prices.START_MARKER}\nold\n{prices.END_MARKER}\nafter\n"
    readme.write_text(original, encoding="utf-8")
    monkeypatch.setattr(prices, "README_PATH", readme)

    def fail_fetch(coin_ids, session=None):
        raise prices.PriceFetchError("boom")

    monkeypatch.setattr(prices, "fetch_prices", fail_fetch)

    assert prices.main() == 1
    assert readme.read_text(encoding="utf-8") == original


def test_main_missing_markers(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text("no markers", encoding="utf-8")
    monkeypatch.setattr(prices, "README_PATH", readme)
    monkeypatch.setattr(prices, "fetch_prices", lambda coin_ids: sample_prices())
    monkeypatch.setattr(prices, "display_prices", lambda *args, **kwargs: None)

    assert prices.main() == 2
    assert readme.read_text(encoding="utf-8") == "no markers"
