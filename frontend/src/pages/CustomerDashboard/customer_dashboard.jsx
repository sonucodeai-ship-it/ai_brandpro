import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import "./customer_dashboard.css";

const API_BASE_URL = String(import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

function CustomerDashboard({ navigateToReview, navigateToQueryMaker }) {
  const { publicUrlId } = useParams();

  const [selectedDashboard, setSelectedDashboard] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [selectedOptions, setSelectedOptions] = useState({});
  const [business, setBusiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const loadDashboard = async (id) => {
    const response = await fetch(
      `${API_BASE_URL}/api/dashboard/public/${id}`
    );

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Unable to load dashboard.");
    setSelectedDashboard(data.dashboard);
    const currentBusinessName = data.dashboard.business_name || "Your Business";
    setBusiness((current) => ({
      ...current,
      business_name: currentBusinessName,
      year_established: data.dashboard.year_established || current?.year_established,
    }));

  };

  const loadQuestions = async (id) => {
    const response = await fetch(
      `${API_BASE_URL}/api/dashboard/public/${id}/questions`
    );
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Unable to load questions.");
    setQuestions(data.questions || []);
  };

  useEffect(() => {
    const initialize = async () => {
      if (!publicUrlId) { setError("Invalid dashboard link."); setLoading(false); return; }
      setLoading(true); setError("");
      try { await loadDashboard(publicUrlId); await loadQuestions(publicUrlId); }
      catch (err) { console.error("Customer dashboard initialization failed:", err); setError(err.message || "Unable to load this dashboard."); }
      finally { setLoading(false); }
    };
    initialize();
  }, [publicUrlId]);

  const toggleOption = (queryId, optionText) => {
    setSelectedOptions((current) => {
      const existing = current[queryId] || [];
      return { ...current, [queryId]: existing.includes(optionText) ? existing.filter((item) => item !== optionText) : [...existing, optionText] };
    });
    setError("");
  };

  const selectedOptionCount = Object.values(selectedOptions).reduce((total, selected) => total + selected.length, 0);

  const generateReview = async () => {
    if (!questions.length) { setError("This dashboard does not have a questionnaire yet."); return; }
    const answers = questions.map((question) => ({ query_id: question.query_id, question: question.question, selected_options: selectedOptions[question.query_id] || [] }));
    if (!answers.some((answer) => answer.selected_options.length > 0)) { setError("Please select at least one option to create your review."); return; }
    setWorking(true); setError("");
    try {
      // Customer review generation is intentionally public.
      // Do not send or require the business owner's authentication token.
      const response = await fetch(
        `${API_BASE_URL}/api/reviews/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            answers,
            dashboard_id: selectedDashboard?.dashboard_id || null,
            regenerate_status: 0,
          }),
        }
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to generate the review.");
      navigateToReview({ review: data.review, reviewId: data.review_id, answers, dashboard: selectedDashboard });
    } catch (err) { console.error("Review generation failed:", err); setError(err.message || "Unable to generate the review."); }
    finally { setWorking(false); }
  };

  return (
    <main className="dashboard-customer-page">
      <div className="dashboard-customer-background-circle dashboard-customer-circle-one" />
      <div className="dashboard-customer-background-circle dashboard-customer-circle-two" />

      <div className="dashboard-customer-container dashboard-customer-detail">
        <header className="dashboard-customer-business-header">
          <div className="dashboard-customer-business-heading">
            <div className="dashboard-customer-business-logo" aria-hidden="true">
              <svg viewBox="0 0 48 48" className="dashboard-customer-google-mark">
                <path fill="#4285F4" d="M43.6 24.5c0-1.4-.1-2.8-.4-4.1H24v7.8h11a9.4 9.4 0 0 1-4.1 6.2v5.1h6.6c3.9-3.6 6.1-8.8 6.1-15Z" />
                <path fill="#34A853" d="M24 44c5.5 0 10.1-1.8 13.5-4.9l-6.6-5.1c-1.8 1.2-4.1 2-6.9 2-5.3 0-9.8-3.6-11.4-8.4H5.8v5.3A20 20 0 0 0 24 44Z" />
                <path fill="#FBBC05" d="M12.6 27.6a12 12 0 0 1 0-7.2v-5.3H5.8a20 20 0 0 0 0 17.8l6.8-5.3Z" />
                <path fill="#EA4335" d="M24 12c3 0 5.7 1 7.8 3.1l5.8-5.8C34.1 6 29.5 4 24 4A20 20 0 0 0 5.8 15.1l6.8 5.3C14.2 15.6 18.7 12 24 12Z" />
              </svg>
            </div>

            <div className="dashboard-customer-business-title">
              <h1>
                {selectedDashboard?.business_name ||
                  business?.business_name ||
                  "Your Business"}
              </h1>
              {(selectedDashboard?.year_established || business?.year_established) && (
                <span>
                  Established {selectedDashboard?.year_established || business?.year_established}
                </span>
              )}
            </div>
          </div>

          {(selectedDashboard?.year_established || business?.year_established) && (
            <div className="dashboard-customer-established-badge">
              <span className="dashboard-customer-established-icon">✓</span>
              <div>
                <small>Serving since</small>
                <strong>
                  {selectedDashboard?.year_established || business?.year_established}
                </strong>
              </div>
            </div>
          )}
        </header>

        <section className="dashboard-customer-intro">
          <div className="dashboard-google-brand" aria-label="Google reviews">
            <svg className="dashboard-google-g" viewBox="0 0 48 48" role="img" aria-label="Google G">
              <path fill="#4285F4" d="M43.6 24.5c0-1.4-.1-2.8-.4-4.1H24v7.8h11a9.4 9.4 0 0 1-4.1 6.2v5.1h6.6c3.9-3.6 6.1-8.8 6.1-15Z" />
              <path fill="#34A853" d="M24 44c5.5 0 10.1-1.8 13.5-4.9l-6.6-5.1c-1.8 1.2-4.1 2-6.9 2-5.3 0-9.8-3.6-11.4-8.4H5.8v5.3A20 20 0 0 0 24 44Z" />
              <path fill="#FBBC05" d="M12.6 27.6a12 12 0 0 1 0-7.2v-5.3H5.8a20 20 0 0 0 0 17.8l6.8-5.3Z" />
              <path fill="#EA4335" d="M24 12c3 0 5.7 1 7.8 3.1l5.8-5.8C34.1 6 29.5 4 24 4A20 20 0 0 0 5.8 15.1l6.8 5.3C14.2 15.6 18.7 12 24 12Z" />
            </svg>
            <span>Google</span>
            <span className="dashboard-google-brand-divider">·</span>
            <span className="dashboard-google-brand-subtitle">Review</span>
          </div>
          <h2>Share your experience</h2>
          <p>Answer a few quick questions to create your Google review.</p>
        </section>

        {error && (
          <div className="dashboard-message error dashboard-customer-error">
            {error}
          </div>
        )}

        {loading ? (
          <section className="dashboard-empty dashboard-customer-empty" role="status">
            <div className="dashboard-empty-icon">…</div>
            <h3>Loading questions</h3>
            <p>Please wait while we prepare the questionnaire.</p>
          </section>
        ) : questions.length === 0 ? (
          <section className="dashboard-empty dashboard-customer-empty">
            <div className="dashboard-empty-icon">?</div>
            <h3>No questions available</h3>
            <p>
              Create your customer questions before generating a review.
            </p>
            <button
              type="button"
              onClick={() => navigateToQueryMaker(selectedDashboard?.dashboard_id)}
            >
              Open Query Maker
              <span>→</span>
            </button>
          </section>
        ) : (
          <section className="dashboard-customer-questions-card">
            {questions.map((question, questionIndex) => {
              const questionKey = question.query_id;
              const selected = selectedOptions[questionKey] || [];

              return (
                <div
                  className="dashboard-customer-question-section"
                  key={questionKey}
                >
                  <div className="dashboard-customer-question-heading">
                    <div className="dashboard-customer-question-number">
                      {String(questionIndex + 1).padStart(2, "0")}
                    </div>

                    <div>
                      <h3>{question.question}</h3>
                    </div>
                  </div>

                  <div className="dashboard-customer-options-grid">
                    {question.options.map((option, optionIndex) => {
                      const isSelected = selected.includes(option.text);

                      return (
                        <button
                          key={
                            option.option_id ??
                            `${questionKey}-${optionIndex}`
                          }
                          type="button"
                          className={`dashboard-customer-option-card ${
                            isSelected ? "selected" : ""
                          }`}
                          onClick={() =>
                            toggleOption(question.query_id, option.text)
                          }
                          disabled={working}
                        >
                          <span className="dashboard-customer-option-icon">
                            {isSelected ? "✓" : "+"}
                          </span>
                          <span className="dashboard-customer-option-text">
                            {option.text}
                          </span>
                          <span className="dashboard-customer-selection-check">✓</span>
                        </button>
                      );
                    })}
                  </div>

                  {questionIndex < questions.length - 1 && (
                    <div className="dashboard-customer-divider" />
                  )}
                </div>
              );
            })}

            <div className="dashboard-customer-action dashboard-customer-sticky-action">
              <button
                type="button"
                className="dashboard-customer-continue-button"
                disabled={working}
                onClick={generateReview}
              >
                <span>{working ? "Creating review…" : "Create review"}</span>
                <span className="dashboard-customer-arrow" aria-hidden="true">
                  {working ? "…" : "→"}
                </span>
              </button>
            </div>
          </section>
        )}

        <footer className="dashboard-customer-footer">
          <span className="dashboard-customer-footer-google">G</span>
          <span>Review created with Google-style review assistance</span>
        </footer>
      </div>
    </main>
  );
}

export default CustomerDashboard;
