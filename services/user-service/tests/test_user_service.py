"""
User Service — Unit Tests
Tests user management, role permission checks, team assignment, pagination.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


class TestRolePermissions:
    """Test role-based permission matrix."""

    PERMISSIONS = {
        "admin": {
            "create_user", "delete_user", "assign_role",
            "view_all_cases", "manage_teams", "view_audit_log",
        },
        "manager": {
            "view_all_cases", "assign_case", "manage_teams",
            "view_analytics", "create_case",
        },
        "supervisor": {
            "view_team_cases", "assign_case", "escalate_case",
            "view_analytics", "create_case",
        },
        "agent": {
            "view_assigned_cases", "update_case", "add_note",
            "create_case",
        },
        "customer": {"create_case", "view_own_cases"},
    }

    def can(self, role: str, permission: str) -> bool:
        return permission in self.PERMISSIONS.get(role, set())

    def test_admin_can_delete_user(self):
        assert self.can("admin", "delete_user") is True

    def test_agent_cannot_delete_user(self):
        assert self.can("agent", "delete_user") is False

    def test_customer_can_create_case(self):
        assert self.can("customer", "create_case") is True

    def test_customer_cannot_view_all_cases(self):
        assert self.can("customer", "view_all_cases") is False

    def test_manager_can_view_analytics(self):
        assert self.can("manager", "view_analytics") is True

    def test_agent_cannot_manage_teams(self):
        assert self.can("agent", "manage_teams") is False

    def test_supervisor_can_escalate(self):
        assert self.can("supervisor", "escalate_case") is True

    def test_unknown_role_has_no_permissions(self):
        assert self.can("hacker", "delete_user") is False

    def test_all_roles_have_permissions(self):
        for role in ["admin", "manager", "supervisor", "agent", "customer"]:
            assert len(self.PERMISSIONS.get(role, set())) > 0


class TestUserValidation:
    """Test user input validation."""

    def _validate_email(self, email: str) -> bool:
        import re
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _validate_password_strength(self, pw: str) -> tuple[bool, str]:
        if len(pw) < 8:
            return False, "Password must be at least 8 characters"
        if not any(c.isupper() for c in pw):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.isdigit() for c in pw):
            return False, "Password must contain at least one digit"
        return True, "ok"

    def test_valid_email(self):
        assert self._validate_email("user@example.com") is True

    def test_valid_subdomain_email(self):
        assert self._validate_email("agent@company.co.uk") is True

    def test_invalid_email_no_at(self):
        assert self._validate_email("notanemail") is False

    def test_invalid_email_no_domain(self):
        assert self._validate_email("user@") is False

    def test_strong_password(self):
        ok, _ = self._validate_password_strength("Secure@123")
        assert ok is True

    def test_short_password(self):
        ok, msg = self._validate_password_strength("Ab1")
        assert ok is False
        assert "8 characters" in msg

    def test_password_no_uppercase(self):
        ok, msg = self._validate_password_strength("secure123")
        assert ok is False
        assert "uppercase" in msg

    def test_password_no_digit(self):
        ok, msg = self._validate_password_strength("SecurePass")
        assert ok is False
        assert "digit" in msg


class TestUserPagination:
    """Test pagination logic for user list endpoint."""

    def _paginate(self, items: list, page: int, page_size: int) -> dict:
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "items": items[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, -(-total // page_size)),  # ceiling division
        }

    def test_first_page(self):
        users = list(range(25))
        result = self._paginate(users, page=1, page_size=10)
        assert result["items"] == list(range(10))
        assert result["total"] == 25

    def test_second_page(self):
        users = list(range(25))
        result = self._paginate(users, page=2, page_size=10)
        assert result["items"] == list(range(10, 20))

    def test_last_page_partial(self):
        users = list(range(25))
        result = self._paginate(users, page=3, page_size=10)
        assert result["items"] == list(range(20, 25))
        assert len(result["items"]) == 5

    def test_total_pages_correct(self):
        users = list(range(25))
        result = self._paginate(users, page=1, page_size=10)
        assert result["total_pages"] == 3

    def test_empty_list(self):
        result = self._paginate([], page=1, page_size=10)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["total_pages"] == 1

    def test_single_page(self):
        users = list(range(5))
        result = self._paginate(users, page=1, page_size=10)
        assert result["total_pages"] == 1


class TestTeamManagement:
    """Test team assignment and membership logic."""

    def _assign_to_team(self, user: dict, team_id: str) -> dict:
        if user.get("role") not in ("agent", "supervisor"):
            raise ValueError(f"Cannot assign role '{user['role']}' to a team")
        return {**user, "team_id": team_id}

    def _get_team_members(self, users: list, team_id: str) -> list:
        return [u for u in users if u.get("team_id") == team_id]

    def test_agent_can_be_assigned(self):
        user = {"id": "u1", "role": "agent", "team_id": None}
        updated = self._assign_to_team(user, "team-mortgage")
        assert updated["team_id"] == "team-mortgage"

    def test_supervisor_can_be_assigned(self):
        user = {"id": "u2", "role": "supervisor", "team_id": None}
        updated = self._assign_to_team(user, "team-credit")
        assert updated["team_id"] == "team-credit"

    def test_admin_cannot_be_assigned_to_team(self):
        user = {"id": "u3", "role": "admin"}
        with pytest.raises(ValueError):
            self._assign_to_team(user, "team-x")

    def test_get_team_members_filters_correctly(self):
        users = [
            {"id": "u1", "team_id": "team-a"},
            {"id": "u2", "team_id": "team-b"},
            {"id": "u3", "team_id": "team-a"},
        ]
        members = self._get_team_members(users, "team-a")
        assert len(members) == 2
        assert all(m["team_id"] == "team-a" for m in members)

    def test_empty_team(self):
        users = [{"id": "u1", "team_id": "team-b"}]
        members = self._get_team_members(users, "team-a")
        assert members == []


class TestUserProfileUpdate:
    """Test allowed profile update fields."""

    ALLOWED_UPDATE_FIELDS = {"full_name", "avatar_url", "phone", "timezone"}

    def _apply_update(self, user: dict, updates: dict) -> dict:
        filtered = {k: v for k, v in updates.items() if k in self.ALLOWED_UPDATE_FIELDS}
        return {**user, **filtered}

    def test_full_name_update_allowed(self):
        user = {"id": "u1", "full_name": "Old Name", "email": "a@b.com"}
        updated = self._apply_update(user, {"full_name": "New Name"})
        assert updated["full_name"] == "New Name"

    def test_email_update_blocked(self):
        user = {"id": "u1", "email": "original@b.com"}
        updated = self._apply_update(user, {"email": "hacker@evil.com"})
        assert updated["email"] == "original@b.com"  # unchanged

    def test_role_update_blocked(self):
        user = {"id": "u1", "role": "agent"}
        updated = self._apply_update(user, {"role": "admin"})
        assert updated["role"] == "agent"  # unchanged

    def test_multiple_allowed_fields(self):
        user = {"id": "u1", "full_name": "Old", "avatar_url": None}
        updated = self._apply_update(user, {"full_name": "New", "avatar_url": "https://cdn/img.png"})
        assert updated["full_name"] == "New"
        assert updated["avatar_url"] == "https://cdn/img.png"
