import React from "react";
import "./LegalPages.css";

export default function PrivacyPolicy() {
  return (
    <main className="legal-page">
      <article className="legal-card">
        <a className="legal-brand" href="/login" aria-label="AI BrandPlus home">AI BrandPlus</a>
        <p className="legal-eyebrow">LEGAL</p>
        <h1>Privacy Policy</h1>
        <p className="legal-updated">Effective date: October 27, 2026</p>
        <p>
          This Privacy Policy explains how AI BrandPlus ("AI BrandPlus," "we," "us," or "our")
          handles information when you use <a href="https://aibrandplus.com">aibrandplus.com</a>
          and its business-management features.
        </p>

        <h2>1. Information we handle</h2>
        <p>Depending on the features you use, we may handle:</p>
        <ul>
          <li>Account details, such as your name, email address, and contact information.</li>
          <li>Business information you provide, such as your business name, description, and profile details.</li>
          <li>Google Business Profile data you authorize us to access, such as account or location details, customer reviews, and review replies.</li>
          <li>Information you enter into AI BrandPlus, including prompts and content submitted to generate suggested replies.</li>
          <li>Technical, diagnostic, and usage information needed to operate, protect, and troubleshoot the service.</li>
        </ul>

        <h2>2. How we use information</h2>
        <p>We use information as needed to provide the features you request, including to:</p>
        <ul>
          <li>Operate and maintain your account and business workspace.</li>
          <li>Connect to Google Business Profile after you authorize access.</li>
          <li>Display authorized reviews and help you draft or manage review replies.</li>
          <li>Respond to support requests, maintain security, prevent misuse, and diagnose errors.</li>
          <li>Meet legal obligations and enforce our terms.</li>
        </ul>

        <h2>3. Google API data and permissions</h2>
        <p>
          If you connect a Google Account, Google will ask you to grant the requested permissions.
          AI BrandPlus accesses Google data only as permitted by your authorization and the applicable
          Google APIs, and uses that data to provide the features you choose. You can review or revoke
          access through your Google Account's third-party connections / permissions settings.
        </p>
        <p>
          Our use and transfer of information received from Google APIs will comply with the Google API
          Services User Data Policy, including its Limited Use requirements. We do not sell Google user
          data or use it for advertising. Google authorization can be revoked at any time; revocation may
          stop future access but does not necessarily delete information already stored in your AI BrandPlus account.
        </p>

        <h2>4. How information may be shared</h2>
        <p>
          We do not sell personal information. Information may be processed by service providers that help
          us host, secure, maintain, or operate AI BrandPlus, including providers used for AI features, where
          applicable. We may disclose information when required by law, to respond to valid legal process,
          or to protect users, our service, and our rights. We do not authorize service providers to use data
          for purposes unrelated to providing their services to us.
        </p>

        <h2>5. Retention and security</h2>
        <p>
          We retain information for as long as reasonably necessary to provide the service, support your
          account, meet legal obligations, resolve disputes, and enforce agreements. Actual retention depends
          on the type of information and how you use the service. We use reasonable technical and
          organizational safeguards designed to protect information, but no method of storage or transmission
          is completely secure.
        </p>

        <h2>6. Your choices and requests</h2>
        <p>
          You can disconnect Google access through your Google Account settings. You may also contact us to
          request access to, correction of, or deletion of personal information, subject to applicable law and
          legitimate retention requirements. We may need to verify your identity before completing a request.
        </p>

        <h2>7. Children's privacy</h2>
        <p>AI BrandPlus is intended for business users and is not designed for children.</p>

        <h2>8. Changes to this policy</h2>
        <p>
          We may update this policy as our service or legal requirements change. We will publish the current
          version on this page and update the effective date when appropriate.
        </p>

        <h2>9. Contact</h2>
        <p>
          For privacy questions or data-related requests, contact us at{" "}
          <a href="mailto:dr.bhartidental@gmail.com">dr.bhartidental@gmail.com</a>.
        </p>
        <footer className="legal-footer">
          <a href="/terms">Terms of Service</a>
          <span aria-hidden="true">•</span>
          <a href="/login">Back to AI BrandPlus</a>
        </footer>
      </article>
    </main>
  );
}
