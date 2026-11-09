"""Conta do usuário: perfil, troca de senha, exclusão, isolamento entre contas."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models import User, UserSession
from tests.conftest import DEFAULT_PASSWORD

COOKIE = "sf_session"
NEW_PASSWORD = "outra-senha-bem-longa-456"


def _count(model) -> int:
    return db.session.execute(select(func.count()).select_from(model)).scalar_one()


@pytest.fixture()
def bruno(make_client):
    c = make_client()
    assert c.register(email="bruno@example.com", display_name="Bruno").status_code == 201
    return c


# --- Acesso sem autenticação ------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/auth/me"),
        ("POST", "/api/auth/logout"),
        ("GET", "/api/users/me"),
        ("PATCH", "/api/users/me"),
        ("PUT", "/api/users/me/password"),
        ("DELETE", "/api/users/me"),
    ],
)
def test_protected_routes_require_authentication(client, method, path):
    response = client.open(path, method=method, json={})

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthenticated"


# --- Perfil ---------------------------------------------------------------------------


def test_update_display_name(ana):
    response = ana.request("PATCH", "/api/users/me", json={"display_name": "Ana Lima"})

    assert response.status_code == 200
    assert response.get_json()["user"]["display_name"] == "Ana Lima"


def test_changing_email_requires_current_password(ana):
    missing = ana.request("PATCH", "/api/users/me", json={"email": "nova@example.com"})
    wrong = ana.request(
        "PATCH", "/api/users/me", json={"email": "nova@example.com", "current_password": "errada-errada-123"}
    )
    ok = ana.request(
        "PATCH", "/api/users/me", json={"email": "Nova@Example.com", "current_password": DEFAULT_PASSWORD}
    )

    assert missing.status_code == 422
    assert wrong.status_code == 403
    assert ok.status_code == 200
    assert ok.get_json()["user"]["email"] == "nova@example.com"


def test_cannot_take_email_of_another_account(ana, bruno):
    response = bruno.request(
        "PATCH", "/api/users/me", json={"email": "ana@example.com", "current_password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 409


def test_empty_profile_update_is_rejected(ana):
    assert ana.request("PATCH", "/api/users/me", json={}).status_code == 422


@pytest.mark.parametrize(
    "extra",
    [{"id": "00000000-0000-0000-0000-000000000000"}, {"password_hash": "x"}, {"is_admin": True}, {"user_id": "x"}],
)
def test_mass_assignment_is_rejected(ana, extra):
    response = ana.request("PATCH", "/api/users/me", json={"display_name": "Ana", **extra})

    assert response.status_code == 422
    assert next(iter(extra)) in {f["field"] for f in response.get_json()["error"]["fields"]}


# --- Isolamento entre usuários (IDOR) ---------------------------------------------------------


def test_each_user_only_sees_own_account(ana, bruno):
    assert ana.request("GET", "/api/users/me").get_json()["user"]["email"] == "ana@example.com"
    assert bruno.request("GET", "/api/users/me").get_json()["user"]["email"] == "bruno@example.com"


def test_user_cannot_modify_another_account_by_id(ana, bruno):
    ana_id = ana.request("GET", "/api/users/me").get_json()["user"]["id"]

    # Não existem rotas com id na URL...
    assert bruno.request("PATCH", f"/api/users/{ana_id}", json={"display_name": "Hacker"}).status_code == 404
    assert bruno.request("DELETE", f"/api/users/{ana_id}", json={"password": DEFAULT_PASSWORD}).status_code == 404
    # ...e um id no corpo é rejeitado em vez de usado.
    assert bruno.request("PATCH", "/api/users/me", json={"id": ana_id, "display_name": "Hacker"}).status_code == 422

    assert ana.request("GET", "/api/users/me").get_json()["user"]["display_name"] == "Ana"


def test_user_cannot_use_csrf_token_to_act_on_another_session(ana, bruno):
    # O token CSRF de Ana não autoriza ações na sessão de Bruno.
    response = bruno.request("DELETE", "/api/users/me", json={"password": DEFAULT_PASSWORD}, headers={"X-CSRF-Token": ana.csrf_token})
    assert response.status_code == 403
    assert _count(User) == 2


# --- Troca de senha ----------------------------------------------------------------------


def test_change_password_with_wrong_current_password_fails(ana):
    response = ana.request(
        "PUT", "/api/users/me/password", json={"current_password": "errada-errada-123", "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 403


def test_change_password_rejects_weak_or_identical_password(ana):
    weak = ana.request("PUT", "/api/users/me/password", json={"current_password": DEFAULT_PASSWORD, "new_password": "123"})
    same = ana.request(
        "PUT", "/api/users/me/password", json={"current_password": DEFAULT_PASSWORD, "new_password": DEFAULT_PASSWORD}
    )
    assert weak.status_code == 422
    assert same.status_code == 422


def test_change_password_revokes_all_other_sessions(ana, make_client):
    other_device = make_client()
    assert other_device.login().status_code == 200
    old_token = ana.client.get_cookie(COOKIE).value

    response = ana.request(
        "PUT", "/api/users/me/password", json={"current_password": DEFAULT_PASSWORD, "new_password": NEW_PASSWORD}
    )

    assert response.status_code == 200
    assert ana.client.get_cookie(COOKIE).value != old_token  # sessão atual foi trocada
    assert ana.request("GET", "/api/auth/me").status_code == 200
    assert other_device.request("GET", "/api/auth/me").status_code == 401
    assert _count(UserSession) == 1
    assert make_client().login().status_code == 401
    assert make_client().login(password=NEW_PASSWORD).status_code == 200


# --- Exclusão de conta ---------------------------------------------------------------------


def test_delete_account_requires_password(ana):
    assert ana.request("DELETE", "/api/users/me", json={"password": "errada-errada-123"}).status_code == 403
    assert ana.request("DELETE", "/api/users/me", json={}).status_code == 422
    assert _count(User) == 1


def test_delete_account_removes_user_and_all_sessions(ana, bruno, make_client):
    second_device = make_client()
    second_device.login()

    response = ana.request("DELETE", "/api/users/me", json={"password": DEFAULT_PASSWORD})

    assert response.status_code == 200
    assert _count(User) == 1  # só Bruno
    assert db.session.execute(select(User)).scalar_one().email == "bruno@example.com"
    assert _count(UserSession) == 1  # só a sessão de Bruno
    assert ana.client.get("/api/auth/me").status_code == 401
    assert second_device.request("GET", "/api/auth/me").status_code == 401
    assert make_client().login().status_code == 401
    assert bruno.request("GET", "/api/auth/me").status_code == 200
