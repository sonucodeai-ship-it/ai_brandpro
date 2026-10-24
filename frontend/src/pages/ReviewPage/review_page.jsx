import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./review_page.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;


// =========================================================
// GOOGLE REVIEW URL
// =========================================================




// =========================================================
// CLIPBOARD HELPER
// =========================================================

const copyTextToClipboard = async (text) => {
  const cleanText = text?.trim();

  if (!cleanText) {
    throw new Error("There is no review to copy.");
  }

  // Modern browsers
  if (
    navigator.clipboard &&
    typeof navigator.clipboard.writeText === "function"
  ) {
    await navigator.clipboard.writeText(cleanText);
    return true;
  }

  // Fallback for older browsers
  const textarea = document.createElement("textarea");

  textarea.value = cleanText;

  textarea.setAttribute("readonly", "");

  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  textarea.style.top = "0";
  textarea.style.opacity = "0";
  textarea.style.pointerEvents = "none";

  document.body.appendChild(textarea);

  textarea.focus();
  textarea.select();
  textarea.setSelectionRange(
    0,
    textarea.value.length
  );

  const copied = document.execCommand("copy");

  document.body.removeChild(textarea);

  if (!copied) {
    throw new Error("Clipboard copy failed.");
  }

  return true;
};


// =========================================================
// REVIEW PAGE
// =========================================================

