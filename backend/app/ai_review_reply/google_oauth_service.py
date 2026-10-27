"""OAuth state, authorization-code exchange, and Business Profile account APIs."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests

from app.database import get_db
from .config import (
    GOOGLE_ACCOUNT_API,
    GOOGLE_AUTHORIZATION_URL,
    GOOGLE_BUSINESS_SCOPE,
    GOOGLE_HTTP_TIMEOUT_SECONDS,
    GOOGLE_LOCATION_API,
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_REDIRECT_URI,
    GOOGLE_TOKEN_URL,
    OAUTH_STATE_MINUTES,
    validate_oauth_configuration,
)
from .google_token_service import decrypt_token, encrypt_token


class GoogleOAuthError(RuntimeError):
    """Safe integration error raised for OAuth and GBP API failures."""


def _response_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500] or "Google request failed."
    error = payload.get("error", {})
    if isinstance(error, dict):
        return str(error.get("message") or error.get("error_description") or "Google request failed.")
    return str(error or payload.get("error_description") or "Google request failed.")


def create_oauth_state(user_id: int, business_id: int) -> str:
    validate_oauth_configuration()
    state = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OAUTH_STATE_MINUTES)
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO google_oauth_state
               (state_token, user_id, business_id, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (state, user_id, business_id, expires_at.replace(tzinfo=None)),
        )
        db.commit()
        return state
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


def consume_oauth_state(state: str) -> dict | None:
    """Atomically consume state once, so a callback cannot be replayed."""
    if not state:
        return None
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT state_id, user_id, business_id, expires_at, used_at
               FROM google_oauth_state
               WHERE state_token = %s
               LIMIT 1 FOR UPDATE""",
            (state,),
        )
        row = cursor.fetchone()
        if not row or row["used_at"] is not None:
            db.rollback()
            return None
        expires_at = row["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now >= expires_at:
            db.rollback()
            return None
        cursor.execute(
            "UPDATE google_oauth_state SET used_at=%s WHERE state_id=%s AND used_at IS NULL",
            (now.replace(tzinfo=None), row["state_id"]),
        )
        if cursor.rowcount != 1:
            db.rollback()
            return None
        db.commit()
        return row
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


def build_authorization_url(state: str) -> str:
    validate_oauth_configuration()
    params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_BUSINESS_SCOPE,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTHORIZATION_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> dict:
    validate_oauth_configuration()
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=GOOGLE_HTTP_TIMEOUT_SECONDS,
    )
    if not response.ok:
        raise GoogleOAuthError(_response_error(response))
    payload = response.json()
    if not payload.get("access_token"):
        raise GoogleOAuthError("Google did not return an access token.")
    return payload


def get_google_accounts(access_token: str) -> list[dict]:
    response = requests.get(
        f"{GOOGLE_ACCOUNT_API}/accounts",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"pageSize": 100},
        timeout=GOOGLE_HTTP_TIMEOUT_SECONDS,
    )
    if not response.ok:
        raise GoogleOAuthError(_response_error(response))
    return response.json().get("accounts", []) or []


def get_google_locations(access_token: str, account_name: str) -> list[dict]:
    """Return all locations for one selected GBP account, following pagination."""
    if not account_name.startswith("accounts/"):
        raise GoogleOAuthError("Invalid Google Business Profile account.")
    results: list[dict] = []
    page_token = None
    while True:
        params = {"readMask": "name,title,storefrontAddress,websiteUri", "pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        response = requests.get(
            f"{GOOGLE_LOCATION_API}/{account_name}/locations",
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=GOOGLE_HTTP_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise GoogleOAuthError(_response_error(response))
        payload = response.json()
        results.extend(payload.get("locations", []) or [])
        page_token = payload.get("nextPageToken")
        if not page_token:
            return results


def save_google_tokens(
    *,
    user_id: int,
    business_id: int,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
) -> None:
    """Save OAuth tokens without silently choosing the first GBP account."""
    expires_at = None
    if expires_in:
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        ).replace(tzinfo=None)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO google_business_connection
               (business_id, user_id, google_account_name, google_account_id,
                google_location_name, google_location_id, google_location_title,
                access_token_encrypted, refresh_token_encrypted,
                access_token_expires_at, connection_status)
               VALUES (%s, %s, NULL, NULL, NULL, NULL, NULL, %s, %s, %s, 'oauth_connected')
               ON DUPLICATE KEY UPDATE
                 user_id=VALUES(user_id),
                 google_account_name=NULL,
                 google_account_id=NULL,
                 google_location_name=NULL,
                 google_location_id=NULL,
                 google_location_title=NULL,
                 access_token_encrypted=VALUES(access_token_encrypted),
                 refresh_token_encrypted=COALESCE(VALUES(refresh_token_encrypted), refresh_token_encrypted),
                 access_token_expires_at=VALUES(access_token_expires_at),
                 connection_status='oauth_connected',
                 updated_at=CURRENT_TIMESTAMP""",
            (
                business_id,
                user_id,
                encrypt_token(access_token),
                encrypt_token(refresh_token) if refresh_token else None,
                expires_at,
            ),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


def get_connection(user_id: int, business_id: int) -> dict | None:
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT connection_id, business_id, user_id, google_account_name,
                      google_account_id, google_location_name, google_location_id,
                      google_location_title, connection_status, access_token_expires_at,
                      last_review_sync_at, created_at, updated_at
               FROM google_business_connection
               WHERE user_id=%s AND business_id=%s LIMIT 1""",
            (user_id, business_id),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()


