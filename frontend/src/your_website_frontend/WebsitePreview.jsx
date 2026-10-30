import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import "./website_preview.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  "http://127.0.0.1:8000";


/**
 * Remove only the mobile contact-bar backdrop from generated showcase HTML.
 * The Call and WhatsApp buttons retain their own colors, shadows, and behavior.
 * Desktop styling is intentionally unchanged.
 */
function applyMobileContactBarFix(htmlDocument) {
  const mobileContactStyle = `
    <style id="vg-mobile-contact-transparent-override">
      @media (max-width: 640px) {
        #vg-contact-actions.vg-contact-actions {
          background: transparent !important;
          border-top: 0 !important;
          box-shadow: none !important;
          backdrop-filter: none !important;
          -webkit-backdrop-filter: none !important;
        }
      }
    </style>
  `;

  // Avoid inserting the same override more than once.
  if (htmlDocument.includes('id="vg-mobile-contact-transparent-override"')) {
    return htmlDocument;
  }

  if (/<\/head\s*>/i.test(htmlDocument)) {
    return htmlDocument.replace(/<\/head\s*>/i, `${mobileContactStyle}</head>`);
  }

  // Defensive fallback for generated documents that omit a closing head tag.
  return `${mobileContactStyle}${htmlDocument}`;
}

function WebsitePreview() {
  const { publicUrlId } = useParams();

  const [html, setHtml] = useState("");
  const [business, setBusiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const loadWebsite = async () => {
      const safePublicUrlId = String(publicUrlId || "").trim();

      if (!safePublicUrlId || safePublicUrlId === "undefined") {
        if (active) {
          setError("This website URL is incomplete or invalid.");
          setLoading(false);
        }
        return;
      }

      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE_URL}/api/your-website/public/${encodeURIComponent(
            safePublicUrlId
          )}`
        );

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.detail || "Unable to load website.");
        }

        const htmlCode = String(data.html_code || "").trim();

        if (!htmlCode) {
          throw new Error("This website has not been published yet.");
        }

        if (active) {
          setHtml(applyMobileContactBarFix(htmlCode));
          setBusiness(data.business || null);
        }
      } catch (err) {
        console.error("Public website loading failed:", err);

        if (active) {
          setError(err.message || "Unable to load website.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadWebsite();

    return () => {
      active = false;
    };
  }, [publicUrlId]);

  if (loading) {
    return (
      <main className="generated-site-loading">
        <div className="generated-site-spinner" />
        <p>Loading website...</p>
      </main>
    );
  }

  if (error || !html) {
    return (
      <main className="generated-site-error">
        <div className="generated-site-error-card">
          <div className="generated-site-error-icon">!</div>
          <span>WEBSITE</span>
          <h1>Website unavailable</h1>
          <p>{error || "This website could not be loaded."}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="generated-site-shell">
      <iframe
        title={business?.business_name || "Business website"}
        className="generated-site-frame"
        srcDoc={html}
        sandbox="allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-modals"
        referrerPolicy="no-referrer"
      />
    </main>
  );
}

export default WebsitePreview;
