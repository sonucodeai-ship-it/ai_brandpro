import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./business_info.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function BusinessInfo() {
  const navigate = useNavigate();
  const formRef = useRef(null);

  const [formData, setFormData] = useState({
    business_name: "",
    business_type: "",
    about_business: "",
    year_established: "",
    google_review_link: "",
  });
  const [updatedAtFormatted, setUpdatedAtFormatted] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadBusinessInfo = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        navigate("/login", { replace: true });
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/business/info`, {
          method: "GET",
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("auth_user");
          navigate("/login", { replace: true });
          return;
        }

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Unable to load business information.");
        }

        if (!cancelled && data.business_id) {
          setFormData({
            business_name: data.business_name || "",
            business_type: data.business_type || "",
            about_business: data.about_business || "",
            year_established: data.year_established ? String(data.year_established) : "",
            google_review_link: data.google_review_link || "",
          });
          setUpdatedAtFormatted(data.updated_at_formatted || "");
        }
      } catch (loadError) {
        console.error("Business information loading failed:", loadError);
        if (!cancelled) setError(loadError.message || "Unable to load business information.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    loadBusinessInfo();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!formRef.current?.reportValidity()) return;

    const token = localStorage.getItem("access_token");
    if (!token) {
      navigate("/login", { replace: true });
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/business/info`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          business_name: formData.business_name.trim(),
          business_type: formData.business_type.trim(),
          about_business: formData.about_business.trim(),
          year_established: Number(formData.year_established),
          google_review_link: formData.google_review_link.trim(),
        }),
      });

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth_user");
        navigate("/login", { replace: true });
        return;
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to save business information.");
      }

      setUpdatedAtFormatted(data.updated_at_formatted || "");
      setSuccess("Business information saved successfully.");
    } catch (saveError) {
      console.error("Business information save failed:", saveError);
      setError(saveError.message || "Unable to save business information.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <main className="business-info-page">
        <div className="business-info-loading" role="status" aria-live="polite">
          <span className="business-info-spinner" />
          <p>Loading business information…</p>
        </div>
      </main>
    );
  }

  return (
    <main className="business-info-page">
      <div className="business-info-container">
        <header className="business-info-header">
          <div className="business-info-heading-copy">
            <span className="business-info-eyebrow">BUSINESS SETTINGS</span>
            <h1>Business information</h1>
            <p>Manage the details customers see and use when interacting with your business.</p>
          </div>
          {updatedAtFormatted && (
            <div className="business-info-updated">
              <span>Last saved</span>
              <strong>{updatedAtFormatted}</strong>
            </div>
          )}
        </header>

        <section className="business-info-card" aria-labelledby="business-details-title">
          <div className="business-info-card-header">
            <div className="business-info-card-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M4 21h16M6.5 21V9.5h11V21M9 9.5V6.5h6v3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M8.5 13h1M8.5 16.5h1M14.5 13h1M14.5 16.5h1" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <h2 id="business-details-title">Business details</h2>
              <p>Keep your business profile accurate and up to date.</p>
            </div>
          </div>

          <form ref={formRef} onSubmit={handleSubmit}>
            {/* =================================================
                BUSINESS NAME
                ================================================= */}

            <div className="business-info-field">

              <label htmlFor="business_name">
                Business Name
                <span className="required-mark">
                  *
                </span>
              </label>

              <div className="business-info-input-wrap">

                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M4 21h16M6.5 21V9.5h11V21M9 9.5V6.5h6v3"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                <input
                  id="business_name"
                  name="business_name"
                  type="text"
                  placeholder="Enter your business name"
                  value={
                    formData.business_name
                  }
                  onChange={handleChange}
                  maxLength={255}
                  required
                />

              </div>

            </div>

            {/* =================================================
                BUSINESS TYPE
                ================================================= */}

            <div className="business-info-field">

              <label htmlFor="business_type">
                Business Type
                <span className="required-mark">
                  *
                </span>
              </label>

              <div className="business-info-input-wrap">

                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M5 20V9h14v11M8 9V5h8v4M8 13h2M14 13h2M8 16.5h2M14 16.5h2"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                <input
                  id="business_type"
                  name="business_type"
                  type="text"
                  placeholder="e.g. Dental Clinic, Restaurant, Salon"
                  value={
                    formData.business_type
                  }
                  onChange={handleChange}
                  maxLength={100}
                  required
                />

              </div>

              <span className="business-info-hint">
                What type of business do you operate?
              </span>

            </div>

            {/* =================================================
                ABOUT BUSINESS
                ================================================= */}

            <div className="business-info-field">

              <div className="business-info-label-row">

                <label htmlFor="about_business">
                  About Business
                  <span className="required-mark">
                    *
                  </span>
                </label>

                <span className="business-info-counter">
                  {
                    formData.about_business
                      .length
                  }
                  /2000
                </span>

              </div>

              <div className="business-info-textarea-wrap">

                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M5 5.5A2.5 2.5 0 0 1 7.5 3h9A2.5 2.5 0 0 1 19 5.5v13a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 5 18.5v-13Z"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  />

                  <path
                    d="M8.5 8h7M8.5 12h7M8.5 16h4"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>

                <textarea
                  id="about_business"
                  name="about_business"
                  placeholder="Tell us briefly about your business, the services you provide, and what makes your business unique..."
                  value={
                    formData.about_business
                  }
                  onChange={handleChange}
                  maxLength={2000}
                  rows={5}
                  required
                />

              </div>

              <span className="business-info-hint">
                A clear description helps AI Reviewer
                understand your business better.
              </span>

            </div>

            {/* =================================================
                YEAR ESTABLISHED
                ================================================= */}

            <div className="business-info-field">

              <label htmlFor="year_established">
                Year Established
                <span className="required-mark">
                  *
                </span>
              </label>

              <div className="business-info-input-wrap">

                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <rect
                    x="4"
                    y="5"
                    width="16"
                    height="15"
                    rx="2"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  />

                  <path
                    d="M8 3v4M16 3v4M4 9h16"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />

                  <path
                    d="M8 13h.01M12 13h.01M16 13h.01M8 16.5h.01M12 16.5h.01"
                    stroke="currentColor"
                    strokeWidth="2.2"
                    strokeLinecap="round"
                  />
                </svg>

                <input
                  id="year_established"
                  name="year_established"
                  type="number"
                  placeholder="e.g. 2018"
                  value={
                    formData.year_established
                  }
                  onChange={handleChange}
                  min="1800"
                  max="2100"
                  required
                />

              </div>

            </div>

            {/* =================================================
                GOOGLE BUSINESS REVIEW LINK
                ================================================= */}

            <div className="business-info-field">
              <label htmlFor="google_review_link">
                Google Business Review Link
                <span className="required-mark">
                  *
                </span>
              </label>

              <div className="business-info-input-wrap">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  <path
                    d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.1-1.1"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                <input
                  id="google_review_link"
                  name="google_review_link"
                  type="url"
                  inputMode="url"
                  placeholder="https://g.page/r/..."
                  value={formData.google_review_link}
                  onChange={handleChange}
                  maxLength={1000}
                  required
                />
              </div>

              <span className="business-info-hint">
                Add the Google link customers should use to leave a review.
              </span>
            </div>


            {error && (
              <div className="business-info-message error" role="alert">
                <span className="business-info-message-icon" aria-hidden="true">!</span>
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div className="business-info-message success" role="status" aria-live="polite">
                <span className="business-info-message-icon" aria-hidden="true">✓</span>
                <span>{success}</span>
              </div>
            )}

            <div className="business-info-actions">
              <button type="submit" className="business-info-save-button" disabled={saving}>
                {saving ? (
                  <>
                    <span className="business-info-button-spinner" aria-hidden="true" />
                    Saving changes…
                  </>
                ) : (
                  "Save changes"
                )}
              </button>
            </div>
            <p className="business-info-footer-text">Your changes are saved to your business profile.</p>
          </form>
        </section>
      </div>
    </main>
  );
}

export default BusinessInfo;
