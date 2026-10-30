import json
import re
from typing import Any

from app.ai_management import generate_ai_text


MIN_OPTIONS = 4
MAX_OPTIONS = 20
MAX_ATTEMPTS = 2

QUERY_GENERATION_PROMPT = """
You create high-quality customer feedback questionnaires.

Generate exactly {question_count} questions for the business described by the user.
Each question MUST have between 4 and 20 distinct, non-empty answer options.
The minimum of 4 options is mandatory for EVERY question. Do not return fewer than 4.
Do not create extra questions. Vary the number of options where it is useful; never
add meaningless choices just to increase the count.

Questions should collect useful details that can help create a natural customer review.
Keep questions concise, customer-friendly, specific to the business, and easy to answer.
Use the supplied owner and staff names/roles only when relevant, such as asking which
team member assisted the customer. Never force a person's name into unrelated questions.
Do not invent people, services, prices, guarantees, or business facts.
When staff information is absent, do not invent staff names.

Return ONLY valid JSON using this structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"]
    }}
  ]
}}
"""


def _extract_json(raw_output: str) -> dict[str, Any]:
    """Parse JSON from an AI response, tolerating a surrounding Markdown fence."""
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise ValueError("AI returned an empty questionnaire.")

    cleaned = raw_output.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # If the provider adds brief text outside the JSON, isolate the JSON object.
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        if start == -1:
            raise ValueError("AI response did not contain a JSON object.")
        cleaned = cleaned[start:]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Retry parsing only the first complete-looking JSON object.
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("AI returned invalid questionnaire JSON.")
        try:
            data = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as error:
            raise ValueError("AI returned invalid questionnaire JSON.") from error

    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object.")
    return data


def _validate_questions(data: dict[str, Any], question_count: int) -> list[dict[str, Any]]:
    questions = data.get("questions")
    if not isinstance(questions, list):
        raise ValueError("AI response does not contain a questions list.")

    if len(questions) != question_count:
        raise ValueError(
            f"AI returned {len(questions)} questions; expected {question_count}."
        )

    validated: list[dict[str, Any]] = []

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError(f"Question {index} has an invalid format.")

        question_text = str(question.get("question") or "").strip()
        if not question_text:
            raise ValueError(f"Question {index} is empty.")

        raw_options = question.get("options")
        if not isinstance(raw_options, list):
            raise ValueError(f"Question {index} has an invalid options list.")

        # Remove blank and duplicate choices while preserving their original order.
        options: list[str] = []
        seen: set[str] = set()
        for raw_option in raw_options:
            option = str(raw_option or "").strip()
            normalized = option.casefold()
            if option and normalized not in seen:
                seen.add(normalized)
                options.append(option)

        if len(options) < MIN_OPTIONS:
            raise ValueError(
                f"Question {index} has {len(options)} distinct options; "
                f"at least {MIN_OPTIONS} are required."
            )

        validated.append({
            "question": question_text,
            "options": options[:MAX_OPTIONS],
        })

    return validated


def _validate_raw_response(raw_output: str, question_count: int) -> None:
    """Validation callback used by ai_management to decide whether to retry."""
    data = _extract_json(raw_output)
    _validate_questions(data, question_count)


def generate_questions(
    business_name: str,
    business_type: str,
    about_business: str,
    year_established: int | str | None,
    question_count: int = 4,
    owner_name: str | None = None,
    staff_members: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Generate a business-specific questionnaire; ai_management owns response retries."""
    if not 2 <= question_count <= 8:
        raise ValueError("Question count must be between 2 and 8.")

    staff_members = staff_members or []
    staff_context = "\\n".join(
        f"- Name: {member.get('name', '').strip()}; Role: {member.get('role', '').strip() or 'Not specified'}"
        for member in staff_members
        if member.get("name", "").strip()
    ) or "No staff members provided."

    user_input = f"""
Business profile:
- Business name: {business_name or "Not provided"}
- Business type: {business_type or "Not provided"}
- About the business: {about_business or "Not provided"}
- Year established: {year_established if year_established is not None else "Not provided"}
- Owner name: {owner_name.strip() if owner_name and owner_name.strip() else "Not provided"}
- Staff members:
{staff_context}

Create the customer questionnaire using only the information above.
"""

    system_prompt = QUERY_GENERATION_PROMPT.format(question_count=question_count)

    raw_output = generate_ai_text(
        user_input,
        system_instruction=system_prompt,
        temperature=0.7,
        max_output_tokens=6000,
        response_validator=lambda output: _validate_raw_response(
            output, question_count
        ),
        max_response_retries=1,
        response_retry_instruction=(
            f"Return exactly {question_count} questions. Every question must contain "
            f"at least {MIN_OPTIONS} distinct, non-empty options and no more than "
            f"{MAX_OPTIONS}. Do not invent business facts or people. Return valid JSON only."
        ),
    )

    # Validation already ran inside ai_management. Parse once more to return
    # the normalized, validated structure expected by the API.
    data = _extract_json(raw_output)
    return _validate_questions(data, question_count)
