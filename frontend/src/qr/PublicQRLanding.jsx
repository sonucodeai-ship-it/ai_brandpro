import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { qrApi } from "./qrApi";
import "./public_qr_landing.css";

function GoogleGIcon() {
  return (
    <svg className="qr-public-google-icon" viewBox="0 0 48 48" role="img" aria-label="Google">
      <path fill="#4285F4" d="M43.6 24.5c0-1.57-.14-3.09-.4-4.55H24v9.02h11c-.48 2.58-1.93 4.77-4.1 6.24v5.2h6.63c3.88-3.58 6.07-8.84 6.07-15.91Z" />
      <path fill="#34A853" d="M24 44c5.4 0 9.92-1.79 13.23-4.85l-6.63-5.2c-1.84 1.24-4.19 1.97-6.6 1.97-5.08 0-9.39-3.43-10.94-8.05H6.21v5.36C9.5 39.52 16.24 44 24 44Z" />
      <path fill="#FBBC05" d="M13.06 27.87A13.2 13.2 0 0 1 12.38 24c0-1.34.23-2.64.68-3.87v-5.36H6.21A20 20 0 0 0 4 24c0 3.23.77 6.29 2.21 9.23l6.85-5.36Z" />
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 16.24 0 9.5 4.48 6.21 14.77l6.85 5.36C14.61 13.43 18.92 9.5 24 9.5Z" />
    </svg>
  );
}

function ShowcaseIcon() {
  return (
    <svg className="qr-public-showcase-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3.25" y="3.25" width="17.5" height="17.5" rx="3.25" stroke="currentColor" strokeWidth="1.7" />
      <path d="M7.5 8h9M7.5 12h3.5M7.5 16h9" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
      <path d="M14.5 11.2 17 13.7l-2.5 2.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4.5 12h14M12.5 5.5 19 12l-6.5 6.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}


export default function PublicQRLanding({
  canonicalizeQrLanding,
  navigateToCustomerDashboard,
  navigateToWebsitePreview,
}) {
  const { qrToken } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [opening, setOpening] = useState("");

  useEffect(() => {
    let alive = true;
    setData(null);
    setError("");
    setLoading(true);

    qrApi.resolvePublic(qrToken)
      .then((result) => {
        if (alive) setData(result);
      })
      .catch((err) => {
        if (alive) setError(err.message || "This QR code is unavailable.");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [qrToken]);

  // App.jsx owns canonical URL construction and replacement navigation.
  useEffect(() => {
    if (data && qrToken && canonicalizeQrLanding) {
      canonicalizeQrLanding(data.business_name, qrToken);
    }
  }, [data, qrToken, canonicalizeQrLanding]);

  const displayBusinessName = String(data?.business_name || "Welcome")
    .replace(/\s+/g, " ")
    .trim();

  const openDestination = async (type) => {
    if (!data || opening) return;

    setOpening(type);

    try {
      await qrApi.track(
        qrToken,
        type === "review" ? "review_click" : "showcase_click",
      );
    } catch (err) {
      // Analytics failures must never block the customer's destination.
      console.warn("QR click analytics could not be recorded:", err);
    }

    if (type === "review") {
      navigateToCustomerDashboard(data.business_name, data.dashboard_public_url_id);
    } else {
      navigateToWebsitePreview(data.business_name, data.website_public_url_id);
    }
  };

  return (
    <main className="qr-public-page">
      <div className="qr-public-background-shape qr-public-background-shape-one" aria-hidden="true" />
      <div className="qr-public-background-shape qr-public-background-shape-two" aria-hidden="true" />

      <section className="qr-public-panel" aria-live="polite">

        {loading ? (
          <div className="qr-public-loading">
            <span className="qr-public-spinner" aria-hidden="true" />
            <p>Preparing your experience</p>
            <span className="qr-public-loading-hint">Just a moment…</span>
          </div>
        ) : error ? (
          <div className="qr-public-error">
            <div className="qr-public-state-icon qr-public-state-icon-error" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 8v5M12 16.5h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                <path d="M10.3 3.8 2.9 17a2 2 0 0 0 1.75 3h14.7a2 2 0 0 0 1.75-3L13.7 3.8a2 2 0 0 0-3.4 0Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
              </svg>
            </div>
            <p className="qr-public-eyebrow">LINK NOT AVAILABLE</p>
            <h1>We can’t open this QR code</h1>
            <p className="qr-public-description">{error}</p>
            <p className="qr-public-help">Please ask the business team for a valid QR code or link.</p>
          </div>
        ) : (
          <>
            <div className="qr-public-welcome-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M4.5 11.5 12 5l7.5 6.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M6.5 10.5V19h11v-8.5M10 19v-5.5h4V19" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>

            <p className="qr-public-eyebrow">A WARM WELCOME FROM</p>
            <h1 className="qr-public-business-name">{displayBusinessName}</h1>
            <span className="qr-public-name-ornament" aria-hidden="true"><span /></span>
            <p className="qr-public-description">
              Thank you for being here. How would you like to continue?
            </p>

            <div className="qr-public-choice-heading">
              <span>CHOOSE AN OPTION</span>
              <span className="qr-public-choice-line" />
            </div>

            <div className="qr-public-actions">
              <button
                type="button"
                className="qr-public-action qr-public-review"
                onClick={() => openDestination("review")}
                disabled={Boolean(opening)}
                aria-label="Review us on Google"
              >
                <span className="qr-public-action-icon qr-public-google-tile">
                  <GoogleGIcon />
                </span>
                <span className="qr-public-action-copy">
                  <strong>Review on Google</strong>
                  <small>Share your experience</small>
                </span>
                <span className="qr-public-action-arrow">
                  {opening === "review" ? <span className="qr-public-button-spinner" /> : <ArrowIcon />}
                </span>
              </button>

              <button
                type="button"
                className="qr-public-action qr-public-showcase"
                onClick={() => openDestination("showcase")}
                disabled={Boolean(opening)}
                aria-label="View our digital showcase"
              >
                <span className="qr-public-action-icon qr-public-showcase-tile">
                  <ShowcaseIcon />
                </span>
                <span className="qr-public-action-copy">
                  <strong>View Our Business</strong>
                  <small>Discover what we offer</small>
                </span>
                <span className="qr-public-action-arrow">
                  {opening === "showcase" ? <span className="qr-public-button-spinner" /> : <ArrowIcon />}
                </span>
              </button>
            </div>

            {opening && (
              <p className="qr-public-opening-message" role="status">
                <span className="qr-public-button-spinner" />
                Opening your selection…
              </p>
            )}

            <div className="qr-public-trust-note">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 3.5 19 6v5.4c0 4.2-2.8 7.5-7 9.1-4.2-1.6-7-4.9-7-9.1V6l7-2.5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                <path d="m9 12 2 2 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span>Your choice opens securely in the next step.</span>
            </div>
          </>
        )}

        <footer className="qr-public-footer">
          <span>Thank you for choosing us</span>
        </footer>
      </section>
    </main>
  );
}
