"""OAuth connection and Business Profile account/location selection routes."""
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.auth import get_current_user_id
from app.database import get_db
from .config import GOOGLE_FRONTEND_URL
from .google_api_service import GoogleApiError, get_valid_access_token
from .google_oauth_service import (
    GoogleOAuthError,
    build_authorization_url,
    consume_oauth_state,
    create_oauth_state,
    delete_connection,
    exchange_code_for_tokens,
    get_connection,
    get_connection_with_tokens,
    get_google_accounts,
    get_google_locations,
    save_google_tokens,
    select_google_account,
    update_selected_location,
)

router = APIRouter(prefix="/api/ai-review-reply/google", tags=["AI Review Reply - Google"])


def _get_user_business(cursor, user_id: int) -> dict:
    cursor.execute(
        """SELECT business_id, business_name, google_review_link
           FROM business_info WHERE user_id=%s
           ORDER BY business_id ASC LIMIT 1""",
        (user_id,),
    )
    business = cursor.fetchone()
    if not business:
        raise HTTPException(status_code=404, detail="Business information not found.")
    return business


def _frontend_redirect(status: str, reason: str | None = None) -> RedirectResponse:
    query = f"google_oauth={quote(status)}"
    if reason:
        query += f"&reason={quote(reason[:120])}"
    return RedirectResponse(f"{GOOGLE_FRONTEND_URL}/google-business?{query}", status_code=303)


@router.get("/status")
def status(user_id: int = Depends(get_current_user_id)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        business = _get_user_business(cursor, user_id)
        connection = get_connection(user_id, int(business["business_id"]))
        connection_status = connection.get("connection_status") if connection else None
        return {
            "success": True,
            "business": business,
            "connected": connection_status == "connected",
            "oauth_authorized": connection_status in ("oauth_connected", "connected"),
            "connection_status": connection_status,
            "location_selected": bool(connection and connection.get("google_location_name")),
            "connection": connection,
        }
    finally:
        cursor.close()
        db.close()


@router.get("/connect")
def connect(user_id: int = Depends(get_current_user_id)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        business = _get_user_business(cursor, user_id)
    finally:
        cursor.close()
        db.close()
    try:
        state = create_oauth_state(user_id, int(business["business_id"]))
        return {"success": True, "authorization_url": build_authorization_url(state)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured correctly.") from exc


@router.get("/callback")
def callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return _frontend_redirect("denied", error)
    if not code or not state:
        return _frontend_redirect("failed", "missing_callback_data")
    state_record = consume_oauth_state(state)
    if not state_record:
        return _frontend_redirect("failed", "invalid_or_expired_state")
    try:
        tokens = exchange_code_for_tokens(code)
        save_google_tokens(
            user_id=int(state_record["user_id"]),
            business_id=int(state_record["business_id"]),
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens.get("expires_in"),
        )
        return _frontend_redirect("success")
    except Exception:
        # Do not leak provider payloads, credentials, or exception strings into redirects.
        return _frontend_redirect("failed", "oauth_processing_error")


@router.get("/accounts")
def accounts(user_id: int = Depends(get_current_user_id)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        business = _get_user_business(cursor, user_id)
    finally:
        cursor.close()
        db.close()
    try:
        connection, token = get_valid_access_token(
            user_id, int(business["business_id"]), require_location=False
        )
        items = get_google_accounts(token)
        return {
            "success": True,
            "accounts": [
                {
                    "name": item.get("name"),
                    "account_id": item.get("accountId") or (item.get("name", "").split("/")[-1]),
                    "account_name": item.get("accountName") or item.get("name"),
                    "type": item.get("type"),
                }
                for item in items
            ],
        }
    except (GoogleApiError, GoogleOAuthError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 502) or 502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to retrieve Google Business Profile accounts.") from exc


@router.post("/select-account")
def select_account(payload: dict, user_id: int = Depends(get_current_user_id)):
    account_name = str(payload.get("account_name") or "").strip()
    if not account_name.startswith("accounts/"):
        raise HTTPException(status_code=400, detail="A valid Google Business Profile account is required.")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        business = _get_user_business(cursor, user_id)
    finally:
        cursor.close()
        db.close()
    business_id = int(business["business_id"])
    try:
        _, token = get_valid_access_token(user_id, business_id, require_location=False)
        accounts = get_google_accounts(token)
        selected = next((a for a in accounts if a.get("name") == account_name), None)
        if not selected:
            raise HTTPException(status_code=404, detail="That Google account is not available to this user.")
        select_google_account(user_id=user_id, business_id=business_id, account=selected)
        return {"success": True, "message": "Google Business Profile account selected."}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to select this Google Business Profile account.") from exc


@router.get("/locations")
def locations(user_id: int = Depends(get_current_user_id)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        business = _get_user_business(cursor, user_id)
    finally:
        cursor.close()
        db.close()
    business_id = int(business["business_id"])
    try:
        connection, token = get_valid_access_token(user_id, business_id, require_location=False)
        account_name = connection.get("google_account_name")
        if not account_name:
            raise HTTPException(status_code=400, detail="Select a Google Business Profile account first.")
        items = get_google_locations(token, account_name)
        return {
            "success": True,
            "locations": [
                {
                    "name": item.get("name"),
                    "location_id": (item.get("name") or "").split("/")[-1],
                    "title": item.get("title"),
                    "storefront_address": item.get("storefrontAddress"),
                    "website_uri": item.get("websiteUri"),
                }
                for item in items
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to retrieve Google Business Profile locations.") from exc


@router.post("/select-location")
def select_location(payload: dict, user_id: int = Depends(get_current_user_id)):
    location_name = str(payload.get("location_name") or "").strip()
    if not location_name.startswith("locations/"):
        raise HTTPException(status_code=400, detail="A valid Google location is required.")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        business = _get_user_business(cursor, user_id)
    finally:
        cursor.close()
        db.close()
    business_id = int(business["business_id"])
    try:
        connection, token = get_valid_access_token(user_id, business_id, require_location=False)
        account_name = connection.get("google_account_name")
        if not account_name:
            raise HTTPException(status_code=400, detail="Select a Google Business Profile account first.")
        locations = get_google_locations(token, account_name)
        selected = next((item for item in locations if item.get("name") == location_name), None)
        if not selected:
            raise HTTPException(status_code=404, detail="Selected Google location was not found.")
        update_selected_location(user_id=user_id, business_id=business_id, location=selected)
        return {
            "success": True,
            "message": "Google Business Profile connected successfully.",
            "location": {
                "name": selected.get("name"),
                "location_id": location_name.split("/")[-1],
                "title": selected.get("title"),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to validate the selected Google location.") from exc


@router.delete("/disconnect")
def disconnect(user_id: int = Depends(get_current_user_id)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        business = _get_user_business(cursor, user_id)
    finally:
        cursor.close()
        db.close()
    result = delete_connection(user_id, int(business["business_id"]))
    return {
        "success": True,
        "disconnected": bool(result),
        "google_revocation_succeeded": bool(result and result.get("google_revocation_succeeded")),
        "message": (
            "Connection removed and Google access revoked."
            if result and result.get("google_revocation_succeeded")
            else "Local connection removed. If Google revocation could not be confirmed, revoke access in your Google Account settings."
        ),
    }
