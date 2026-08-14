import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "../styles/landing.css";

/* ------------------------------------------------------------------ */
/*  Intersection Observer hook for scroll-triggered animations        */
/* ------------------------------------------------------------------ */
function useScrollAnimation() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = ref.current;
    if (!container) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("lp-visible");
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    const elements = container.querySelectorAll(".lp-animate");
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return ref;
}

/* ------------------------------------------------------------------ */
/*  Feature data                                                      */
/* ------------------------------------------------------------------ */
const FEATURES = [
  {
    icon: "🎫",
    title: "Incident Management",
    desc: "Create, track, and manage support incidents with full lifecycle control and audit history.",
  },
  {
    icon: "🧠",
    title: "RAG Knowledge Retrieval",
    desc: "Enterprise knowledge base powered by Pinecone vector search to surface relevant solutions.",
  },
  {
    icon: "🤖",
    title: "AI Copilot Analysis",
    desc: "LLM-powered analysis suggests resolutions, detects duplicates, and recommends next actions.",
  },
  {
    icon: "🔍",
    title: "Smart Search & Routing",
    desc: "Semantic search across incidents and knowledge to find related issues and patterns instantly.",
  },
  {
    icon: "📊",
    title: "Dashboard & Analytics",
    desc: "Real-time overview of open incidents, resolution rates, priority breakdowns, and team metrics.",
  },
];

const WORKFLOW_STEPS = [
  {
    num: "01",
    title: "A user reports an issue",
    desc: "A support ticket is submitted through the service desk with details about the problem, affected systems, and priority level.",
  },
  {
    num: "02",
    title: "The system loads context",
    desc: "SupportIQ automatically retrieves related incidents, knowledge articles, and historical resolution patterns using RAG-based vector search.",
  },
  {
    num: "03",
    title: "AI copilot analyzes the issue",
    desc: "The AI agent evaluates symptoms, matches against known solutions, and generates a recommended resolution with supporting evidence.",
  },
  {
    num: "04",
    title: "Duplicates and related issues detected",
    desc: "Semantic similarity analysis flags potential duplicate tickets and surfaces related incidents to avoid redundant work.",
  },
  {
    num: "05",
    title: "Agent reviews and acts",
    desc: "The support agent reviews the AI recommendation, modifies if needed, and applies the resolution — keeping human judgment in the loop.",
  },
  {
    num: "06",
    title: "Knowledge base grows",
    desc: "Resolved incidents feed back into the knowledge base, continuously improving future AI recommendations and search accuracy.",
  },
];

const WHY_CARDS = [
  {
    title: "AI handles the repetitive path first",
    desc: "Let the AI copilot absorb common requests, surface known solutions, and draft responses before the team steps in.",
  },
  {
    title: "Human oversight stays in the loop",
    desc: "Every AI recommendation requires human review. Agents can accept, modify, or reject suggestions with full context.",
  },
  {
    title: "Operations and knowledge stay connected",
    desc: "Keep incidents, knowledge articles, resolution patterns, and analytics connected in one unified support system.",
  },
];

