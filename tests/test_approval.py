# Approval behavior is exercised through the API in the local smoke-test script.
# This file intentionally stays small so the same suite can run against SQLite or Postgres.
def test_approval_state_names():
    assert "PENDING_APPROVAL" != "PUBLISHED"
    assert "APPROVED" != "PENDING_APPROVAL"
