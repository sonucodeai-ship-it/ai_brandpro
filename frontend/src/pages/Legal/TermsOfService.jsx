import React from "react";
import "./LegalPages.css";

export default function TermsOfService() {
  return (
    <main className="legal-page">
      <article className="legal-card">
        <a className="legal-brand" href="/login" aria-label="AI BrandPlus home">AI BrandPlus</a>
        <p className="legal-eyebrow">LEGAL</p>
        <h1>Terms of Service</h1>
        <p className="legal-updated">Effective date: October 27, 2026</p>
        <p>
          These Terms of Service ("Terms") apply to your use of AI BrandPlus at{" "}
          <a href="https://aibrandplus.com">aibrandplus.com</a>. By accessing or using the service,
          you agree to these Terms. If you do not agree, do not use the service.
        </p>

        <h2>1. The service</h2>
        <p>
          AI BrandPlus provides business-management and reputation workflows. Depending on the features
          available to your account, these may include connecting to Google Business Profile, viewing
          authorized reviews, and generating or managing suggested review replies.
        </p>

        <h2>2. Accounts and authorization</h2>
        <p>
          You must provide accurate account information and keep your login credentials secure. If you connect
          a Google Account or business profile, you represent that you are the owner, manager, or otherwise
          authorized to grant access to that profile. You are responsible for reviewing the permissions you grant.
          You may revoke Google access through your Google Account settings.
        </p>

        <h2>3. Acceptable use</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Use AI BrandPlus for unlawful, fraudulent, deceptive, or abusive activity.</li>
          <li>Access or attempt to manage a business profile without authorization.</li>
          <li>Interfere with the service, bypass security controls, or attempt unauthorized access.</li>
          <li>Use the service in a way that violates Google's terms, API policies, or applicable law.</li>
          <li>Submit or publish content that infringes rights or is unlawful.</li>
        </ul>

        <h2>4. AI-generated content and review replies</h2>
        <p>
          AI BrandPlus may generate suggested text using automated systems. Such text may be inaccurate,
          incomplete, or unsuitable for a particular situation. You are responsible for checking each suggestion
          for factual accuracy, tone, privacy, and compliance before using it. If a feature lets you publish or
          submit a reply, you are responsible for confirming that you are authorized to do so and that the final
          content is appropriate.
        </p>

        <h2>5. Third-party services</h2>
        <p>
          Some features rely on third-party services, including Google Business Profile APIs and AI or hosting
          providers. These services may change, become unavailable, or impose their own requirements. Your use
          of third-party services is also subject to their applicable terms and policies. AI BrandPlus is not
          affiliated with or endorsed by Google unless expressly stated.
        </p>

        <h2>6. Availability and changes</h2>
        <p>
          We aim to keep AI BrandPlus available and reliable, but do not guarantee uninterrupted or error-free
          operation. We may change, suspend, or discontinue features when reasonably necessary for operational,
          security, legal, or business reasons.
        </p>

        <h2>7. Intellectual property and submitted content</h2>
        <p>
          AI BrandPlus and its software, branding, and materials are owned by or licensed to their respective
          rights holders. You remain responsible for ensuring that you have the rights and permissions needed
          to submit, use, or publish content through the service.
        </p>

        <h2>8. Disclaimer and limitation</h2>
        <p>
          To the extent permitted by applicable law, the service is provided on an "as available" basis and
          without guarantees that it will meet every requirement or produce a particular business outcome.
          Nothing in these Terms excludes any right or liability that cannot legally be excluded.
        </p>

        <h2>9. Suspension and termination</h2>
        <p>
          You may stop using AI BrandPlus at any time. We may restrict or suspend access where reasonably
          necessary to address security risks, misuse, violations of these Terms, legal requirements, or a
          third-party service restriction.
        </p>

        <h2>10. Changes to these Terms</h2>
        <p>
          We may update these Terms as the service evolves. The current version will be published on this page
          with an updated effective date when appropriate. Continued use after an update takes effect means
          you accept the updated Terms to the extent permitted by law.
        </p>

        <h2>11. Contact</h2>
        <p>
          For questions about these Terms, contact{" "}
          <a href="mailto:dr.bhartidental@gmail.com">dr.bhartidental@gmail.com</a>.
        </p>
        <footer className="legal-footer">
          <a href="/privacy">Privacy Policy</a>
          <span aria-hidden="true">•</span>
          <a href="/login">Back to AI BrandPlus</a>
        </footer>
      </article>
    </main>
  );
}
