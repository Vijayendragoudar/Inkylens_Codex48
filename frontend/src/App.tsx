import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  api,
  Brand,
  DecisionState,
  Finding,
  GuidelineRule,
  Review,
  ReviewHistoryItem,
  RuleType,
} from "./api";

const DEMO_COPY =
  "Our REVOLUTIONARY coffee plan gives every customer GUARANTEED energy. Join today for the best cup in the city.";

const ruleTypeLabels: Record<RuleType, string> = {
  forbidden_term: "Forbidden term",
  preferred_term: "Preferred replacement",
  tone: "Tone guidance",
  approved_fact: "Approved fact",
  claim_constraint: "Claim restriction",
};

const decisionLabels: Record<DecisionState, string> = {
  open: "Open",
  resolved: "Resolved",
  dismissed: "Dismissed",
  accepted_exception: "Accepted exception",
};

function messageFor(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function blankRule(index: number): GuidelineRule {
  return {
    rule_key: `RULE-${String(index + 1).padStart(3, "0")}`,
    rule_type: "forbidden_term",
    title: "New guidance",
    content: "",
    replacement: null,
  };
}

export default function App() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [history, setHistory] = useState<ReviewHistoryItem[]>([]);
  const [review, setReview] = useState<Review | null>(null);
  const [draft, setDraft] = useState(DEMO_COPY);
  const [newBrandName, setNewBrandName] = useState("");
  const [aiDisclosureAccepted, setAiDisclosureAccepted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    void bootstrap();
  }, []);

  async function bootstrap() {
    setLoading(true);
    setError(null);
    try {
      const availableBrands = await api.listBrands();
      setBrands(availableBrands);
      if (availableBrands.length > 0) {
        await selectBrand(availableBrands[0].id);
      }
    } catch (caught) {
      setError(`Could not load the demo: ${messageFor(caught)}`);
    } finally {
      setLoading(false);
    }
  }

  async function selectBrand(brandId: string) {
    setError(null);
    setNotice(null);
    try {
      const [nextBrand, nextHistory] = await Promise.all([
        api.getBrand(brandId),
        api.listReviewHistory(brandId),
      ]);
      setBrand(nextBrand);
      setHistory(nextHistory);
      setReview(null);
      setAiDisclosureAccepted(false);
    } catch (caught) {
      setError(`Could not open this brand: ${messageFor(caught)}`);
    }
  }

  async function refreshBrandAndHistory(brandId: string) {
    const [nextBrand, nextHistory] = await Promise.all([
      api.getBrand(brandId),
      api.listReviewHistory(brandId),
    ]);
    setBrand(nextBrand);
    setBrands((current) => current.map((item) => (item.id === brandId ? nextBrand : item)));
    setHistory(nextHistory);
  }

  async function createBrand(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = newBrandName.trim();
    if (!name) {
      setError("Enter a name for the new brand profile.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await api.createBrand(name);
      setBrands((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name)));
      setNewBrandName("");
      await selectBrand(created.id);
      setNotice("New brand profile created. Add its organisation-supplied guidance before reviewing copy.");
    } catch (caught) {
      setError(`Could not create the brand: ${messageFor(caught)}`);
    } finally {
      setSaving(false);
    }
  }

  function updateBrandField(field: "name" | "description", value: string) {
    if (!brand) return;
    setBrand({ ...brand, [field]: value });
  }

  function updateRule(index: number, patch: Partial<GuidelineRule>) {
    if (!brand) return;
    setBrand({
      ...brand,
      guidelines: brand.guidelines.map((rule, ruleIndex) =>
        ruleIndex === index ? { ...rule, ...patch } : rule,
      ),
    });
  }

  function addRule() {
    if (!brand) return;
    setBrand({ ...brand, guidelines: [...brand.guidelines, blankRule(brand.guidelines.length)] });
  }

  function removeRule(index: number) {
    if (!brand) return;
    setBrand({ ...brand, guidelines: brand.guidelines.filter((_, ruleIndex) => ruleIndex !== index) });
  }

  async function saveBrand() {
    if (!brand) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const saved = await api.updateBrand(brand);
      setBrand(saved);
      setBrands((current) => current.map((item) => (item.id === saved.id ? saved : item)));
      setNotice("Brand guidance saved. Future findings will link back to these rules.");
    } catch (caught) {
      setError(`Could not save guidance: ${messageFor(caught)}`);
    } finally {
      setSaving(false);
    }
  }

  async function runReview() {
    if (!brand) return;
    if (!draft.trim()) {
      setError("Paste or write content before running a review.");
      return;
    }
    if (!aiDisclosureAccepted) {
      setError("Confirm the AI-processing disclosure before submitting content for review.");
      return;
    }
    setReviewing(true);
    setError(null);
    setNotice(null);
    try {
      const nextReview = await api.createReview(brand.id, draft, review?.id);
      setReview(nextReview);
      await refreshBrandAndHistory(brand.id);
      setNotice(
        nextReview.ai_status === "completed"
          ? "Review complete. Confirm each suggestion before making an editorial decision."
          : "Deterministic review complete. AI-assisted analysis is unavailable, and that limitation is shown below.",
      );
    } catch (caught) {
      setError(`Could not run the review: ${messageFor(caught)}`);
    } finally {
      setReviewing(false);
    }
  }

  async function openHistoryItem(item: ReviewHistoryItem) {
    setError(null);
    try {
      const savedReview = await api.getReview(item.id);
      setReview(savedReview);
      setDraft(savedReview.submission_text);
      setNotice(`Viewing saved revision ${savedReview.revision_number}.`);
    } catch (caught) {
      setError(`Could not open that saved review: ${messageFor(caught)}`);
    }
  }

  async function updateDecision(finding: Finding, state: DecisionState) {
    setError(null);
    try {
      const decision = await api.updateDecision(finding.id, state, finding.decision?.note || "");
      setReview((current) =>
        current
          ? {
              ...current,
              findings: current.findings.map((item) =>
                item.id === finding.id ? { ...item, decision } : item,
              ),
            }
          : current,
      );
    } catch (caught) {
      setError(`Could not save the reviewer decision: ${messageFor(caught)}`);
    }
  }

  const counts = useMemo(() => {
    const initial = { high: 0, medium: 0, low: 0 };
    for (const finding of review?.findings || []) initial[finding.severity] += 1;
    return initial;
  }, [review]);

  if (loading) {
    return <main className="loading-screen">Loading the Inkylens demo…</main>;
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">INKYLENS / ROUND 2 MVP</p>
          <h1>Brand review, made explainable.</h1>
          <p className="hero-copy">
            Check copy against organisation-supplied guidance, preserve the evidence, and keep the
            final editorial decision human.
          </p>
        </div>
        <div className="hero-status" aria-label="Demo status">
          <span className="status-dot" /> Anonymous demo workspace
        </div>
      </header>

      <section className="judge-route" aria-labelledby="judge-route-title">
        <div>
          <p className="eyebrow" id="judge-route-title">JUDGE ROUTE</p>
          <strong>1. Edit guidance</strong>
          <strong>2. Review copy</strong>
          <strong>3. Record a decision</strong>
          <strong>4. Reopen history</strong>
        </div>
        <p>
          This is a fictional sample brand. Findings are assistance for a human reviewer, not a
          compliance certification.
        </p>
      </section>

      {error && <div className="message error" role="alert">{error}</div>}
      {notice && <div className="message notice" role="status">{notice}</div>}

      <section className="brand-switcher" aria-label="Brand profile controls">
        <label>
          Active brand
          <select
            value={brand?.id || ""}
            onChange={(event) => void selectBrand(event.target.value)}
            disabled={!brand}
          >
            {brands.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <form onSubmit={createBrand} className="new-brand-form">
          <label>
            New profile
            <input
              value={newBrandName}
              onChange={(event) => setNewBrandName(event.target.value)}
              placeholder="e.g. Studio North"
              maxLength={120}
            />
          </label>
          <button className="secondary-button" type="submit" disabled={saving}>Create profile</button>
        </form>
      </section>

      {brand && (
        <div className="workspace-grid">
          <section className="card guideline-card" aria-labelledby="guidelines-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">SOURCE OF TRUTH</p>
                <h2 id="guidelines-title">Brand guidance</h2>
              </div>
              <button className="primary-button" type="button" onClick={() => void saveBrand()} disabled={saving}>
                {saving ? "Saving…" : "Save guidance"}
              </button>
            </div>

            <label>
              Brand name
              <input value={brand.name} onChange={(event) => updateBrandField("name", event.target.value)} maxLength={120} />
            </label>
            <label>
              Context for reviewers
              <textarea value={brand.description} onChange={(event) => updateBrandField("description", event.target.value)} rows={2} maxLength={2000} />
            </label>

            <div className="rule-list">
              {brand.guidelines.map((rule, index) => (
                <article className="rule-editor" key={`${rule.id || "new"}-${index}`}>
                  <div className="rule-editor-topline">
                    <strong>{rule.rule_key || "New rule"}</strong>
                    <button className="text-button danger" type="button" onClick={() => removeRule(index)}>Remove</button>
                  </div>
                  <div className="rule-grid">
                    <label>
                      Rule key
                      <input value={rule.rule_key} onChange={(event) => updateRule(index, { rule_key: event.target.value })} maxLength={40} />
                    </label>
                    <label>
                      Type
                      <select value={rule.rule_type} onChange={(event) => updateRule(index, { rule_type: event.target.value as RuleType })}>
                        {Object.entries(ruleTypeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                      </select>
                    </label>
                  </div>
                  <label>
                    Title
                    <input value={rule.title} onChange={(event) => updateRule(index, { title: event.target.value })} maxLength={140} />
                  </label>
                  <label>
                    {rule.rule_type === "preferred_term" ? "Phrase to replace" : "Guidance or phrase"}
                    <textarea value={rule.content} onChange={(event) => updateRule(index, { content: event.target.value })} rows={2} maxLength={2000} />
                  </label>
                  {(rule.rule_type === "forbidden_term" || rule.rule_type === "preferred_term") && (
                    <label>
                      {rule.rule_type === "preferred_term" ? "Preferred replacement" : "Suggested correction"}
                      <input value={rule.replacement || ""} onChange={(event) => updateRule(index, { replacement: event.target.value || null })} maxLength={200} />
                    </label>
                  )}
                </article>
              ))}
            </div>
            <button className="secondary-button add-rule" type="button" onClick={addRule}>+ Add guideline</button>
          </section>

          <section className="card review-card" aria-labelledby="review-title">
            <div className="section-heading">
              <div>
                <p className="eyebrow">PRE-PUBLISH CHECK</p>
                <h2 id="review-title">Review content</h2>
              </div>
              {review && <span className="revision-chip">Revision {review.revision_number}</span>}
            </div>

            <label>
              Copy to review
              <textarea
                className="content-input"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                rows={10}
                maxLength={20000}
                aria-describedby="privacy-disclosure"
              />
            </label>
            <p className="character-count">{draft.length.toLocaleString()} / 20,000 characters</p>
            <label className="disclosure" id="privacy-disclosure">
              <input type="checkbox" checked={aiDisclosureAccepted} onChange={(event) => setAiDisclosureAccepted(event.target.checked)} />
              <span>
                I understand that, when configured, this content and the necessary approved guidance
                are sent to the configured AI provider. Do not submit confidential customer content.
              </span>
            </label>
            <button className="primary-button full-width" type="button" onClick={() => void runReview()} disabled={reviewing}>
              {reviewing ? "Reviewing…" : review ? "Save revision & recheck" : "Run brand review"}
            </button>

            {review && (
              <div className="review-result" aria-live="polite">
                <div className="result-summary">
                  <div>
                    <p className="eyebrow">REVIEW RESULT</p>
                    <h3>{review.findings.length} finding{review.findings.length === 1 ? "" : "s"}</h3>
                  </div>
                  <div className="severity-summary" aria-label="Findings by severity">
                    <span className="severity high">{counts.high} high</span>
                    <span className="severity medium">{counts.medium} medium</span>
                    <span className="severity low">{counts.low} low</span>
                  </div>
                </div>

                <div className={`ai-state ${review.ai_status}`}>
                  <strong>AI-assisted analysis: {review.ai_status === "completed" ? "available" : "unavailable"}</strong>
                  <span>{review.ai_error || "Structured AI findings were validated against the supplied guidance."}</span>
                </div>

                <div className="findings-list">
                  {review.findings.length === 0 && <p className="empty-state">No findings were generated. A human reviewer should still make the final decision.</p>}
                  {review.findings.map((finding) => (
                    <article className="finding" key={finding.id}>
                      <div className="finding-topline">
                        <div>
                          <span className={`severity ${finding.severity}`}>{finding.severity}</span>
                          <span className="source-chip">{finding.source === "deterministic" ? "Rule check" : "AI-assisted"}</span>
                        </div>
                        <select
                          aria-label={`Reviewer decision for ${finding.label}`}
                          value={finding.decision?.state || "open"}
                          onChange={(event) => void updateDecision(finding, event.target.value as DecisionState)}
                        >
                          {Object.entries(decisionLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                        </select>
                      </div>
                      <h4>{finding.label}</h4>
                      <p>{finding.explanation}</p>
                      <blockquote>{finding.excerpt}</blockquote>
                      <p className="suggestion"><strong>Suggested correction:</strong> {finding.suggestion}</p>
                      <p className="rule-reference">
                        {finding.rule_keys.length > 0
                          ? `Source rule${finding.rule_keys.length > 1 ? "s" : ""}: ${finding.rule_keys.join(", ")}`
                          : "No supplied rule directly supports this finding; human verification is required."}
                      </p>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      {brand && (
        <section className="card history-card" aria-labelledby="history-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">AUDIT TRAIL</p>
              <h2 id="history-title">Saved review history</h2>
            </div>
            <span className="history-count">{history.length} saved</span>
          </div>
          {history.length === 0 ? (
            <p className="empty-state">Run a review to create the first saved revision.</p>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <button className="history-item" type="button" key={item.id} onClick={() => void openHistoryItem(item)}>
                  <span className="history-revision">Revision {item.revision_number}</span>
                  <span className="history-excerpt">{item.excerpt}</span>
                  <span>{item.finding_count} findings · {formatDate(item.created_at)}</span>
                </button>
              ))}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
