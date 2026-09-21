from fastapi import HTTPException

from sentinel.config import settings
from sentinel.services.authz import authorize_action, enforce_tenant_scope


def test_phase8_rbac_forbids_arbiter_report_lock() -> None:
    old = settings.rbac_enabled
    try:
        settings.rbac_enabled = True
        raised = False
        try:
            authorize_action("arbiter", "report_lock")
        except HTTPException as exc:
            raised = True
            assert exc.status_code == 403
        assert raised is True
    finally:
        settings.rbac_enabled = old


def test_phase8_rbac_allows_chief_report_lock() -> None:
    old = settings.rbac_enabled
    try:
        settings.rbac_enabled = True
        role = authorize_action("chief_arbiter", "report_lock")
        assert role == "chief_arbiter"
    finally:
        settings.rbac_enabled = old


def test_phase8_tenant_scope_requires_federation_header_for_non_system() -> None:
    old = settings.tenant_enforcement_enabled
    try:
        settings.tenant_enforcement_enabled = True
        raised = False
        try:
            enforce_tenant_scope("arbiter", None, "fedA::event-12")
        except HTTPException as exc:
            raised = True
            assert exc.status_code == 403
        assert raised is True
    finally:
        settings.tenant_enforcement_enabled = old


def test_phase8_tenant_scope_rejects_cross_federation_event() -> None:
    old = settings.tenant_enforcement_enabled
    try:
        settings.tenant_enforcement_enabled = True
        raised = False
        try:
            enforce_tenant_scope("federation_admin", "fedA", "fedB::event-12")
        except HTTPException as exc:
            raised = True
            assert exc.status_code == 403
        assert raised is True
    finally:
        settings.tenant_enforcement_enabled = old

