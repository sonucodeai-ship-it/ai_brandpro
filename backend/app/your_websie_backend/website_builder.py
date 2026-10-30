import html as html_lib
import json
import logging
import re
from urllib.parse import quote

from app.ai_management import generate_ai_text

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    cleaned = (text or "").strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end <= start:
            raise RuntimeError(
                "AI returned invalid JSON."
            )

        try:
            data = json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "AI returned invalid JSON."
            ) from error

    if not isinstance(data, dict):
        raise RuntimeError(
            "AI returned JSON, but not a JSON object."
        )

    return data


def _generate_text(
    prompt: str,
    temperature: float = 0.7,
    max_output_tokens: int = 12000,
) -> str:
    """Generate website content through the centralized AI provider layer."""
    return generate_ai_text(
        prompt=prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


def _generate_json(
    prompt: str,
    temperature: float = 0.8,
    max_output_tokens: int = 3000,
) -> dict:
    return _extract_json(
        _generate_text(
            prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
    )


WEBSITE_QUESTION_PROMPT = """
You are an expert customer-facing business showcase information architect.

Create a business-specific questionnaire for a single-page customer showcase.
The purpose is NOT to collect information for a conventional corporate website.
The purpose is to help a business owner clearly present what customers can
actually see, use, buy, book, choose, or compare.

The questionnaire MUST change substantially according to the business type.
Focus on practical customer-facing information such as facilities,
amenities, services, treatments, products, menu/catalog items, packages,
rate lists, pricing, options, policies, and useful visit information.

BUSINESS-SPECIFIC DIRECTION

RESTAURANT / CAFE / FOOD BUSINESS:
- menu categories and important items
- signature dishes or specialties
- prices/rate list when available
- serving sizes, variants, combos, or packages when relevant
- dietary options when actually offered
- dine-in, takeaway, or delivery facilities when supplied
- opening hours and location/contact only if not already known

DENTAL / MEDICAL / CLINIC:
- treatments/services offered
- treatment-specific facilities and equipment
- specialties or areas of care
- consultation/appointment information
- treatment packages or published fees/rates when available
- patient facilities and useful visit information
- emergency/urgent-care availability only if actually offered

SALON / SPA / BEAUTY:
- services and service categories
- packages
- rate list/prices
- facilities and treatment areas
- products or brands only if supplied
- booking and visit information

GYM / FITNESS:
- facilities and equipment
- memberships and pricing
- programs/classes
- personal training or other services
- amenities and timings

HOTEL / RESORT:
- room categories and rates when available
- amenities/facilities
- dining options/menu information
- experiences and activities
- packages
- check-in/policy information when supplied

RETAIL / CLOTHING / FASHION:
- product categories
- collections or product ranges
- prices/rate ranges when available
- sizes, variants, materials, or customization when supplied
- store facilities and shopping options

SERVICE BUSINESS / OTHER:
Identify the most useful customer-facing information for THAT business.
Prioritize what customers need to understand the offering and make a visit,
purchase, booking, or enquiry decision.

RULES:
- Ask 8 to 12 questions.
- Do not ask for information already present in business_info, including owner name,
  business phone number, and staff names/roles.
- Use the owner name, phone number, and saved staff names/roles to make
  questions specific to this business where relevant. For example,
  refer to known staff by their saved names and roles when asking how services
  are delivered or which staff members handle them. Do not ask the owner to
  re-enter those known details.
- Do not ask technical questions.
- Do not ask for passwords, API keys, or website-development details.
- Do not invent prices, services, facilities, products, staff, claims, or policies.
- Ask the owner to provide prices/rates only if their business normally publishes them.
- Questions must be easy for a business owner to answer.
- Prefer questions that produce concrete customer-facing content over vague marketing copy.
- Ask for a complete list when a list is important, e.g. menu items, services,
  facilities, amenities, packages, or rates.
- If exact prices are not available, allow the owner to say that pricing is
  enquiry-based or not published; do not force invented prices.
- Do not repeat information already supplied in the business description.
- The next AI stage will write answers, so focus this stage on excellent,
  non-repetitive questions that reveal useful customer-facing information.
- Use the saved owner and staff names/roles only where relevant; never invent
  additional people or assign unsupported responsibilities.
- Return only valid JSON.

Return:
{
  "questions": [
    {
      "question_key": "snake_case",
      "question_text": "Question",
      "input_type": "textarea",
      "required": true,
      "placeholder": "Short optional hint only",
      "helper_text": "Short help"
    }
  ]
}
"""



PROFESSIONAL_ANSWER_PROMPT = """
You are a practical business-showcase content specialist. Create editable starter
answers for a customer-facing digital showcase. Its core content is the actual
menu, services, facilities, products, packages, options, and rates—not marketing
copy. Answers must be point-to-point and easy to scan.

IMPORTANT DISTINCTION
- FACTS in the business profile are confirmed facts.
- If a question needs details that are missing, create a useful CATEGORY-APPROPRIATE
  SUGGESTED DRAFT where doing so is reasonable. Never pretend the suggestion is
  confirmed or an official business price.
- Do not invent the business's exact official prices, specific brands, credentials,
  opening hours, policies, staff duties, or unique facilities.
- Suggested menus/services/facilities and estimated prices must be represented
  as editable draft content, but NEVER append warning/disclaimer sentences to
  the answer field. Set needs_owner_confirmation=true for suggested content.

SHOWCASE CONTENT REQUIREMENTS
1. For a MENU question with no menu supplied, draft a compact, category-appropriate
   sample menu with useful item names and realistic indicative INR prices when the
   business is in India or no location/currency is supplied. Group items by 2–4
   useful categories. Do not invent a signature dish or claim items are actually
   sold; use the suggested-draft note.
2. For RATE / PRICE / FEE / PACKAGE / MEMBERSHIP questions, do not answer only
   "contact us for prices" when a useful indicative draft can be made. Provide
   5–10 relevant itemized services or tiers with INR prices/ranges by default if
   location/currency is not supplied. Keep the prices internally consistent and
   appropriate to the business category and likely service level. These are
   planning estimates, not researched or official prices; add the single compact
   indicative-rate note at the end. If the category is regulated (medical, dental,
   legal, financial), use broad indicative ranges only, avoid precise clinical
   promises, and note briefly that final fees depend on consultation/case/materials.
3. For SERVICES / TREATMENTS / PRODUCTS, provide a concise category-specific list
   of relevant options. Separate confirmed offerings from suggested options; if
   details are not in the profile, use the suggested-draft note once at the end.
4. For FACILITIES / AMENITIES / EQUIPMENT, provide a short grouped list of the most
   relevant facilities customers would expect to check for this category. Do not
   claim these exist; if inferred, append the suggested-draft note once.
5. For packages or memberships, show tier/name, key inclusions, and indicative
   price/range when the question asks for rates. Do not make up discounts or
   contractual terms.
6. Use the business type and about_business to choose relevant content. Do not
   suggest unrelated items or services just to reach a target count.
7. If the profile contains real menu items, rates, services, or facilities, use
   those first and preserve their exact names and prices. Do not overwrite them
   with estimates. You may add a separate clearly marked suggested section only
   when the question asks for a fuller list and the missing items are useful.

POINT-TO-POINT WRITING RULES
- Prefer short headings and bullet lines: "Item — ₹price" or "Facility — short detail".
- Usually 4–10 bullets for list questions; 1–3 concise sentences for simple questions.
- Target roughly 15–80 words. A menu or rate card may be longer if needed.
- No introductions, repeated business name, slogans, generic benefits, filler,
  long paragraphs, fake testimonials, ratings, awards, guarantees, or superlatives.
- No placeholders such as [insert here], and no explanation of what the AI did.
- Use supplied owner/staff names and roles only when relevant.
- Return one answer for every question_key, exactly matching its key, as valid JSON:
{
  "answers": [
    {"question_key": "exact_question_key", "answer_text": "Point-to-point answer", "needs_owner_confirmation": true}
  ]
}
"""


def _clean_initial_answer(answer: str) -> str:
    """Remove AI-warning labels and tidy the answer without changing its facts."""
    text = str(answer or "").strip()
    warning_patterns = (
        r"AI[- ]SUGGESTED\s+INDICATIVE\s+RATES\s*[—–-]?\s*confirm\s+and\s+edit\s+before\s+publishing\.?",
        r"AI[- ]SUGGESTED\s+DRAFT\s*[—–-]?\s*confirm\s+the\s+listed\s+services/facilities\s+before\s+publishing\.?",
        r"AI[- ]GENERATED\s+DRAFT[^.]*\.?",
        r"confirm\s+and\s+edit\s+before\s+publishing\.?",
        r"confirm\s+the\s+listed\s+services/facilities\s+before\s+publishing\.?",
        r"suggested\s+draft\s*[—–-]\s*verify\s+availability\s+before\s+publishing\.?",
        r"indicative\s+draft\s+rates\s*[—–-]\s*verify\s+prices\s+before\s+publishing\.?",
        r"verify\s+availability\s+before\s+publishing\.?",
    )
    for pattern in warning_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove leading/trailing separator noise left behind after label removal.
    text = re.sub(r"^[\s:;,.—–-]+|[\s:;—–-]+$", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    return text.strip()


def _safe_answer_fallback(question: dict, phone: str = "") -> str:
    """Return a concise, honest fallback when the model gives no usable answer."""
    text = str(question.get("question_text") or "").lower()
    if any(term in text for term in ("price", "pricing", "rate", "fee", "cost", "menu", "package", "membership")):
        return "Please contact us for the current menu and itemized rates."
    if any(term in text for term in ("hour", "timing", "open", "opening", "closing")):
        return "Please contact us to confirm our current opening hours."
    if any(term in text for term in ("service", "treatment", "product", "menu item", "offering")):
        return "Please contact us for the current list of available services and offerings."
    if any(term in text for term in ("facility", "amenity", "equipment")):
        return "Please contact us to confirm which facilities are currently available."
    if phone:
        return f"Please contact us at {phone} for the latest details."
    return "Please contact the business for the latest confirmed details."


def _generate_professional_initial_answers(
    business: dict,
    questions: list[dict],
) -> list[dict]:
    """Generate a dedicated, business-aware answer draft for every question.

    This is intentionally a separate AI pass from question generation: the
    model can analyze the complete questionnaire and business profile before
    composing useful, coherent answers (especially service and rate lists).
    """
    business_context = {
        "business_name": business.get("business_name", ""),
        "business_type": business.get("business_type", ""),
        "about_business": business.get("about_business", ""),
        "year_established": business.get("year_established", ""),
        "owner_name": business.get("owner_name", ""),
        "phone_number": business.get("phone_number", ""),
        "staff_members": business.get("staff_members", []),
    }
    question_context = [
        {
            "question_key": q["question_key"],
            "question_text": q["question_text"],
            "helper_text": q.get("helper_text", ""),
        }
        for q in questions
    ]
    prompt = f"""
{PROFESSIONAL_ANSWER_PROMPT}

BUSINESS PROFILE (source facts; do not alter these facts):
{json.dumps(business_context, ensure_ascii=False, indent=2, default=str)}

QUESTIONS TO ANSWER:
{json.dumps(question_context, ensure_ascii=False, indent=2)}

Create a genuinely useful, editable showcase draft for every question.
Prioritize menu items, services, facilities, products, packages, and rates.
For missing menus/rate cards, create plausible category-specific indicative
suggestions rather than returning contact-only text. Use INR when no currency
or location is supplied. Clearly distinguish suggestions from confirmed facts
using needs_owner_confirmation=true internally; do not append warning text. Keep all answers
point-to-point and omit filler. Never imply an estimate is an official price.
"""
    data = _generate_json(
        prompt,
        temperature=0.55,
        max_output_tokens=7000,
    )
    raw_answers = data.get("answers")
    if not isinstance(raw_answers, list):
        raise RuntimeError("AI did not return professional website answers.")

    by_key: dict[str, dict] = {}
    for item in raw_answers:
        if isinstance(item, dict):
            key = str(item.get("question_key", "")).strip()
            if key:
                by_key[key] = item

    # Repair pass: a showcase pricing/menu answer without any itemized numeric
    # prices is not useful enough. Ask the model specifically for the missing
    # rate cards instead of silently accepting a contact-only answer.
    pricing_terms = ("price", "pricing", "rate", "fee", "cost", "menu", "package", "membership", "tariff")
    priced_answers = {}
    missing_priced_questions = []
    for question in questions:
        qtext = str(question.get("question_text") or "").lower()
        if not any(term in qtext for term in pricing_terms):
            continue
        item = by_key.get(question["question_key"], {})
        candidate = _clean_initial_answer(str(item.get("answer_text") or ""))
        # Treat explicit enquiry-only pricing as valid only when the business
        # profile itself says rates are enquiry-based/not published.
        profile_text = " ".join(str(business.get(k) or "") for k in ("about_business", "business_type")).lower()
        explicitly_unpublished = any(token in profile_text for token in ("prices on enquiry", "pricing on request", "rates on request", "price list not published", "enquiry-based pricing"))
        has_price = bool(re.search(r"(?:₹|\bINR\b|\bRs\.?\s*)\s*\d|\b\d{2,}(?:\s*[-–to]+\s*\d{2,})?\s*(?:₹|INR|Rs\.?)?", candidate, flags=re.IGNORECASE))
        if has_price or explicitly_unpublished:
            priced_answers[question["question_key"]] = item
        else:
            missing_priced_questions.append(question)

    if missing_priced_questions:
        repair_prompt = f"""
You are preparing concise, point-to-point content for a digital business showcase.
Business profile (confirmed facts):
{json.dumps(business_context, ensure_ascii=False, indent=2, default=str)}

Create ONLY the missing menu/rate/package answers listed below:
{json.dumps([{ "question_key": q["question_key"], "question_text": q["question_text"], "helper_text": q.get("helper_text", "") } for q in missing_priced_questions], ensure_ascii=False, indent=2)}

Requirements:
- Do NOT answer with only "contact us for prices".
- For a menu question, provide 6-10 relevant menu items, grouped into concise categories, with realistic indicative INR prices when currency/location is not supplied.
- For rate/service/package/membership questions, provide 5-8 relevant itemized entries or tiers with realistic indicative prices/ranges, appropriate to this business category. Use broad ranges for regulated professional/medical services.
- Never claim suggested prices are official. Do not append any warning or disclaimer sentence to answer_text.
- Use confirmed profile details where available; do not invent brands, credentials, official policies, or unrelated offerings.
- Format as short bullets, ideally "Item — ₹price". No introductions, filler, slogans, or paragraphs explaining the AI.
- Return valid JSON only: {{"answers":[{{"question_key":"exact key","answer_text":"...","needs_owner_confirmation":true}}]}}
"""
        try:
            repair_data = _generate_json(repair_prompt, temperature=0.35, max_output_tokens=4500)
            repaired = repair_data.get("answers", [])
            if isinstance(repaired, list):
                for item in repaired:
                    if isinstance(item, dict) and item.get("question_key"):
                        key = str(item["question_key"]).strip()
                        if key in {q["question_key"] for q in missing_priced_questions}:
                            by_key[key] = item
        except Exception:
            logger.exception("Showcase answer rate-card repair pass failed; retaining first-pass answers.")

    phone = str(business.get("phone_number") or "").strip()
    for question in questions:
        item = by_key.get(question["question_key"], {})
        answer = str(item.get("answer_text") or "").strip()

        answer = _clean_initial_answer(answer)
        if not answer:
            answer = _safe_answer_fallback(question, phone)

        question["initial_answer"] = answer[:10000]
    return questions

def generate_website_questions(business: dict) -> list[dict]:
    prompt = f"""
{WEBSITE_QUESTION_PROMPT}

BUSINESS:
Name: {business.get("business_name", "")}
Type: {business.get("business_type", "")}
About: {business.get("about_business", "")}
Established: {business.get("year_established", "")}
Owner name: {business.get("owner_name", "")}
Business phone number: {business.get("phone_number", "")}
Saved staff members and roles:
{json.dumps(business.get("staff_members", []), ensure_ascii=False)}

Create the questionnaire and editable initial answers specifically for this business.
The initial answers are starter content only. Do not present missing facts as known.
"""

    data = _generate_json(
        prompt,
        temperature=0.9,
        max_output_tokens=3000,
    )

    questions = data.get("questions")

    if not isinstance(questions, list):
        raise RuntimeError(
            "AI did not return website questions."
        )

    normalized = []

    for index, item in enumerate(
        questions[:12],
        start=1,
    ):
        if not isinstance(item, dict):
            continue

        text = str(
            item.get("question_text", "")
        ).strip()

        if not text:
            continue

        key = str(
            item.get(
                "question_key",
                f"question_{index}",
            )
        ).strip() or f"question_{index}"

        initial_answer = str(
            item.get("initial_answer", "")
        ).strip()[:10000]

        # Never leave the textarea with only a placeholder. If the model omits
        # starter copy, provide truthful contact-based text using known details.
        initial_answer = _clean_initial_answer(initial_answer)
        if (
            not initial_answer
            or initial_answer.lower().startswith(("example:", "e.g.", "eg."))
            or "[" in initial_answer
            or "]" in initial_answer
        ):
            initial_answer = _safe_answer_fallback(item, str(business.get("phone_number") or "").strip())

        normalized.append(
            {
                "question_order": index,
                "question_key": key[:100],
                "question_text": text[:1000],
                "input_type": "textarea",
                "required": bool(
                    item.get("required", True)
                ),
                "placeholder": str(
                    item.get("placeholder", "")
                ).strip()[:500],
                "helper_text": str(
                    item.get("helper_text", "")
                ).strip()[:500],
                "initial_answer": initial_answer,
            }
        )

    if len(normalized) < 5:
        raise RuntimeError(
            "AI generated too few useful website questions."
        )

    # Second AI pass: draft concise answers grounded in the business profile.
    # Missing facts and prices must not be fabricated.
    return _generate_professional_initial_answers(business, normalized)


def _format_answers(answers: list[dict]) -> str:
    parts = []

    for index, item in enumerate(
        answers,
        start=1,
    ):
        question = str(
            item.get("question", "")
        ).strip()

        answer = str(
            item.get("answer", "")
        ).strip()

        if not question or not answer:
            continue

        parts.append(
            f"QUESTION {index}:\n"
            f"{question}\n\n"
            f"OWNER ANSWER:\n"
            f"{answer}"
        )

    return "\n\n".join(parts)



WEBSITE_IMAGE_QUERY_PROMPT = """
You are an expert commercial visual art director creating imagery for a
customer-facing business facility, services, menu, and rate-card showcase.

The goal is NOT to make a generic corporate website or fill a page with stock
photography. Select real photographic subjects that help customers understand
what the business offers and what they can expect to see, use, buy, eat, book,
or experience.

VISUAL PRIORITIES

1. FACILITIES / AMENITIES:
Search for relevant equipment, rooms, counters, treatment areas, seating,
machines, tools, fixtures, amenities, or other physical facilities when
supported by the business information.

2. PRODUCTS / MENU / CATALOG:
For restaurants, food businesses, retail, salons, clinics, and similar
businesses, prioritize relevant products, dishes, ingredients, tools,
materials, or service details. Never invent a specific branded item.

3. SERVICES / TREATMENTS:
Use visual details of the actual service environment, instruments, equipment,
materials, or treatment setup when supported. Prefer concrete detail shots over
generic smiling-person stock photos.

4. RATE / PACKAGE PRESENTATION:
Do not search for generic money, price-tag, or currency stock photos. Pricing
should be represented through clean typography, tables, cards, or badges in
HTML. Images should support the actual offering instead.

5. HERO / ENVIRONMENT:
Use one broader environment image only when it materially helps customers
understand the business. Do not default to a generic building exterior.

CATEGORY EXAMPLES

DENTAL / MEDICAL:
dental chair, treatment room detail, dental instruments, relevant equipment,
sterile clinical setup, treatment detail.

RESTAURANT / CAFE:
signature-style food, menu-relevant dish category, ingredients, tableware,
serving details, coffee/food preparation details.

SALON / SPA:
professional tools, treatment setup, styling equipment, clean salon detail,
beauty products when supplied.

GYM:
strength equipment, cardio machines, training accessories, facility details.

HOTEL / RESORT:
room details, amenities, dining setup, bathroom details, hospitality spaces.

RETAIL / FASHION:
product details, fabrics, accessories, display details, relevant merchandise.

OTHER BUSINESSES:
Identify the most recognizable physical objects, products, tools, materials,
equipment, facilities, or visual details associated with the supplied business.

IMAGE STRATEGY
- Return 3 to 5 image queries.
- Use different visual roles rather than five similar photos.
- Prefer 2 to 4 facility/product/detail images and at most 1 broader environment image.
- Do not invent a specific product, dish, treatment, facility, or brand unsupported by the supplied information.
- Generic category-level visuals are allowed when they are inherent to the business.
- Choose orientation deliberately: landscape for hero/environment, portrait for
  product/detail compositions, square for compact showcase cards.
- The purpose must be hero, section, or supporting.
- Queries must be concrete enough for Unsplash search.

Return ONLY valid JSON:
{
  "image_queries": [
    {
      "query": "specific search query",
      "purpose": "hero",
      "orientation": "landscape",
      "visual_role": "short description"
    }
  ]
}
"""


def generate_website_image_queries(
    business: dict,
    answers: list[dict],
) -> list[dict]:
    """
    Generate a business-specific visual plan before searching Unsplash.
    """

    answers_text = _format_answers(answers)

    prompt = f"""
{WEBSITE_IMAGE_QUERY_PROMPT}

BUSINESS INFORMATION

Business name:
{business.get("business_name", "")}

Business type:
{business.get("business_type", "")}

About business:
{business.get("about_business", "")}

Year established:
{business.get("year_established", "")}

OWNER-PROVIDED WEBSITE INFORMATION

{answers_text}

Now create the visual image-search plan.

Think like a professional commercial art director:
choose images that can become part of the composition, not a gallery of
generic stock photos.

Prioritize real physical details, products, tools, instruments, materials,
ingredients, equipment, and other recognizable visual elements of this
business.

Return only the JSON object.
"""

    data = _generate_json(
        prompt,
        temperature=0.85,
        max_output_tokens=2500,
    )

    queries = data.get("image_queries")

    if not isinstance(queries, list):
        raise RuntimeError(
            "AI did not return website image queries."
        )

    normalized = []

    for item in queries[:5]:
        if not isinstance(item, dict):
            continue

        query = str(
            item.get("query", "")
        ).strip()

        if not query:
            continue

        purpose = str(
            item.get("purpose", "section")
        ).strip().lower()

        if purpose not in {
            "hero",
            "section",
            "supporting",
        }:
            purpose = "section"

        orientation = str(
            item.get("orientation", "landscape")
        ).strip().lower()

        if orientation not in {
            "landscape",
            "portrait",
            "square",
        }:
            orientation = "landscape"

        visual_role = str(
            item.get("visual_role", "")
        ).strip()

        normalized.append(
            {
                "query": query[:500],
                "purpose": purpose,
                "orientation": orientation,
                "visual_role": visual_role[:300],
            }
        )

    if len(normalized) < 2:
        raise RuntimeError(
            "AI generated too few useful website image queries."
        )

    return normalized


def _format_image_assets(
    image_assets: list[dict] | None,
) -> str:
    """
    Format backend-selected Unsplash assets for the HTML-generation prompt.
    """

    if not image_assets:
        return "No real image assets were found. Use CSS/SVG artwork instead."

    lines = []

    for index, asset in enumerate(
        image_assets,
        start=1,
    ):
        lines.append(
            f"""
IMAGE ASSET {index}
Provider: {asset.get("provider", "unsplash")}
Image URL: {asset.get("image_url", "")}
Source URL: {asset.get("source_url", "")}
Photographer: {asset.get("photographer", "")}
Photographer URL: {asset.get("photographer_url", "")}
Search query: {asset.get("query", "")}
Purpose: {asset.get("purpose", "section")}
Visual role: {asset.get("visual_role", "")}
Width: {asset.get("width", 0)}
Height: {asset.get("height", 0)}
""".strip()
        )

    return "\n\n".join(lines)



def _clean_generated_html(html: str) -> str:
    cleaned = (html or "").strip()

    cleaned = re.sub(
        r"^```(?:html)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    start = cleaned.lower().find("<!doctype")
    if start == -1:
        start = cleaned.lower().find("<html")

    if start > 0:
        cleaned = cleaned[start:]

    return cleaned.strip()

def _validate_in_page_links(html: str) -> None:
    """Reject only genuinely broken in-page anchor links."""
    ids = {
        value
        for value in re.findall(
            r'\bid\s*=\s*["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )
    }

    for target in re.findall(
        r'\bhref\s*=\s*["\']#([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    ):
        if target and target not in ids:
            raise RuntimeError(
                f"AI generated an in-page link to missing section '#{target}'."
            )


def _validate_html(html: str) -> str:
    cleaned = _clean_generated_html(html)

    if len(cleaned) < 1000:
        raise RuntimeError(
            "AI generated website code is too short."
        )

    lower = cleaned.lower()

    if "<html" not in lower:
        raise RuntimeError(
            "AI did not generate a complete HTML document."
        )

    if "<style" not in lower:
        raise RuntimeError(
            "AI website does not contain CSS."
        )

    if "<meta" not in lower or "viewport" not in lower:
        raise RuntimeError(
            "AI website is missing the mobile viewport."
        )

    # The site is rendered inside a sandboxed iframe.
    # Do not allow dangerous document-level embedding behavior.
    cleaned = re.sub(
        r"<base\b[^>]*>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Never allow generated navigation code to replace the iframe document.
    forbidden_navigation = re.search(
        r"(?:window\.location|location\.(?:href|assign|replace)|document\.write|<meta[^>]+http-equiv\s*=\s*[\"']?refresh)",
        cleaned,
        flags=re.IGNORECASE,
    )

    if forbidden_navigation:
        raise RuntimeError(
            "AI generated unsafe document-navigation code. Please regenerate the website."
        )

    # Reject relative document-navigation links that can replace the iframe
    # page when a customer taps a menu item. Safe navigation is limited to
    # in-page anchors, explicit contact links, and explicitly supplied URLs.
    unsafe_href = re.search(
        r"href\s*=\s*[\"'](?:/|\./|\.\./|index\.html(?:[?#]|\"|'))",
        cleaned,
        flags=re.IGNORECASE,
    )

    if unsafe_href:
        raise RuntimeError(
            "AI generated a relative page-navigation link. Please regenerate the website."
        )

    # Reject common placeholder / invented image sources.
    placeholder_image = re.search(
        r'<img\b[^>]+src\s*=\s*["\'](?:https?://)?(?:'
        r'placehold\.co|placehold\.it|placeholder\.com|'
        r'via\.placeholder\.com|dummyimage\.com)',
        cleaned,
        flags=re.IGNORECASE,
    )

    if placeholder_image:
        raise RuntimeError(
            "AI generated a placeholder image source."
        )

    # Generated websites may only use image URLs that were supplied by the
    # backend when image assets are available. The stricter exact-URL check
    # is performed in generate_website_html().

    # Defensive interaction layer. It does not impose a visual template.
    interaction_script = """<script>
(function () {
  "use strict";

  function closeMenus(except) {
    document.querySelectorAll('[aria-expanded="true"]').forEach(function (button) {
      if (except && button === except) return;
      button.setAttribute("aria-expanded", "false");
      var controlledId = button.getAttribute("aria-controls");
      if (!controlledId) return;
      var panel = document.getElementById(controlledId);
      if (panel) {
        panel.hidden = true;
        panel.classList.remove("is-open", "open", "active");
      }
    });
  }

  document.querySelectorAll("[aria-controls]").forEach(function (button) {
    var controlledId = button.getAttribute("aria-controls");
    var panel = document.getElementById(controlledId);
    if (!panel) return;

    var isExpanded = button.getAttribute("aria-expanded") === "true";
    panel.hidden = !isExpanded;

    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      var open = button.getAttribute("aria-expanded") === "true";
      closeMenus(button);
      button.setAttribute("aria-expanded", String(!open));
      panel.hidden = open;
      panel.classList.toggle("is-open", !open);
      panel.classList.toggle("open", !open);
      panel.classList.toggle("active", !open);
    });
  });

  document.querySelectorAll("[data-dropdown-toggle]").forEach(function (button) {
    var targetId = button.getAttribute("data-dropdown-toggle");
    var panel = document.getElementById(targetId);
    if (!panel) return;

    button.setAttribute("aria-expanded", button.getAttribute("aria-expanded") === "true" ? "true" : "false");
    panel.hidden = button.getAttribute("aria-expanded") !== "true";

    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      var open = button.getAttribute("aria-expanded") === "true";
      closeMenus(button);
      button.setAttribute("aria-expanded", String(!open));
      panel.hidden = open;
      panel.classList.toggle("is-open", !open);
      panel.classList.toggle("open", !open);
      panel.classList.toggle("active", !open);
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest("[aria-controls], [data-dropdown-toggle]")) {
      closeMenus();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeMenus();
  });

  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener("click", function (event) {
      var href = link.getAttribute("href");
      if (!href || href === "#") return;
      var target = document.querySelector(href);
      if (!target) return;
      event.preventDefault();
      closeMenus();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  document.querySelectorAll("[aria-controls], [data-dropdown-toggle]").forEach(function (button) {
    button.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        button.click();
      }
    });
  });
})();
</script>"""

    if re.search(r"</body>\s*</html>\s*$", cleaned, flags=re.IGNORECASE):
        cleaned = re.sub(
            r"</body>",
            interaction_script + "\n</body>",
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        cleaned += "\n" + interaction_script

    return cleaned


SHOWCASE_ART_DIRECTION_PROMPT = """
You are a senior commercial showcase art director and information architect.
Your first job is to think like a customer looking at a business's digital
showcase, not like a web agency building a conventional website.

The product is a DIGITAL SHOWCASE for displaying a business's actual:
- menu items and food/drink options
- services, treatments, and facilities
- product catalogue and product variants
- price list, rate card, packages, and memberships
- amenities, equipment, included features, and customer options
- important conditions and practical visit/enquiry information

Analyze the business profile and owner answers together. Choose the showcase
format, content hierarchy, visual style, and interaction pattern that best fit
this specific business. A restaurant should feel like a premium menu; a clinic
like a treatment and fee guide; a salon like a service menu and price board; a
gym like a facilities and membership guide; a hotel like an amenities, room,
and package showcase; a retailer like a browsable product catalogue. Do not
force these examples onto unrelated businesses.

Return a concise JSON design brief with:
{
  "showcase_type": "short description of the most suitable showcase format",
  "customer_priority": "what customers most need to see first",
  "visual_direction": "specific art direction, mood, typography and composition",
  "palette_direction": "business-appropriate color direction",
  "content_hierarchy": ["ordered section labels based on available information"],
  "presentation_patterns": ["specific UI patterns suited to the content"],
  "important_content": ["specific information from the answers that deserves prominence"],
  "avoid": ["design mistakes to avoid for this business"]
}

Rules:
- The design brief must be grounded in business_info and the owner answers.
- Never add services, menu items, facilities, packages, prices, or policies.
- If owner answers contain clearly marked AI-suggested draft rates/items, treat
  them as unconfirmed draft content. Preserve their draft labels and do not
  imply they are official until the owner confirms them.
- Prioritize useful information over marketing copy.
- Avoid generic hero sections, generic testimonials, fabricated ratings,
  fake stats, empty slogans, and standard corporate-site layouts.
- Do not include any HTML or CSS in this design brief.
- Return valid JSON only.
"""

WEBSITE_HTML_PROMPT = """
You are a senior award-winning web designer, visual art director,
commercial showcase designer, UX designer, and front-end engineer.

Create ONE complete, production-quality, customer-facing business showcase
as a SINGLE self-contained HTML document.

IMPORTANT PRODUCT DEFINITION

This is NOT a conventional company website, corporate website, portfolio,
landing page, or generic business website.

It is a practical CUSTOMER SHOWCASE: a digital display/menu/catalog that lets
a business owner present what customers can see, use, buy, eat, book, choose,
or compare.

The primary content should therefore be drawn from the supplied owner answers
and organized around the business's real offerings.

CORE SHOWCASE CONTENT

Depending on the business, naturally prioritize the sections that are actually
supported by the supplied information:

- Facilities / Amenities
- Services / Treatments
- Menu / Product Catalog
- Rate List / Pricing
- Packages / Plans
- Products / Specialties
- What's Included / Options
- Visit / Booking Information
- Location / Contact

Do NOT force every section into every business. If a business does not have a
menu, do not create a fake menu. If prices are not supplied, do not invent them.
If facilities are not supplied, do not invent facilities. Build around what is
actually available.

The page should feel like a premium digital brochure, menu, facility board,
service catalog, or rate-card experience rather than a marketing-heavy website.

BUSINESS-SPECIFIC FEEL

A restaurant should feel like an elegant digital menu and dining showcase.
A dental clinic should feel like a clean treatment/facility/service showcase.
A salon should feel like a service + facility + rate-card showcase.
A gym should feel like a facilities + membership + program showcase.
A hotel should feel like an amenities + rooms + experiences + rates showcase.
A retail store should feel like a product catalog/showroom.
Other businesses should receive the most natural customer-showcase format.

==================================================
CUSTOMER EXPERIENCE
==================================================

A customer should be able to understand within seconds:
1. What this business offers.
2. What facilities, products, services, menu items, or packages are available.
3. What options or rates are available when supplied.
4. How the offerings are organized.
5. How to contact, visit, or enquire when that information is supplied.

Use clear labels, short descriptions, visual grouping, and scannable pricing.
Avoid long marketing paragraphs.

==================================================
MOBILE FIRST
==================================================

MOBILE FIRST IS MANDATORY.

Design for 360px to 430px first:
- thumb-friendly controls
- large readable typography
- no horizontal scrolling
- compact but comfortable cards
- sticky/mobile navigation when appropriate
- vertically scannable menu/rate lists
- touch-friendly interactions
- responsive desktop/tablet enhancement

==================================================
SHOWCASE DESIGN SYSTEM
==================================================

Choose a composition appropriate to the business. Do not mechanically reuse a
fixed template.

Possible visual patterns include, where appropriate:
- menu-style categorized lists
- elegant rate tables
- facility tiles
- service cards
- product cards
- package comparison blocks
- icon-led amenity lists
- editorial image + information layouts
- compact specification rows
- category tabs or accordions
- visual feature strips
- sticky section navigation

Pricing and rate information must be especially easy to scan. When prices are
provided, show the exact supplied values clearly and consistently. Never alter
or embellish owner-provided prices.

Use tasteful CSS/SVG icons for facilities, categories, and small visual cues.
Do not depend on icon libraries or external scripts.

==================================================
VISUAL QUALITY
==================================================

The result must look like a professional commercial digital showcase:
- premium
- modern
- distinctive
- clean
- highly scannable
- strong hierarchy
- refined spacing
- category-appropriate typography
- intentional image placement
- restrained decoration
- subtle motion where useful

Avoid:
- generic SaaS dashboard styling
- corporate-template appearance
- huge marketing hero sections that push useful information below the fold
- excessive gradients
- childish UI
- repetitive card grids
- fake testimonials/reviews
- fake statistics
- unnecessary decorative noise
- giant paragraphs

The useful customer information should remain visually dominant.

==================================================
IMAGES
==================================================

Use ONLY the real image assets supplied by the backend.

Do NOT:
- invent image URLs
- search the web from JavaScript
- call Unsplash from the generated website
- use another image provider
- use random remote images
- use placeholder.com
- use broken image URLs
- use data URLs for external images
- use base64 image data

When images are supplied, choose them according to their stated purpose and
visual role. Use at least 2 different supplied images when the content supports
it, but do not turn the showcase into a gallery.

Prefer images that explain the business: facilities, products, dishes,
equipment, tools, materials, treatment environments, or other real details.

If an image is not useful for a particular section, use CSS/SVG instead.

Unsplash attribution metadata supplied by the backend should be included in a
small tasteful footer/credit area without distracting from the showcase.

==================================================
FACTUAL ACCURACY — ABSOLUTE RULE
==================================================

Use ONLY:
1. supplied business_info
2. supplied owner answers
3. supplied image metadata for image credits

NEVER invent:
- prices or rates
- menu items
- products
- services
- treatments
- facilities
- amenities
- doctors/staff
- opening hours
- address
- phone/email
- ratings/reviews
- awards
- guarantees
- statistics
- discounts
- package contents
- policies

If information is missing, simply do not show that information.
Do not create fake content to fill space.
Do not repeat the same information across multiple sections.

==================================================
FUNCTIONALITY
==================================================

FUNCTIONALITY IS MANDATORY:
- Every visible button must have a real purpose.
- Navigation must stay inside the generated document.
- Use safe in-page anchors such as #facilities, #services, #menu, #rates,
  #contact only when those sections exist.
- Never use href="/", href="./", href="index.html", or other document-changing links.
- Never use window.location, location.href, location.assign, location.replace,
  document.write, meta refresh, or redirects.
- Mobile menu buttons must only open/close the menu.
- Accordions/dropdowns must expand/collapse correctly and close on Escape or
  outside click where appropriate.
- Internal anchor links should smoothly scroll without replacing the document.
- Contact buttons may use tel: or mailto: ONLY when explicitly supplied.
- External URLs may be used only when explicitly supplied by the owner and must
  open safely in a new tab.
- All controls need accessible labels and correct ARIA state.
- The showcase must remain usable without JavaScript.
- Use only small self-contained vanilla JavaScript when interaction is genuinely needed.
- No backend calls.
- No API calls.
- No fake submission forms.
- No external scripts.
- No React.
- No Tailwind.
- No Bootstrap.
- No JavaScript frameworks.

==================================================
TECHNICAL OUTPUT
==================================================

Return ONLY the complete HTML document.
No markdown fences.
No explanation before or after it.

The document MUST contain:
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>...</style>
</head>
<body>...</body>
</html>

Use semantic HTML and accessible labels.

==================================================
FINAL DESIGN DECISION
==================================================

You are responsible for choosing the right:
- showcase format
- section hierarchy
- menu/rate-list presentation
- typography
- colors
- image placement and crop
- card/list treatment
- navigation
- decorative treatment
- interaction pattern

Do NOT mechanically follow a fixed template.
Build this as a custom customer-facing showcase for this exact business.
"""

def _normalize_contact_phone(phone_number: str) -> tuple[str, str]:
    """
    Return (tel_uri, whatsapp_digits).
    Ten-digit Indian numbers are normalized to country code 91.
    Numbers already containing an international prefix retain it.
    """
    raw = str(phone_number or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return "", ""

    if raw.startswith("+"):
        international_digits = digits
    elif len(digits) == 10:
        international_digits = "91" + digits
    elif len(digits) == 11 and digits.startswith("0"):
        international_digits = "91" + digits[1:]
    elif len(digits) == 12 and digits.startswith("91"):
        international_digits = digits
    else:
        # Preserve numbers that already appear to include a country code.
        international_digits = digits

    tel_uri = "+" + international_digits
    return tel_uri, international_digits


def _inject_contact_actions(html_document: str, business: dict) -> str:
    """
    Add reliable Call and WhatsApp actions independently of AI output.
    The action bar is responsive, accessible, and only shown when a phone
    number is available in the saved business profile.
    """
    if 'id="vg-contact-actions"' in html_document:
        return html_document

    phone = str(business.get("phone_number") or "").strip()
    tel_uri, whatsapp_digits = _normalize_contact_phone(phone)
    if not tel_uri or not whatsapp_digits:
        return html_document

    business_name = html_lib.escape(
        str(business.get("business_name") or "our business").strip(),
        quote=True,
    )
    message = quote(
        f"Hello {str(business.get('business_name') or 'there').strip()}, I found your website and would like to know more about your services."
    )
    tel_href = html_lib.escape(tel_uri, quote=True)
    wa_href = f"https://wa.me/{whatsapp_digits}?text={message}"

    contact_markup = f"""
<div id="vg-contact-actions" class="vg-contact-actions" aria-label="Contact {business_name}">
  <a class="vg-contact-action vg-contact-call" href="tel:{tel_href}" aria-label="Call {business_name}">
    <span class="vg-contact-action-icon" aria-hidden="true">☎</span>
    <span>Call Now</span>
  </a>
  <a class="vg-contact-action vg-contact-whatsapp" href="{wa_href}" target="_blank" rel="noopener noreferrer" aria-label="Message {business_name} on WhatsApp">
    <span class="vg-contact-action-icon" aria-hidden="true">✆</span>
    <span>WhatsApp</span>
  </a>
</div>
"""
    contact_styles = """
<style id="vg-contact-actions-styles">
  *, *::before, *::after { box-sizing: border-box; }
  html { width: 100%; max-width: 100%; overflow-x: clip; scroll-behavior: smooth; }
  body { max-width: 100%; overflow-x: clip; }
  img, video, iframe, svg { max-width: 100%; }
  #vg-contact-actions.vg-contact-actions {
    position: fixed;
    z-index: 2147483000;
    right: max(22px, env(safe-area-inset-right));
    bottom: max(22px, env(safe-area-inset-bottom));
    display: flex;
    align-items: center;
    gap: 10px;
    max-width: calc(100vw - 32px);
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  #vg-contact-actions .vg-contact-action {
    min-height: 48px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 9px;
    padding: 12px 18px;
    border: 1px solid rgba(255,255,255,.18);
    border-radius: 999px;
    box-shadow: 0 8px 24px rgba(15,23,42,.20);
    color: #fff !important;
    text-decoration: none !important;
    font-size: 14px;
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap;
    -webkit-tap-highlight-color: transparent;
    transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
  }
  #vg-contact-actions .vg-contact-action:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(15,23,42,.24);
    filter: brightness(1.04);
  }
  #vg-contact-actions .vg-contact-action:focus-visible {
    outline: 3px solid #111827;
    outline-offset: 3px;
  }
  #vg-contact-actions .vg-contact-call { background: #172033; }
  #vg-contact-actions .vg-contact-whatsapp { background: #16834a; }
  #vg-contact-actions .vg-contact-action-icon { font-size: 17px; line-height: 1; }
  @media (max-width: 640px) {
    body { padding-bottom: calc(82px + env(safe-area-inset-bottom)) !important; }
    #vg-contact-actions.vg-contact-actions {
      right: 0;
      bottom: 0;
      left: 0;
      width: 100%;
      max-width: none;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 10px;
      padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
      background: rgba(255,255,255,.96);
      border-top: 1px solid rgba(15,23,42,.10);
      box-shadow: 0 -6px 24px rgba(15,23,42,.08);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
    }
    #vg-contact-actions .vg-contact-action {
      width: 100%;
      min-width: 0;
      min-height: 48px;
      padding: 12px 8px;
      border-radius: 13px;
      font-size: 14px;
      gap: 7px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    #vg-contact-actions .vg-contact-action { transition: none; }
  }
</style>
"""
    if re.search(r"</head\s*>", html_document, flags=re.IGNORECASE):
        html_document = re.sub(
            r"</head\s*>",
            contact_styles + "\n</head>",
            html_document,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        html_document = contact_styles + html_document

    if re.search(r"</body\s*>", html_document, flags=re.IGNORECASE):
        html_document = re.sub(
            r"</body\s*>",
            contact_markup + "\n</body>",
            html_document,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        html_document += contact_markup

    return html_document




def generate_website_html(
    business: dict,
    answers: list[dict],
    image_assets: list[dict] | None = None,
    color_theme_1: str | None = None,
    color_theme_2: str | None = None,
) -> str:
    """
    Generate the showcase using the earlier proven HTML architecture prompt.
    The answer-generation layer supplies the content; this layer controls its
    visual hierarchy, responsive presentation, and interactions.
    """
    answers_text = _format_answers(answers)
    if not answers_text:
        raise RuntimeError("No valid website answers were provided.")

    image_assets_text = _format_image_assets(image_assets)

    color_1 = str(color_theme_1 or "").strip() or "AI CHOICE"
    color_2 = str(color_theme_2 or "").strip() or "AI CHOICE"

    if color_1 == "AI CHOICE" and color_2 == "AI CHOICE":
        color_direction = (
            "No colors were selected by the owner. Choose both primary and "
            "secondary brand colors yourself based on the business category."
        )
    elif color_1 == "AI CHOICE":
        color_direction = (
            f"Owner selected secondary/theme color: {color_2}. Choose a "
            "compatible primary color that creates a polished, accessible palette."
        )
    elif color_2 == "AI CHOICE":
        color_direction = (
            f"Owner selected primary/theme color: {color_1}. Choose a "
            "compatible secondary color that creates a polished, accessible palette."
        )
    else:
        color_direction = (
            f"Owner explicitly selected the two theme colors: {color_1} and {color_2}. "
            "Use these exact colors as the core brand palette. Do not replace them."
        )

    prompt = f"""
{WEBSITE_HTML_PROMPT}

RESTORED SHOWCASE ARCHITECTURE — IMPORTANT
Use the strong visual architecture and category-specific composition described
above. Do not simplify this into a generic template or plain list of cards.

FACILITY SHOWCASE PRIORITY
If the supplied answers contain facilities, amenities, equipment, rooms,
treatment areas, or customer-use features:
- Create a clearly visible, dedicated Facilities / Amenities section.
- Place it among the first major content sections, not hidden at the bottom.
- Use an appropriate visual treatment such as icon-led facility tiles,
  editorial image-and-detail blocks, grouped amenity panels, or a refined
  facility grid.
- Give each facility a concise label and only the detail present in the answers.
- Do not omit facility entries or merge unrelated facilities into vague text.
- Use supplied images as visual support for relevant facility groups.
If no facility information exists in the answers, do not fabricate a section.

OFFERING AND PRICING PRIORITY
- Put the actual services, menu, products, packages, and rate information
  before lengthy introductory/about content.
- Preserve all supplied list items and their prices.
- Convert point-to-point answers into purposeful visual sections, not walls
  of text and not one repetitive card style.
- Keep menu/rate lists scannable, with names and prices visually aligned.
- Never replace supplied answer content with generic marketing copy.

COLOR THEME DIRECTION
{color_direction}

BUSINESS INFORMATION
Business name: {business.get("business_name", "")}
Business type: {business.get("business_type", "")}
About business: {business.get("about_business", "")}
Year established: {business.get("year_established", "")}
Business phone number: {business.get("phone_number", "")}

OWNER-PROVIDED WEBSITE INFORMATION
{answers_text}

REAL IMAGE ASSETS SELECTED BY THE BACKEND
{image_assets_text}

IMAGE COMPOSITION
Use supplied images intentionally and selectively. Prefer facility, equipment,
product, treatment, food, or service-detail imagery where relevant. Do not use
one generic stock image as the entire visual identity. Never invent image URLs.

CONTACT CONVERSION REQUIREMENTS
The backend injects Call Now and WhatsApp controls using the saved business
phone number. Do not invent contact details. Reserve enough space so these
controls do not obscure the showcase.

Return ONLY a complete HTML document. Prioritize mobile first and ensure the
facility, service, menu, product, package, and rate content remains easy to scan.
"""

    last_validation_error = None
    cleaned = ""

    for attempt in range(2):
        generation_prompt = prompt
        if attempt == 1:
            generation_prompt += (
                "\n\nRETRY: The previous HTML failed validation because: "
                f"{last_validation_error}. Return a complete corrected document "
                "from <!doctype html> through </html>. Keep all showcase sections, "
                "especially Facilities / Amenities when present in the answers. "
                "Ensure all in-page anchors exist and all CSS is self-contained."
            )

        generated_html = _generate_text(
            generation_prompt,
            temperature=0.9 if attempt == 0 else 0.75,
            max_output_tokens=16000,
        )
        candidate = _clean_generated_html(generated_html)

        try:
            candidate = _validate_html(candidate)
            _validate_in_page_links(candidate)
            cleaned = candidate
            break
        except Exception as validation_error:
            last_validation_error = validation_error
            logger.warning(
                "Showcase HTML validation failed on attempt %s: %s",
                attempt + 1,
                validation_error,
            )
            if attempt == 1:
                raise RuntimeError(
                    "AI could not produce valid showcase HTML after two attempts: "
                    f"{validation_error}"
                ) from validation_error

    if not cleaned:
        raise RuntimeError("AI returned no valid showcase HTML after retry.")

    # Preserve deterministic contact actions from the current production flow.
    cleaned = _inject_contact_actions(cleaned, business)

    selected_colors = [color for color in (color_theme_1, color_theme_2) if color]
    if selected_colors:
        missing_colors = [
            color for color in selected_colors if color.lower() not in cleaned.lower()
        ]
        if missing_colors:
            theme_metadata = (
                '<style id="owner-color-theme">:root{'
                + ';'.join(
                    f'--owner-theme-{index + 1}:{color}'
                    for index, color in enumerate(selected_colors)
                )
                + '}</style>'
            )
            cleaned = re.sub(
                r"</head>",
                theme_metadata + "</head>",
                cleaned,
                count=1,
                flags=re.IGNORECASE,
            )

    return cleaned


# Backward-compatible function name.
# The new router should use generate_website_html.
def generate_website_config(
    business: dict,
    answers: list[dict],
    image_assets: list[dict] | None = None,
    color_theme_1: str | None = None,
    color_theme_2: str | None = None,
) -> dict:
    html = generate_website_html(
        business,
        answers,
        image_assets=image_assets,
        color_theme_1=color_theme_1,
        color_theme_2=color_theme_2,
    )

    return {
        "render_mode": "generated_html",
        "html": html,
    }
