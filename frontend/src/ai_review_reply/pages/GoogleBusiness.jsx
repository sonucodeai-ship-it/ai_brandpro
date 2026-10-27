import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import "../styles/google_business.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("access_token");
  if (!token) {
    window.location.assign("/login");
    throw new Error("Your session has expired. Please log in again.");
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("auth_user");
    window.location.assign("/login");
    throw new Error("Your session has expired.");
  }
  if (!response.ok) throw new Error(data.detail || "Unable to complete the request.");
  return data;
}

export default function GoogleBusiness() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [business, setBusiness] = useState(null);
  const [connection, setConnection] = useState(null);
  const [connected, setConnected] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [locations, setLocations] = useState([]);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("error");

  const showMessage = (text, type = "error") => {
    setMessage(text);
    setMessageType(type);
  };

  const loadStatus = useCallback(async () => {
    const data = await apiFetch("/api/ai-review-reply/google/status");
    setBusiness(data.business || null);
    setConnection(data.connection || null);
    setConnected(Boolean(data.connected));
    return data;
  }, []);

  const loadAccounts = useCallback(async () => {
    const data = await apiFetch("/api/ai-review-reply/google/accounts");
    setAccounts(data.accounts || []);
  }, []);

  const loadLocations = useCallback(async () => {
    const data = await apiFetch("/api/ai-review-reply/google/locations");
    setLocations(data.locations || []);
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await loadStatus();
      if (data.oauth_authorized && !data.connection?.google_account_name) {
        await loadAccounts();
      } else if (data.connection?.google_account_name && !data.connection?.google_location_id) {
        await loadLocations();
      }
    } catch (error) {
      showMessage(error.message || "Unable to load Google connection.");
    } finally {
      setLoading(false);
    }
  }, [loadAccounts, loadLocations, loadStatus]);

  useEffect(() => {
    const status = searchParams.get("google_oauth");
    const reason = searchParams.get("reason");
    if (status === "success") {
      showMessage("Google authorization succeeded. Select the account and location to finish setup.", "success");
    } else if (status === "denied") {
      showMessage("Google authorization was cancelled or denied.", "error");
    } else if (status === "failed") {
      showMessage(`Google authorization could not be completed${reason ? ` (${reason})` : ""}.`, "error");
    }
    refresh();
  }, [refresh, searchParams]);

  const handleConnect = async () => {
    setBusy(true);
    setMessage("");
    try {
      const data = await apiFetch("/api/ai-review-reply/google/connect");
      if (!data.authorization_url) throw new Error("Google authorization URL was not returned.");
      window.location.assign(data.authorization_url);
    } catch (error) {
      showMessage(error.message || "Unable to start Google authorization.");
      setBusy(false);
    }
  };

  const handleSelectAccount = async (accountName) => {
    setBusy(true);
    setMessage("");
    try {
      await apiFetch("/api/ai-review-reply/google/select-account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_name: accountName }),
      });
      await loadStatus();
      await loadLocations();
      showMessage("Account selected. Now choose the business location.", "success");
    } catch (error) {
      showMessage(error.message || "Unable to select this Google account.");
    } finally {
      setBusy(false);
    }
  };

  const handleSelectLocation = async (locationName) => {
    setBusy(true);
    setMessage("");
    try {
      const data = await apiFetch("/api/ai-review-reply/google/select-location", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ location_name: locationName }),
      });
      await loadStatus();
      showMessage(data.message || "Google Business Profile connected successfully.", "success");
    } catch (error) {
      showMessage(error.message || "Unable to connect this location.");
    } finally {
      setBusy(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm("Disconnect Google Business Profile from AI BrandPlus?")) return;
    setBusy(true);
    try {
      await apiFetch("/api/ai-review-reply/google/disconnect", { method: "DELETE" });
      setAccounts([]);
      setLocations([]);
      await loadStatus();
      showMessage("Google Business Profile disconnected from AI BrandPlus.", "success");
    } catch (error) {
      showMessage(error.message || "Unable to disconnect Google.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <main className="google-business-page"><div className="google-business-shell google-business-loading"><div className="google-business-spinner" /><p>Loading Google Business connection...</p></div></main>;
  }

  const accountSelected = Boolean(connection?.google_account_name);
  const locationSelected = Boolean(connection?.google_location_name);

  return (
    <main className="google-business-page">
      <div className="google-business-shell">
        <header className="google-business-header">
          <button type="button" className="google-business-back" onClick={() => navigate("/menu")}>← Back</button>
          <span className="google-business-eyebrow">AI REVIEW REPLY</span>
          <h1>Google Business Profile</h1>
          <p>Connect a Google Business Profile to manage customer reviews and replies from AI BrandPlus.</p>
        </header>

        {message && <div className={`google-business-message ${messageType}`} role="status">{message}</div>}

        <section className="google-business-card">
          <div className="google-business-card-top">
            <div className="google-business-google-mark">G</div>
            <div>
              <span className="google-business-label">BUSINESS CONNECTION</span>
              <h2>{business?.business_name || "Your Business"}</h2>
            </div>
            <span className={`google-business-status ${connected ? "connected" : "not-connected"}`}>
              <span />{connected ? "Connected" : "Not connected"}
            </span>
          </div>

          {connected ? (
            <>
              <div className="google-business-connected-panel">
                <strong>Google Business Profile connected</strong>
                <p>{connection?.google_location_title || "Your selected business location is connected."}</p>
                <div className="google-business-details">
                  <div><small>Google account</small><span>{connection?.google_account_name || "Connected"}</span></div>
                  <div><small>Location ID</small><span>{connection?.google_location_id || "Connected"}</span></div>
                </div>
              </div>
              <button type="button" className="google-business-secondary-button" onClick={handleConnect} disabled={busy}>Reconnect Google</button>
              <button type="button" className="google-business-secondary-button" onClick={handleDisconnect} disabled={busy}>Disconnect</button>
              <button type="button" className="google-business-secondary-button" onClick={() => navigate("/google-reviews")}>Manage reviews</button>
            </>
          ) : !connection?.connection_status || connection?.connection_status === "reauthorization_required" ? (
            <div className="google-business-connect-copy">
              <h3>Connect your Google Business Profile</h3>
              <p>You will be redirected to Google to authorize AI BrandPlus. Your Google password is never entered into AI BrandPlus.</p>
              <ul>
                <li>Authorization is handled directly by Google.</li>
                <li>AI BrandPlus requests the Business Profile permission required for review management.</li>
                <li>You can disconnect the integration from this page.</li>
              </ul>
              <button type="button" className="google-business-connect-button" onClick={handleConnect} disabled={busy}>
                <span className="google-business-button-mark">G</span><span>{busy ? "Opening Google..." : "Connect Google Business"}</span><span>→</span>
              </button>
            </div>
          ) : !accountSelected ? (
            <div className="google-business-locations">
              <h3>Select a Google Business Profile account</h3>
              {accounts.length === 0 ? <p>No Business Profile accounts were found for this Google account. Check that this Google user manages a profile.</p> :
                accounts.map((account) => (
                  <button type="button" className="google-business-location" key={account.name} onClick={() => handleSelectAccount(account.name)} disabled={busy}>
                    <span className="google-business-location-icon">G</span>
                    <span className="google-business-location-copy"><strong>{account.account_name || account.name}</strong><small>{account.type || account.account_id}</small></span>
                    <span className="google-business-location-arrow">→</span>
                  </button>
                ))}
            </div>
          ) : !locationSelected ? (
            <div className="google-business-locations">
              <h3>Select a business location</h3>
              {locations.length === 0 ? <p>No locations were found under this account.</p> :
                locations.map((location) => (
                  <button type="button" className="google-business-location" key={location.name} onClick={() => handleSelectLocation(location.name)} disabled={busy}>
                    <span className="google-business-location-icon">G</span>
                    <span className="google-business-location-copy"><strong>{location.title || "Business location"}</strong><small>{location.storefront_address?.addressLines?.join(", ") || location.location_id}</small></span>
                    <span className="google-business-location-arrow">→</span>
                  </button>
                ))}
            </div>
          ) : null}
        </section>
        <footer className="google-business-footer"><span>AI BrandPlus</span><span>•</span><span>Secure Google Business connection</span></footer>
      </div>
    </main>
  );
}
