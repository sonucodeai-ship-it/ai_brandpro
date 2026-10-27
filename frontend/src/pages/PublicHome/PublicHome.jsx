import "./PublicHome.css";

const FEATURES = [
  {
    number: "01",
    title: "Business review content",
    description:
      "Create tailored review text from your business context and customer feedback prompts.",
  },
  {
    number: "02",
    title: "Business workspace",
    description:
      "Organize business information, dashboards, and review-related workflows in one workspace.",
  },
  {
    number: "03",
    title: "AI-assisted replies",
    description:
      "Prepare draft responses to customer reviews with AI assistance. Review drafts before using them.",
  },
];

export default function PublicHome() {
  return (
    <main className="public-home">
      <header className="public-nav">
        <a className="public-brand" href="/" aria-label="AI BrandPlus home">
          <span className="public-brand-mark" aria-hidden="true">A</span>
          <span>AI BrandPlus</span>
        </a>
        <nav className="public-nav-links" aria-label="Main navigation">
          <a href="#features">Features</a>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a className="public-signin" href="/login">Sign in</a>
        </nav>
      </header>

      <section className="public-hero">
        <div className="public-hero-copy">
          <p className="public-eyebrow">AI TOOLS FOR BUSINESS WORKFLOWS</p>
          <h1>Build stronger customer relationships with <span>AI BrandPlus.</span></h1>
          <p className="public-hero-description">
            AI BrandPlus is a business-focused platform that helps teams prepare
            review content, organize business information, and work with
            AI-assisted customer-review responses.
          </p>
          <div className="public-hero-actions">
            <a className="public-primary-button" href="/login">Sign in to AI BrandPlus</a>
            <a className="public-secondary-button" href="#features">Explore the platform</a>
          </div>
          <p className="public-note">
            AI-generated content should be checked for accuracy before it is published or sent.
          </p>
        </div>

        <aside className="public-preview" aria-label="Platform overview">
          <div className="public-preview-top">
            <span className="public-dot" />
            <span className="public-dot" />
            <span className="public-dot" />
            <span className="public-preview-label">BUSINESS WORKSPACE</span>
          </div>
          <div className="public-preview-body">
            <div className="public-preview-icon">✦</div>
            <p className="public-preview-kicker">AI-ASSISTED WORKFLOW</p>
            <h2>Your business, organized.</h2>
            <p>Review content, business details, and customer-facing workflows in one place.</p>
            <div className="public-preview-line"><span>Business information</span><b>Workspace</b></div>
            <div className="public-preview-line"><span>Review content</span><b>AI assisted</b></div>
            <div className="public-preview-line"><span>Response drafts</span><b>Human reviewed</b></div>
          </div>
        </aside>
      </section>

      <section className="public-features" id="features">
        <div className="public-section-heading">
          <p className="public-eyebrow">WHAT THE PLATFORM DOES</p>
          <h2>Practical tools for everyday business workflows</h2>
          <p>AI BrandPlus supports business owners and teams with AI-assisted content and organized workflows.</p>
        </div>
        <div className="public-feature-grid">
          {FEATURES.map((feature) => (
            <article className="public-feature-card" key={feature.number}>
              <span className="public-feature-number">{feature.number}</span>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="public-transparency">
        <div>
          <p className="public-eyebrow">PRIVACY & TRANSPARENCY</p>
          <h2>Your information deserves clear handling.</h2>
          <p>
            Read our policies to understand how AI BrandPlus describes its
            services, handles information, and sets the terms for using the platform.
          </p>
        </div>
        <div className="public-policy-links">
          <a href="/privacy">Read Privacy Policy <span aria-hidden="true">↗</span></a>
          <a href="/terms">Read Terms of Service <span aria-hidden="true">↗</span></a>
        </div>
      </section>

      <footer className="public-footer">
        <a className="public-brand public-footer-brand" href="/">
          <span className="public-brand-mark" aria-hidden="true">A</span>
          <span>AI BrandPlus</span>
        </a>
        <p>AI-assisted business tools. Please review generated content before use.</p>
        <div>
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a href="/login">Sign in</a>
        </div>
        <small>© {new Date().getFullYear()} AI BrandPlus</small>
      </footer>
    </main>
  );
}