function ReviewPage() {
  const location = useLocation();
  const navigate = useNavigate();


  // =======================================================
  // DYNAMIC DATA FROM DASHBOARD
  // =======================================================

  const {
    review: initialReview,
    reviewId: initialReviewId = null,
    answers: initialAnswers = [],
    dashboard: initialDashboard = null,
  } = location.state || {};

  const googleReviewUrl =
    initialDashboard?.google_review_link?.trim() || "";


  // =======================================================
  // STATE
  // =======================================================

  const [review, setReview] = useState(
    initialReview || ""
  );

  const [reviewId, setReviewId] = useState(
    initialReviewId || null
  );

  const [answers] = useState(
    Array.isArray(initialAnswers)
      ? initialAnswers
      : []
  );

  const [isEditing, setIsEditing] = useState(false);

  const [copied, setCopied] = useState(false);

  const [isRegenerating, setIsRegenerating] =
    useState(false);

  const [isOpeningGoogle, setIsOpeningGoogle] =
    useState(false);

  const [error, setError] = useState("");


  // =======================================================
  // COPIED STATE
  // =======================================================

  const showCopiedState = (
    duration = 2500
  ) => {
    setCopied(true);

    window.setTimeout(() => {
      setCopied(false);
    }, duration);
  };


  // =======================================================
  // COPY REVIEW
  // =======================================================

  const copyReviewToClipboard = async () => {
    const reviewText = review.trim();

    if (!reviewText) {
      throw new Error(
        "There is no review to copy."
      );
    }

    await copyTextToClipboard(reviewText);

    showCopiedState();
  };


  // =======================================================
  // MANUAL COPY
  // =======================================================

  const handleCopy = async () => {
    if (!review.trim()) {
      setError(
        "There is no review to copy."
      );

      return;
    }

    try {
      setError("");

      await copyReviewToClipboard();

    } catch (copyError) {
      console.error(
        "Unable to copy review:",
        copyError
      );

      setError(
        "Unable to copy the review automatically. Please copy it manually."
      );
    }
  };


  // =======================================================
  // REGENERATE REVIEW
  // =======================================================

  const handleRegenerate = async () => {
    /*
     * Regeneration requires the same answers that were
     * originally selected on the Dashboard.
     */

    if (
      isRegenerating ||
      !Array.isArray(answers) ||
      answers.length === 0
    ) {
      setError(
        "Your selected answers are not available. Please generate the review again from the Dashboard."
      );

      return;
    }

    setIsRegenerating(true);
    setError("");
    setCopied(false);

    try {
      // Customer review regeneration is intentionally public.
      // Do not require or send the business owner's authentication token.
      const response = await fetch(
        `${API_BASE_URL}/api/reviews/generate`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            answers,
            dashboard_id: initialDashboard?.dashboard_id || null,
            regenerate_status: 1,
          }),
        }
      );


      // ---------------------------------------------------
      // Parse response
      // ---------------------------------------------------

      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
          `Request failed with status ${response.status}`
        );
      }


      if (
        !data.success ||
        !data.review
      ) {
        throw new Error(
          "Invalid review response from server."
        );
      }


      // ---------------------------------------------------
      // Update displayed review
      // ---------------------------------------------------

      setReview(
        data.review
      );

      if (data.review_id) {
        setReviewId(data.review_id);
      }

      setIsEditing(false);

      setCopied(false);

    } catch (regenerateError) {
      console.error(
        "Review regeneration failed:",
        regenerateError
      );

      setError(
        regenerateError.message ||
        "Unable to regenerate the review. Please try again."
      );

    } finally {
      setIsRegenerating(false);
    }
  };


  // =======================================================
  // SAVE SUBMIT STATUS
  // =======================================================

  const saveSubmitStatus = async (status) => {
    if (!reviewId) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/reviews/${reviewId}/submit-status`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            submit_status: status,
            review_text: review.trim(),
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(
          data.detail || "Unable to save review submit status."
        );
      }
    } catch (statusError) {
      console.error(
        "Review submit status update failed:",
        statusError
      );
    }
  };


  // =======================================================
  // GOOGLE REVIEW
  // =======================================================

  const handleGoogleReview = async () => {
    const reviewText = review.trim();

    if (!reviewText) {
      setError(
        "Please generate a review before continuing to Google."
      );
      return;
    }

    if (!googleReviewUrl) {
      setError(
        "The Google Business Review link is not available. Please contact the business."
      );
      return;
    }

    if (isOpeningGoogle) {
      return;
    }

    setIsOpeningGoogle(true);
    setError("");

    /*
     * IMPORTANT:
     * Open Google synchronously from the user's click.
     * This gives the browser the best chance of allowing the popup.
     *
     * The returned window object is the only reliable signal available
     * to this application for determining whether the browser allowed
     * the Google window to open.
     */
    const googleWindow = window.open(
      googleReviewUrl,
      "_blank"
    );

    /*
     * Determine the Google hand-off status independently from clipboard
     * operations. Clipboard permission can fail even when Google opens
     * successfully, so it must never change the Google-open status.
     */
    if (!googleWindow) {
      await saveSubmitStatus(0);

      setError(
        "Google could not be opened. Please allow pop-ups and try again."
      );

      setIsOpeningGoogle(false);
      return;
    }

    /*
     * Google was successfully opened.
     *
     * IMPORTANT:
     * submit_status = 1 means the customer was successfully handed off
     * to Google. It does NOT mean that Google confirmed a review was
     * actually submitted. Google is a separate cross-origin website and
     * this application cannot verify the final submission from here.
     */
    await saveSubmitStatus(1);

    /*
     * Clipboard handling is intentionally independent from the Google
     * hand-off status. If copying fails, Google is already open and the
     * customer can still paste the review manually.
     */
    try {
      await copyTextToClipboard(reviewText);

      showCopiedState(3500);

      /*
       * We intentionally do not access or modify Google's page.
       */
      window.setTimeout(() => {
        setError("");
      }, 500);

    } catch (copyError) {
      console.error(
        "Unable to copy review automatically:",
        copyError
      );

      setError(
        "Google is open. The review could not be copied automatically. Please copy it manually and paste it into the review box."
      );
    } finally {
      setIsOpeningGoogle(false);
    }
  };


  // =======================================================
  // NO REVIEW STATE
  // =======================================================

  if (!initialReview) {
    return (
      <div className="review-generator-page review-minimal-page">
        <main className="review-minimal-container">
          <button
            type="button"
            className="review-back-button"
            aria-label="Go back"
            onClick={() => {
              const publicUrlId = initialDashboard?.public_url_id;
              if (publicUrlId) {
                navigate(`/customer-dashboard/${publicUrlId}`, { replace: true });
                return;
              }
              navigate(-1);
            }}
          >
            <span aria-hidden="true">‹</span>
          </button>
          <section className="review-minimal-card review-empty-state">
            <div className="review-google-mark" aria-label="Google">G</div>
            <h1>Review not found</h1>
            <p>Your review session could not be found. Please go back and complete your experience details.</p>
            <button
              type="button"
              className="review-primary-button"
              onClick={() => {
                const publicUrlId = initialDashboard?.public_url_id;
                if (publicUrlId) {
                  navigate(`/customer-dashboard/${publicUrlId}`, { replace: true });
                  return;
                }
                navigate(-1);
              }}
            >
              Go back
            </button>
          </section>
        </main>
      </div>
    );
  }

  // =======================================================
  // MINIMAL REVIEW PAGE
  // =======================================================

  return (
    <div className="review-generator-page review-minimal-page">
      <main className="review-minimal-container">
        <button
          type="button"
          className="review-back-button"
          aria-label="Go back"
          onClick={() => {
            const publicUrlId = initialDashboard?.public_url_id;
            if (publicUrlId) {
              navigate(`/customer-dashboard/${publicUrlId}`, { replace: true });
              return;
            }
            navigate(-1);
          }}
        >
          <span aria-hidden="true">‹</span>
        </button>

        <header className="review-minimal-header">
          <div className="review-confetti" aria-hidden="true">
            <span>✦</span><span>•</span><span>✧</span><span>✦</span>
            <span>•</span><span>✧</span><span>✦</span><span>•</span>
            <span>✧</span><span>✦</span><span>•</span><span>✧</span>
          </div>
          <h1>Your AI Review</h1>
        </header>

        {error && (
          <div className="review-minimal-error" role="alert">
            {error}
          </div>
        )}

        <section className="review-minimal-card">
          <div className="review-rating-line">
            <div className="review-google-mark" aria-label="Google">G</div>
            <div className="review-gold-stars" aria-label="5 out of 5 stars">★★★★★</div>
          </div>

          <div className={`review-minimal-text ${isEditing ? "is-editing" : ""}`}>
            {isEditing ? (
              <textarea
                value={review}
                onChange={(event) => {
                  setReview(event.target.value);
                  setCopied(false);
                  setError("");
                }}
                autoFocus
                aria-label="Edit your review"
                maxLength={1000}
              />
            ) : (
              <p>{review}</p>
            )}
          </div>

          <div className="review-minimal-meta">
            <span>{review.length}/1000</span>
          </div>
        </section>

        <div className="review-minimal-actions">
          <button
            type="button"
            className="review-google-primary"
            onClick={handleGoogleReview}
            disabled={isOpeningGoogle || !googleReviewUrl}
          >
            <span className="review-google-button-mark" aria-hidden="true">G</span>
            <span>
              {isOpeningGoogle
                ? "Opening Google..."
                : copied
                  ? "Copied — Continue to Google"
                  : googleReviewUrl
                    ? "Copy & Continue to Google"
                    : "Google Review Link Unavailable"}
            </span>
          </button>

          <div className="review-secondary-actions">
            <button
              type="button"
              className="review-regenerate-button"
              onClick={handleRegenerate}
              disabled={isRegenerating || answers.length === 0}
            >
              <span className={isRegenerating ? "spin" : ""} aria-hidden="true">↻</span>
              {isRegenerating ? "Regenerating..." : "Regenerate Review"}
            </button>
            <button
              type="button"
              className="review-edit-button"
              onClick={() => {
                setIsEditing((current) => !current);
                setError("");
              }}
              disabled={isRegenerating || isOpeningGoogle}
            >
              {isEditing ? "✓ Done Editing" : "✎ Edit"}
            </button>
          </div>
        </div>

        {answers.length > 0 && (
          <section className="review-experience-summary" aria-label="Customer experience summary">
            <div className="review-summary-heading">
              <div>
                <span className="review-summary-eyebrow">YOUR INPUT</span>
                <h2>Customer Experience Summary</h2>
                <p>Your selected answers used to personalize this review.</p>
              </div>
              <span className="review-summary-check" aria-hidden="true">✓</span>
            </div>

            <div className="review-summary-list">
              {answers.map((answer, index) => {
                const question = answer?.question || `Question ${index + 1}`;
                const selectedOptions = Array.isArray(answer?.selected_options)
                  ? answer.selected_options
                  : [];

                return (
                  <div
                    className="review-summary-item"
                    key={answer?.query_id ?? `summary-answer-${index}`}
                  >
                    <div className="review-summary-number">{index + 1}</div>
                    <div className="review-summary-detail">
                      <span className="review-summary-question">{question}</span>
                      <div className="review-summary-tags">
                        {selectedOptions.length > 0 ? (
                          selectedOptions.map((option, optionIndex) => (
                            <span
                              key={`${index}-${optionIndex}`}
                              className="review-summary-tag"
                            >
                              {option}
                            </span>
                          ))
                        ) : (
                          <span className="review-summary-tag">No option selected</span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="review-summary-note">
              <span aria-hidden="true">✦</span>
              <div>
                <strong>Made from your answers</strong>
                <p>Your review reflects the experience you selected.</p>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}


export default ReviewPage;
