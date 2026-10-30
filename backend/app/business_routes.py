from fastapi import APIRouter, Header, HTTPException
from mysql.connector import Error

from app.database import get_db
from app.auth import get_current_user_id
from app.main import format_datetime
from app.schemas import BusinessInfoRequest, BusinessInfoResponse

router = APIRouter(prefix="/api/business", tags=["Business Information"])


def _fetch_staff(cursor, user_id: int, business_id: int) -> list[dict]:
    """Return only staff rows owned by the authenticated business."""
    cursor.execute(
        """
        SELECT business_staff_id, role, name, updated_at
        FROM business_staff
        WHERE user_id = %s AND business_id = %s
        ORDER BY business_staff_id ASC
        """,
        (user_id, business_id),
    )
    rows = cursor.fetchall()
    return [
        {
            "business_staff_id": row["business_staff_id"],
            "role": row["role"],
            "name": row["name"],
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
            "updated_at_formatted": format_datetime(row["updated_at"]) if row.get("updated_at") else None,
        }
        for row in rows
    ]


def _sync_staff(cursor, user_id: int, business_id: int, staff_members) -> None:
    """Upsert submitted staff rows and delete rows removed from the form.

    Existing IDs are always checked against both user_id and business_id to
    prevent one user from modifying another user's staff records.
    """
    retained_ids: list[int] = []
    seen_ids: set[int] = set()

    for staff in staff_members:
        role = staff.role.strip()
        name = staff.name.strip()
        if not role or not name:
            raise HTTPException(status_code=422, detail="Each staff member must have both a role and a name.")

        staff_id = staff.business_staff_id
        if staff_id is not None:
            if staff_id in seen_ids:
                raise HTTPException(status_code=422, detail="Duplicate staff member ID supplied.")
            seen_ids.add(staff_id)
            cursor.execute(
                """
                UPDATE business_staff
                SET role = %s, name = %s
                WHERE business_staff_id = %s AND user_id = %s AND business_id = %s
                """,
                (role, name, staff_id, user_id, business_id),
            )
            if cursor.rowcount == 0:
                # A no-op update can also have rowcount=0; verify ownership/existence.
                cursor.execute(
                    """SELECT business_staff_id FROM business_staff
                       WHERE business_staff_id = %s AND user_id = %s AND business_id = %s""",
                    (staff_id, user_id, business_id),
                )
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="A staff member was not found for this business.")
            retained_ids.append(staff_id)
        else:
            cursor.execute(
                """
                INSERT INTO business_staff (user_id, business_id, role, name)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, business_id, role, name),
            )
            retained_ids.append(int(cursor.lastrowid))

    # Delete only this authenticated user's staff records for this business.
    if retained_ids:
        placeholders = ", ".join(["%s"] * len(retained_ids))
        cursor.execute(
            f"""DELETE FROM business_staff
                WHERE user_id = %s AND business_id = %s
                  AND business_staff_id NOT IN ({placeholders})""",
            (user_id, business_id, *retained_ids),
        )
    else:
        cursor.execute(
            "DELETE FROM business_staff WHERE user_id = %s AND business_id = %s",
            (user_id, business_id),
        )


@router.post("/info", response_model=BusinessInfoResponse)
def save_business_info(request: BusinessInfoRequest, authorization: str = Header(...)):
    """Create or update the current user's business profile and staff list."""
    user_id = get_current_user_id(authorization)
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT business_id FROM business_info WHERE user_id = %s LIMIT 1 FOR UPDATE",
            (user_id,),
        )
        existing_business = cursor.fetchone()

        if existing_business:
            business_id = int(existing_business["business_id"])
            cursor.execute(
                """
                UPDATE business_info
                SET owner_name = %s, phone_number = %s,
                    business_name = %s, business_type = %s,
                    about_business = %s, year_established = %s,
                    google_review_link = %s
                WHERE user_id = %s
                """,
                (
                    request.owner_name.strip(), request.phone_number.strip(),
                    request.business_name.strip(), request.business_type.strip(),
                    request.about_business.strip(), request.year_established,
                    str(request.google_review_link), user_id,
                ),
            )
            message = "Business information updated successfully."
        else:
            cursor.execute(
                """
                INSERT INTO business_info (
                    user_id, owner_name, phone_number, business_name,
                    business_type, about_business, year_established, google_review_link
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id, request.owner_name.strip(), request.phone_number.strip(),
                    request.business_name.strip(), request.business_type.strip(),
                    request.about_business.strip(), request.year_established,
                    str(request.google_review_link),
                ),
            )
            business_id = int(cursor.lastrowid)
            message = "Business information saved successfully."

        # Synchronize staff only when this request includes the staff list.
        # This keeps older API clients from accidentally deleting staff rows.
        if request.staff_members is not None:
            _sync_staff(cursor, user_id, business_id, request.staff_members)

        cursor.execute(
            "SELECT owner_name, phone_number, updated_at FROM business_info WHERE business_id = %s LIMIT 1",
            (business_id,),
        )
        saved = cursor.fetchone()
        staff_members = _fetch_staff(cursor, user_id, business_id)
        connection.commit()

        return {
            "success": True,
            "message": message,
            "business_id": business_id,
            "owner_name": saved["owner_name"],
            "phone_number": saved["phone_number"],
            "staff_members": staff_members,
            "business_name": request.business_name.strip(),
            "business_type": request.business_type.strip(),
            "about_business": request.about_business.strip(),
            "year_established": request.year_established,
            "google_review_link": str(request.google_review_link),
            "updated_at": saved["updated_at"].isoformat() if saved and saved["updated_at"] else None,
            "updated_at_formatted": format_datetime(saved["updated_at"]) if saved and saved["updated_at"] else None,
        }
    except HTTPException:
        connection.rollback()
        raise
    except Error as error:
        connection.rollback()
        print(f"Business information database error: {error}")
        raise HTTPException(status_code=500, detail="Unable to save business information. Please try again.") from error
    except Exception as error:
        connection.rollback()
        print(f"Business information error: {error}")
        raise HTTPException(status_code=500, detail="Unable to save business information. Please try again.") from error
    finally:
        cursor.close()
        connection.close()


@router.get("/info", response_model=BusinessInfoResponse)
def get_business_info(authorization: str = Header(...)):
    """Return the current user's business profile and associated staff."""
    user_id = get_current_user_id(authorization)
    connection = get_db()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT business_id, owner_name, phone_number, business_name,
                   business_type, about_business, year_established,
                   google_review_link, updated_at
            FROM business_info
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        business = cursor.fetchone()
        if not business:
            return {
                "success": True,
                "message": "Business information not found.",
                "business_id": None,
                "owner_name": None,
                "phone_number": None,
                "staff_members": [],
                "business_name": None,
                "business_type": None,
                "about_business": None,
                "year_established": None,
                "google_review_link": None,
                "updated_at": None,
                "updated_at_formatted": None,
            }

        staff_members = _fetch_staff(cursor, user_id, int(business["business_id"]))
        return {
            "success": True,
            "message": "Business information retrieved successfully.",
            "business_id": business["business_id"],
            "owner_name": business["owner_name"],
            "phone_number": business["phone_number"],
            "staff_members": staff_members,
            "business_name": business["business_name"],
            "business_type": business["business_type"],
            "about_business": business["about_business"],
            "year_established": int(business["year_established"]) if business["year_established"] is not None else None,
            "google_review_link": business["google_review_link"],
            "updated_at": business["updated_at"].isoformat() if business["updated_at"] else None,
            "updated_at_formatted": format_datetime(business["updated_at"]) if business["updated_at"] else None,
        }
    except Error as error:
        print(f"Business information database error: {error}")
        raise HTTPException(status_code=500, detail="Unable to retrieve business information.") from error
    except Exception as error:
        print(f"Business information error: {error}")
        raise HTTPException(status_code=500, detail="Unable to retrieve business information.") from error
    finally:
        cursor.close()
        connection.close()