def get_connection_with_tokens(user_id: int, business_id: int) -> dict | None:
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT * FROM google_business_connection
               WHERE user_id=%s AND business_id=%s LIMIT 1""",
            (user_id, business_id),
        )
        row = cursor.fetchone()
        if not row:
            return None
        row["access_token"] = decrypt_token(row["access_token_encrypted"])
        row["refresh_token"] = (
            decrypt_token(row["refresh_token_encrypted"])
            if row.get("refresh_token_encrypted") else None
        )
        return row
    finally:
        cursor.close()
        db.close()


def select_google_account(*, user_id: int, business_id: int, account: dict) -> None:
    account_name = str(account.get("name") or "")
    if not account_name.startswith("accounts/"):
        raise GoogleOAuthError("Google returned an invalid account.")
    account_id = str(account.get("accountId") or account_name.split("/")[-1])
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """UPDATE google_business_connection
               SET google_account_name=%s, google_account_id=%s,
                   google_location_name=NULL, google_location_id=NULL,
                   google_location_title=NULL, connection_status='oauth_connected',
                   updated_at=CURRENT_TIMESTAMP
               WHERE user_id=%s AND business_id=%s""",
            (account_name, account_id, user_id, business_id),
        )
        if cursor.rowcount != 1:
            raise GoogleOAuthError("Google connection was not found.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


def update_selected_location(*, user_id: int, business_id: int, location: dict) -> None:
    location_name = str(location.get("name") or "")
    if not location_name.startswith("locations/"):
        raise GoogleOAuthError("Google returned an invalid location.")
    location_id = location_name.split("/")[-1]
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """UPDATE google_business_connection
               SET google_location_name=%s, google_location_id=%s,
                   google_location_title=%s, connection_status='connected',
                   updated_at=CURRENT_TIMESTAMP
               WHERE user_id=%s AND business_id=%s AND google_account_name IS NOT NULL""",
            (location_name, location_id, location.get("title"), user_id, business_id),
        )
        if cursor.rowcount != 1:
            raise GoogleOAuthError("Select a Google account before selecting a location.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()


def delete_connection(user_id: int, business_id: int) -> dict | None:
    """Revoke the stored Google grant when possible, then remove local connection data."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT refresh_token_encrypted, access_token_encrypted FROM google_business_connection WHERE user_id=%s AND business_id=%s LIMIT 1",
            (user_id, business_id),
        )
        row = cursor.fetchone()
        if not row:
            return None

        encrypted_refresh = row.get("refresh_token_encrypted")
        encrypted_access = row.get("access_token_encrypted")
        token_to_revoke = (
            decrypt_token(encrypted_refresh) if encrypted_refresh
            else decrypt_token(encrypted_access) if encrypted_access
            else None
        )
        revoke_succeeded = False
        if token_to_revoke:
            try:
                response = requests.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": token_to_revoke},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=GOOGLE_HTTP_TIMEOUT_SECONDS,
                )
                revoke_succeeded = response.status_code == 200
            except requests.RequestException:
                # Remove local credentials even if Google revocation is temporarily unavailable.
                revoke_succeeded = False

        cursor.execute(
            "DELETE FROM google_business_connection WHERE user_id=%s AND business_id=%s",
            (user_id, business_id),
        )
        db.commit()
        return {"deleted": True, "google_revocation_succeeded": revoke_succeeded}
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
        db.close()
