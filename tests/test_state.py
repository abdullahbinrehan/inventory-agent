from datetime import datetime, timedelta, timezone

from agent.state import load_state, save_state, should_alert, record_alert


def _iso_hours_ago(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def test_load_state_missing_file_returns_empty(tmp_path):
    missing = tmp_path / "nope.json"
    assert load_state(missing) == {}


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    state = {"SKU-A": {"sku": "SKU-A", "last_alerted_at": _iso_hours_ago(1),
                       "urgency": "HIGH", "alert_count_7d": 1}}
    save_state(state, path)
    loaded = load_state(path)
    assert loaded == state


def test_load_state_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("not json at all")
    assert load_state(path) == {}


# ---------------------------------------------------------------------------
# should_alert
# ---------------------------------------------------------------------------

def test_should_alert_first_time():
    assert should_alert("SKU-A", "HIGH", {}) is True


def test_should_alert_within_window_same_urgency():
    state = {"SKU-A": {"sku": "SKU-A", "last_alerted_at": _iso_hours_ago(2),
                       "urgency": "HIGH", "alert_count_7d": 1}}
    assert should_alert("SKU-A", "HIGH", state) is False


def test_should_alert_after_window():
    state = {"SKU-A": {"sku": "SKU-A", "last_alerted_at": _iso_hours_ago(30),
                       "urgency": "HIGH", "alert_count_7d": 1}}
    assert should_alert("SKU-A", "HIGH", state) is True


def test_should_alert_when_urgency_escalates():
    state = {"SKU-A": {"sku": "SKU-A", "last_alerted_at": _iso_hours_ago(2),
                       "urgency": "NORMAL", "alert_count_7d": 1}}
    assert should_alert("SKU-A", "CRITICAL", state) is True


def test_should_not_alert_when_urgency_deescalates():
    state = {"SKU-A": {"sku": "SKU-A", "last_alerted_at": _iso_hours_ago(2),
                       "urgency": "CRITICAL", "alert_count_7d": 1}}
    assert should_alert("SKU-A", "NORMAL", state) is False


# ---------------------------------------------------------------------------
# record_alert
# ---------------------------------------------------------------------------

def test_record_alert_creates_entry():
    state = {}
    record_alert("SKU-A", "CRITICAL", state)
    assert "SKU-A" in state
    assert state["SKU-A"]["urgency"] == "CRITICAL"
    assert state["SKU-A"]["alert_count_7d"] == 1


def test_record_alert_increments_count_within_7_days():
    state = {"SKU-A": {"sku": "SKU-A", "last_alerted_at": _iso_hours_ago(2),
                       "urgency": "HIGH", "alert_count_7d": 3}}
    record_alert("SKU-A", "CRITICAL", state)
    assert state["SKU-A"]["alert_count_7d"] == 4
    assert state["SKU-A"]["urgency"] == "CRITICAL"


def test_record_alert_resets_count_after_7_days():
    state = {"SKU-A": {"sku": "SKU-A", "last_alerted_at": _iso_hours_ago(24 * 8),
                       "urgency": "HIGH", "alert_count_7d": 5}}
    record_alert("SKU-A", "HIGH", state)
    assert state["SKU-A"]["alert_count_7d"] == 1