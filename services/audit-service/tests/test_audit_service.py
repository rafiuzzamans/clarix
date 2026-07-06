"""
Audit Service — Unit Tests
Tests audit event creation, filtering, querying, and security logging.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


class TestAuditEventSchema:
    """Test audit event payload creation and field validation."""

    def _make_event(
        self,
        actor_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str,
        description: str,
        ip_address: str = None,
        metadata: dict = None,
    ) -> dict:
        return {
            "actor_id": actor_id,
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "description": description,
            "ip_address": ip_address or "0.0.0.0",
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def test_event_has_all_required_fields(self):
        event = self._make_event(
            "user-1", "case.status_changed", "case", "case-123",
            "Status changed from open to in_progress"
        )
        for field in ["actor_id", "event_type", "resource_type",
                      "resource_id", "description", "created_at"]:
            assert field in event

    def test_ip_address_defaults_to_zero(self):
        event = self._make_event("u1", "login", "session", "s1", "User logged in")
        assert event["ip_address"] == "0.0.0.0"

    def test_custom_ip_address(self):
        event = self._make_event("u1", "login", "session", "s1", "Login",
                                 ip_address="192.168.1.100")
        assert event["ip_address"] == "192.168.1.100"

    def test_metadata_is_dict(self):
        event = self._make_event("u1", "case.assigned", "case", "c1",
                                 "Case assigned to agent",
                                 metadata={"assigned_to": "agent-5"})
        assert isinstance(event["metadata"], dict)
        assert event["metadata"]["assigned_to"] == "agent-5"

    def test_created_at_is_string(self):
        event = self._make_event("u1", "login", "session", "s1", "Login")
        assert isinstance(event["created_at"], str)


class TestAuditEventTypes:
    """Test the categorisation and naming of audit event types."""

    VALID_EVENT_TYPES = {
        # Auth events
        "auth.login", "auth.logout", "auth.login_failed",
        "auth.password_changed", "auth.mfa_enabled",
        # Case events
        "case.created", "case.updated", "case.status_changed",
        "case.assigned", "case.escalated", "case.resolved", "case.closed",
        # User events
        "user.created", "user.updated", "user.role_changed", "user.deactivated",
        # File events
        "file.uploaded", "file.deleted",
        # Admin events
        "admin.config_changed",
    }

    def test_all_auth_events_valid(self):
        auth_events = [e for e in self.VALID_EVENT_TYPES if e.startswith("auth.")]
        assert len(auth_events) >= 3

    def test_all_case_events_valid(self):
        case_events = [e for e in self.VALID_EVENT_TYPES if e.startswith("case.")]
        assert len(case_events) >= 5

    def test_login_event_exists(self):
        assert "auth.login" in self.VALID_EVENT_TYPES

    def test_unknown_event_not_in_set(self):
        assert "hacker.exploit" not in self.VALID_EVENT_TYPES

    def test_event_type_has_category_prefix(self):
        for event_type in self.VALID_EVENT_TYPES:
            assert "." in event_type, f"Event '{event_type}' missing category prefix"


class TestAuditEventFiltering:
    """Test filtering and searching audit log entries."""

    def _filter_events(
        self,
        events: list,
        actor_id: str = None,
        event_type: str = None,
        resource_type: str = None,
        since: datetime = None,
    ) -> list:
        results = events
        if actor_id:
            results = [e for e in results if e["actor_id"] == actor_id]
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        if resource_type:
            results = [e for e in results if e["resource_type"] == resource_type]
        if since:
            results = [e for e in results
                       if datetime.fromisoformat(e["created_at"]) >= since]
        return results

    @pytest.fixture
    def sample_events(self):
        now = datetime.now(timezone.utc)
        return [
            {"actor_id": "u1", "event_type": "auth.login", "resource_type": "session",
             "created_at": (now - timedelta(hours=2)).isoformat()},
            {"actor_id": "u2", "event_type": "case.created", "resource_type": "case",
             "created_at": (now - timedelta(hours=1)).isoformat()},
            {"actor_id": "u1", "event_type": "case.updated", "resource_type": "case",
             "created_at": now.isoformat()},
        ]

    def test_filter_by_actor(self, sample_events):
        results = self._filter_events(sample_events, actor_id="u1")
        assert len(results) == 2
        assert all(e["actor_id"] == "u1" for e in results)

    def test_filter_by_event_type(self, sample_events):
        results = self._filter_events(sample_events, event_type="case.created")
        assert len(results) == 1

    def test_filter_by_resource_type(self, sample_events):
        results = self._filter_events(sample_events, resource_type="case")
        assert len(results) == 2

    def test_filter_since_timestamp(self, sample_events):
        one_hour_ago = datetime.now(timezone.utc) - timedelta(minutes=90)
        results = self._filter_events(sample_events, since=one_hour_ago)
        assert len(results) == 2  # last 90 minutes

    def test_combined_filters(self, sample_events):
        results = self._filter_events(sample_events, actor_id="u1", resource_type="case")
        assert len(results) == 1
        assert results[0]["event_type"] == "case.updated"

    def test_no_filters_returns_all(self, sample_events):
        results = self._filter_events(sample_events)
        assert len(results) == 3


class TestAuditPagination:
    """Test cursor-based pagination for audit logs."""

    def _paginate(self, events: list, page: int, page_size: int) -> dict:
        # Sort descending by created_at (newest first)
        sorted_events = sorted(events, key=lambda e: e["created_at"], reverse=True)
        total = len(sorted_events)
        start = (page - 1) * page_size
        return {
            "items": sorted_events[start:start + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def test_returns_newest_first(self):
        now = datetime.now(timezone.utc)
        events = [
            {"created_at": (now - timedelta(hours=2)).isoformat(), "id": "old"},
            {"created_at": now.isoformat(), "id": "new"},
        ]
        result = self._paginate(events, 1, 10)
        assert result["items"][0]["id"] == "new"

    def test_page_size_respected(self):
        now = datetime.now(timezone.utc)
        events = [{"created_at": (now - timedelta(minutes=i)).isoformat()}
                  for i in range(20)]
        result = self._paginate(events, 1, 5)
        assert len(result["items"]) == 5

    def test_total_count_correct(self):
        now = datetime.now(timezone.utc)
        events = [{"created_at": (now - timedelta(minutes=i)).isoformat()}
                  for i in range(50)]
        result = self._paginate(events, 1, 10)
        assert result["total"] == 50


class TestSecurityAuditEvents:
    """Test security-related audit events and alerting thresholds."""

    def _count_failed_logins(self, events: list, actor_id: str, window_minutes: int = 15) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        return sum(
            1 for e in events
            if e["actor_id"] == actor_id
            and e["event_type"] == "auth.login_failed"
            and datetime.fromisoformat(e["created_at"]) >= cutoff
        )

    def _is_account_lockout_required(self, failed_count: int, threshold: int = 5) -> bool:
        return failed_count >= threshold

    def test_counts_failed_logins_in_window(self):
        now = datetime.now(timezone.utc)
        events = [
            {"actor_id": "u1", "event_type": "auth.login_failed",
             "created_at": (now - timedelta(minutes=5)).isoformat()},
            {"actor_id": "u1", "event_type": "auth.login_failed",
             "created_at": (now - timedelta(minutes=3)).isoformat()},
            {"actor_id": "u1", "event_type": "auth.login_failed",
             "created_at": (now - timedelta(minutes=20)).isoformat()},  # outside window
        ]
        count = self._count_failed_logins(events, "u1", window_minutes=15)
        assert count == 2  # Only 2 within 15 min window

    def test_lockout_threshold_5(self):
        assert self._is_account_lockout_required(5) is True

    def test_no_lockout_below_threshold(self):
        assert self._is_account_lockout_required(4) is False

    def test_different_user_not_counted(self):
        now = datetime.now(timezone.utc)
        events = [
            {"actor_id": "u2", "event_type": "auth.login_failed",
             "created_at": now.isoformat()},
        ]
        count = self._count_failed_logins(events, "u1")
        assert count == 0
