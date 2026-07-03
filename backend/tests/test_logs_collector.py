"""Unit tests for the log scanner."""

from app.kubernetes.logs_collector import scan_logs


def test_detects_exception_and_connection_failure():
    text = "\n".join(
        [
            "INFO starting service",
            "Traceback (most recent call last):",
            "psycopg2.OperationalError: connection refused",
            "INFO retrying",
        ]
    )
    matches = scan_logs(text)
    categories = {m["category"] for m in matches}
    assert "exception" in categories
    assert "connection_failure" in categories


def test_detects_missing_env_var():
    matches = scan_logs("RuntimeError: environment variable DATABASE_URL is not set")
    assert any(m["category"] == "missing_env_var" for m in matches)


def test_no_false_positives_on_clean_logs():
    matches = scan_logs("INFO listening on :8080\nINFO ready to serve traffic")
    assert matches == []


def test_dedupes_repeated_lines():
    text = "\n".join(["Exception happened"] * 5)
    matches = scan_logs(text)
    assert len(matches) == 1
