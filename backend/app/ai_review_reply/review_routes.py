"""Authenticated local review list and GBP review mutation routes."""
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user_id
from app.database import get_db
from .google_api_service import GoogleApiError
from .google_review_service import (
    delete_google_review_reply,
    get_local_reviews,
    reply_to_google_review,
    sync_reviews,
)

router = APIRouter(prefix="/api/ai-review-reply/reviews", tags=["AI Review Reply - Reviews"])


def _get_business_id(user_id: int) -> int:
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT business_id FROM business_info WHERE user_id=%s ORDER BY business_id ASC LIMIT 1",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Business information not found.")
        return int(row["business_id"])
    finally:
        cursor.close()
        db.close()


def _serialize_review(row: dict) -> dict:
    return {
        "review_id": row["review_id"],
        "google_review_name": row["google_review_name"],
        "google_review_id": row["google_review_id"],
        "reviewer_name": row["reviewer_name"] or "Google customer",
        "reviewer_profile_url": row["reviewer_profile_url"] or "",
        "star_rating": row["star_rating"] or "",
        "comment": row["comment"] or "",
        "google_create_time": row["google_create_time"] or "",
        "google_update_time": row["google_update_time"] or "",
        "reply_comment": row["reply_comment"] or "",
        "reply_update_time": row["reply_update_time"] or "",
        "last_synced_at": row["last_synced_at"].isoformat() if row.get("last_synced_at") else None,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


@router.get("")
def list_reviews(user_id: int = Depends(get_current_user_id)):
    business_id = _get_business_id(user_id)
    return {
        "success": True,
        "reviews": [_serialize_review(row) for row in get_local_reviews(user_id, business_id)],
    }


@router.post("/sync")
def sync(user_id: int = Depends(get_current_user_id)):
    business_id = _get_business_id(user_id)
    try:
        result = sync_reviews(user_id, business_id)
        return {"success": True, "message": "Google reviews synchronized.", **result}
    except GoogleApiError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to synchronize Google reviews.") from exc


@router.put("/{review_id}/reply")
def reply(review_id: int, payload: dict, user_id: int = Depends(get_current_user_id)):
    business_id = _get_business_id(user_id)
    comment = str(payload.get("comment") or "").strip()
    try:
        result = reply_to_google_review(user_id, business_id, review_id, comment)
        return {"success": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GoogleApiError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to publish the reply.") from exc


@router.delete("/{review_id}/reply")
def delete_reply(review_id: int, user_id: int = Depends(get_current_user_id)):
    business_id = _get_business_id(user_id)
    try:
        delete_google_review_reply(user_id, business_id, review_id)
        return {"success": True, "message": "Google review reply deleted."}
    except GoogleApiError as exc:
        raise HTTPException(status_code=exc.status_code or 502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to delete the reply.") from exc