/* ------------------------------------------------------------------ */
/*  LandingPage Component                                             */
/* ------------------------------------------------------------------ */
export default function LandingPage() {
  const containerRef = useScrollAnimation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="landing-page" ref={containerRef}>
      {/* ──────── Navbar ──────── */}
      <nav className="lp-navbar" id="lp-top">
        <div className="lp-navbar-inner">
          <Link to="/" className="lp-logo">
            <span className="lp-logo-icon">⚡</span>
            SupportIQ
          </Link>

          <button
            className="lp-mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? "✕" : "☰"}
          </button>

          <div className={`lp-nav-links${mobileMenuOpen ? " lp-nav-open" : ""}`}>
            <a href="#features" className="lp-nav-link" onClick={() => setMobileMenuOpen(false)}>
              Features
            </a>
            <a href="#workflow" className="lp-nav-link" onClick={() => setMobileMenuOpen(false)}>
              Workflow
            </a>
            <a
              href="https://github.com/redasaniharsh/SupportIQ"
              className="lp-nav-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub
            </a>
            <Link
              to="/dashboard"
              className="lp-nav-cta"
              onClick={() => setMobileMenuOpen(false)}
            >
              Open Dashboard →
            </Link>
          </div>
        </div>
      </nav>

      {/* ──────── Hero ──────── */}
      <section className="lp-hero">
        <div className="lp-hero-bg">
          <div className="lp-blob lp-blob-1" />
          <div className="lp-blob lp-blob-2" />
          <div className="lp-blob lp-blob-3" />
        </div>

        <div className="lp-hero-inner">
          <div className="lp-hero-content">
            <h1 className="lp-hero-title lp-animate lp-visible">
              AI-powered support,{" "}
              <span className="lp-hero-title-accent">human-ready operations</span>
            </h1>

            <p className="lp-hero-subtitle lp-animate lp-visible lp-animate-delay-1">
              SupportIQ is an AI-powered service desk that brings incident management,
              knowledge retrieval, AI copilot analysis, and smart routing into one
              unified platform.
            </p>

            <div className="lp-hero-actions lp-animate lp-visible lp-animate-delay-2">
              <Link to="/dashboard" className="lp-btn-primary">
                🚀 Open Dashboard
              </Link>
              <a
                href="https://github.com/redasaniharsh/SupportIQ"
                className="lp-btn-outline"
                target="_blank"
                rel="noopener noreferrer"
              >
                ⭐ View on GitHub
              </a>
            </div>

            <div className="lp-hero-pills lp-animate lp-visible lp-animate-delay-3">
              <div className="lp-hero-pill">
                <div className="lp-hero-pill-label">Support Model</div>
                <div className="lp-hero-pill-value">AI with human oversight</div>
              </div>
              <div className="lp-hero-pill">
                <div className="lp-hero-pill-label">Knowledge Layer</div>
                <div className="lp-hero-pill-value">RAG-backed answers</div>
              </div>
              <div className="lp-hero-pill">
                <div className="lp-hero-pill-label">Runtime Surface</div>
                <div className="lp-hero-pill-value">Search, analyze, resolve</div>
              </div>
            </div>
          </div>

          <div className="lp-hero-cards lp-animate lp-visible lp-animate-delay-2">
            <div className="lp-hero-card lp-hero-card-primary">
              <div className="lp-hero-card-icon">🔗</div>
              <div className="lp-hero-card-title">AI support, connected end to end</div>
              <div className="lp-hero-card-desc">
                Bring incidents, knowledge retrieval, AI analysis, and resolution
                tracking into one coordinated support flow.
              </div>
            </div>

            <div className="lp-hero-card lp-hero-card-secondary">
              <p>AI handles first replies, retrieval, and duplicate detection in one flow.</p>
              <p>Human review keeps every recommendation accountable.</p>
              <p>Tickets connect resolution data back to the knowledge base.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ──────── Features ──────── */}
      <section className="lp-section" id="features">
        <div className="lp-section-inner">
          <div className="lp-section-label lp-animate">System Scope</div>
          <h2 className="lp-section-title lp-animate lp-animate-delay-1">
            Cover the full support flow
          </h2>
          <p className="lp-section-subtitle lp-animate lp-animate-delay-2">
            From the first ticket to final resolution, the key steps stay inside one system.
          </p>

          <div className="lp-features-grid">
            {FEATURES.map((f, i) => (
              <div
                key={f.title}
                className={`lp-feature-card lp-animate lp-animate-delay-${Math.min(i + 1, 4)}`}
              >
                <div className="lp-feature-icon">{f.icon}</div>
                <div className="lp-feature-title">{f.title}</div>
                <div className="lp-feature-desc">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ──────── Workflow ──────── */}
      <section className="lp-section lp-workflow" id="workflow">
        <div className="lp-section-inner">
          <div className="lp-section-label lp-animate">Workflow</div>
          <h2 className="lp-section-title lp-animate lp-animate-delay-1">
            From first contact to resolution
          </h2>
          <p className="lp-section-subtitle lp-animate lp-animate-delay-2">
            From the first user message to AI analysis, human review, and ticket
            follow-up, the core flow stays in one system.
          </p>

          <div className="lp-workflow-steps">
            {WORKFLOW_STEPS.map((s, i) => (
              <div
                key={s.num}
                className={`lp-step lp-animate lp-animate-delay-${Math.min(i + 1, 4)}`}
              >
                <div className="lp-step-number">{s.num}</div>
                <div className="lp-step-content">
                  <div className="lp-step-title">{s.title}</div>
                  <div className="lp-step-desc">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ──────── Why SupportIQ ──────── */}
      <section className="lp-section lp-why" id="why">
        <div className="lp-section-inner">
          <div className="lp-section-label lp-animate">Why SupportIQ</div>
          <h2 className="lp-section-title lp-animate lp-animate-delay-1">
            Built for real service desk scenarios
          </h2>
          <p className="lp-section-subtitle lp-animate lp-animate-delay-2">
            Handle inbound tickets, AI analysis, knowledge retrieval, and follow-up
            work inside one system.
          </p>

          <div className="lp-why-grid">
            {WHY_CARDS.map((c, i) => (
              <div
                key={c.title}
                className={`lp-why-card lp-animate lp-animate-delay-${Math.min(i + 1, 3)}`}
              >
                <div className="lp-why-card-title">{c.title}</div>
                <div className="lp-why-card-desc">{c.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ──────── Positioning ──────── */}
      <section className="lp-section">
        <div className="lp-section-inner">
          <div className="lp-section-label lp-animate">Project Positioning</div>
          <h2 className="lp-section-title lp-animate lp-animate-delay-1">
            Not a chatbot, but a support system
          </h2>

          <div className="lp-positioning-grid">
            <div className="lp-position-card lp-animate lp-animate-delay-2">
              <p>
                This is not a chatbot shell. It is a support system where AI analysis,
                knowledge retrieval, incident tracking, and resolution flow are connected
                end to end.
              </p>
            </div>
            <div className="lp-position-card lp-animate lp-animate-delay-3">
              <p>
                The value is in making AI and human collaboration operable, observable,
                and maintainable for real support teams working under pressure.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ──────── CTA Banner ──────── */}
      <section className="lp-cta-banner">
        <div className="lp-cta-banner-inner">
          <div className="lp-cta-content">
            <div>
              <div className="lp-cta-label">Get Started</div>
              <h2 className="lp-cta-title">Ready to transform your support desk?</h2>
              <p className="lp-cta-desc">
                Explore the dashboard, inspect the architecture, and see how AI-powered
                analysis works in practice.
              </p>
            </div>
            <div className="lp-cta-actions">
              <Link to="/dashboard" className="lp-btn-white">
                🚀 Open Dashboard
              </Link>
              <a
                href="https://github.com/redasaniharsh/SupportIQ"
                className="lp-btn-ghost"
                target="_blank"
                rel="noopener noreferrer"
              >
                ⭐ View on GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ──────── Footer ──────── */}
      <footer className="lp-footer">
        <p>
          Built by{" "}
          <a
            href="https://github.com/redasaniharsh"
            target="_blank"
            rel="noopener noreferrer"
          >
            Harsh Redasani
          </a>{" "}
          · SupportIQ © {new Date().getFullYear()}
        </p>
      </footer>
    </div>
  );
}
