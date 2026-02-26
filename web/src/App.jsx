// App.jsx
import { useEffect, useMemo, useRef, useState } from "react";
import TypingHelp from "./TypingHelp";
import "./App.css";

const API_BASE_RAW = import.meta.env.VITE_API_BASE_URL;
const API_BASE = API_BASE_RAW.endsWith("/") ? API_BASE_RAW : API_BASE_RAW + "/";
const NORMALIZE_URL = API_BASE + "normalize";

const DEFAULT_LAT = "";
const DEFAULT_AM = "";

// -input sizing
const MAX_CHARS = 500; // hard cap
const AUTO_RESIZE_UP_TO = 200; // autosize up to this; beyond -> lock height + scroll
const MIN_ROWS = 2;
const MAX_ROWS = 10;

const HABIT_STRENGTH = 0.85;

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

async function copyToClipboard(text) {
  await navigator.clipboard.writeText(text);
}

function tokenizeForReview(text) {
  const re = /(\s+)|([\p{L}\p{N}'_]+)|([^\s\p{L}\p{N}'_]+)/gu;
  const tokens = [];
  for (const m of text.matchAll(re)) {
    if (m[1]) tokens.push({ kind: "ws", text: m[1] });
    else if (m[2]) tokens.push({ kind: "word", text: m[2] });
    else if (m[3]) tokens.push({ kind: "punct", text: m[3] });
  }
  return tokens;
}

function tokensToText(tokens) {
  return (tokens ?? []).map((t) => t.text).join("");
}

function extractWords(text) {
  return (tokenizeForReview(text) ?? [])
    .filter((t) => t.kind === "word")
    .map((t) => t.text);
}

function useAutosizeWithThresholdLock(
  ref,
  value,
  {
    enabled = true, // if false, do nothing
    threshold = AUTO_RESIZE_UP_TO,
    minRows = MIN_ROWS,
    maxRows = MAX_ROWS,
    lockHeightRef, // useRef<number|null>
  } = {}
) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!enabled) return;

    const len = (value ?? "").length;

    const cs = window.getComputedStyle(el);
    const lineHeight = parseFloat(cs.lineHeight || "20") || 20;
    const paddingTop = parseFloat(cs.paddingTop || "0") || 0;
    const paddingBottom = parseFloat(cs.paddingBottom || "0") || 0;
    const borderTop = parseFloat(cs.borderTopWidth || "0") || 0;
    const borderBottom = parseFloat(cs.borderBottomWidth || "0") || 0;

    const minH =
      minRows * lineHeight +
      paddingTop +
      paddingBottom +
      borderTop +
      borderBottom;
    const maxH =
      maxRows * lineHeight +
      paddingTop +
      paddingBottom +
      borderTop +
      borderBottom;

    // if we are at/under threshold -> autosize and clear any old lock.
    if (len <= threshold) {
      if (lockHeightRef) lockHeightRef.current = null;

      el.style.height = "auto";
      el.style.overflowY = "hidden";

      const nextH = Math.min(Math.max(el.scrollHeight, minH), maxH);
      el.style.height = `${nextH}px`;
      el.style.overflowY = el.scrollHeight > maxH ? "auto" : "hidden";
      return;
    }

    // above threshold:
    // lock height to whatever we had when we first crossed the threshold.
    // If no lock yet, compute an autosized height and lock it.
    if (!lockHeightRef) {
      // fallback: lock to maxH if no ref provided
      el.style.height = `${maxH}px`;
      el.style.overflowY = "auto";
      return;
    }

    if (lockHeightRef.current == null) {
      // measure the "natural" height right now (bounded) and freeze it
      el.style.height = "auto";
      el.style.overflowY = "hidden";

      const nextH = Math.min(Math.max(el.scrollHeight, minH), maxH);
      lockHeightRef.current = nextH;
    }

    el.style.height = `${lockHeightRef.current}px`;
    el.style.overflowY = "auto";
  }, [ref, value, enabled, threshold, minRows, maxRows, lockHeightRef]);
}

export default function App() {
  // mode: "lat_to_am" or "am_to_lat"
  const [mode, setMode] = useState("lat_to_am");

  // canonical inputs
  const [latinText, setLatinText] = useState(DEFAULT_LAT);
  const [amText, setAmText] = useState(DEFAULT_AM);

  // output state ( for debugging / future use)
  const [result, setResult] = useState(null);

  // review state (Amharic output only, for lat_to_am)
  const [reviewMode, setReviewMode] = useState(false);
  const [outTokens, setOutTokens] = useState(null);

  // Store the Latin word list that produced the current output
  const [latinWords, setLatinWords] = useState([]);

  // poppers
  const [reviewOne, setReviewOne] = useState(null);
  const [reviewPunct, setReviewPunct] = useState(null);
  const [popover, setPopover] = useState({ open: false, x: 0, y: 0 });

  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const latinIsInput = mode === "lat_to_am";
  const amIsInput = mode === "am_to_lat";

  const latinLabel = `Latin ${latinIsInput ? "(input)" : "(output)"}`;
  const amLabel = `Amharic ${amIsInput ? "(input)" : "(output)"}`;

  // refs for autosizing
  const latinTaRef = useRef(null);
  const amTaRef = useRef(null);

  // locks -- height at threshold (pixel height, not rows)
  const latinLockHRef = useRef(null);
  const amLockHRef = useRef(null);

  const finalAm = useMemo(() => {
    if (mode !== "lat_to_am") return amText;
    if (outTokens) return tokensToText(outTokens);
    return amText;
  }, [mode, amText, outTokens]);

  // autosize Latin always (textarea always mounted)
  useAutosizeWithThresholdLock(latinTaRef, latinText, {
    enabled: true,
    lockHeightRef: latinLockHRef,
  });

  // Autosize Amharic only when textarea exists (not review div)
  useAutosizeWithThresholdLock(amTaRef, finalAm, {
    enabled: !(mode === "lat_to_am" && reviewMode),
    lockHeightRef: amLockHRef,
  });

  // ESC key closes popovers; also ends review mode
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key !== "Escape") return;
      closePopover();
      if (reviewMode) {
        setReviewMode(false);
        setAmText((prev) => prev);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [reviewMode]);

  function resetReviewState() {
    setReviewMode(false);
    setOutTokens(null);
    setReviewOne(null);
    setReviewPunct(null);
    setPopover({ open: false, x: 0, y: 0 });
  }

  function closePopover() {
    setReviewOne(null);
    setReviewPunct(null);
    setPopover({ open: false, x: 0, y: 0 });
  }

  async function runNormalize() {
    setErr("");
    setLoading(true);
    setResult(null);
    closePopover();
    resetReviewState();

    try {
      const text = latinIsInput ? latinText : amText;

      const options =
        mode === "am_to_lat"
          ? { return_latin_std: true, return_alternatives: false }
          : {
              return_alternatives: true,
              max_alternatives: 5,
              latin_mode: "auto",
              habit_strength: HABIT_STRENGTH,
            };

      const data = await fetchJson(NORMALIZE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, options }),
      });

      setResult(data);

      if (mode === "lat_to_am") {
        const bestAm = data.text_am ?? "";
        setAmText(bestAm);
        setOutTokens(tokenizeForReview(bestAm));
        setLatinWords(extractWords(latinText));
      } else {
        setLatinText(data.latin_std ?? "");
      }
    } catch (e) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  function tokenIndexToWordOrdinal(tokens, tokenIdx) {
    let ord = 0;
    for (let i = 0; i < tokenIdx; i++) {
      if (tokens[i]?.kind === "word") ord += 1;
    }
    return ord;
  }

  async function openWordReview(tokenIdx, evt) {
    if (!reviewMode) return;
    if (mode !== "lat_to_am") return;
    if (!outTokens || tokenIdx == null) return;

    const tok = outTokens[tokenIdx];
    if (!tok || tok.kind !== "word") return;

    if (reviewOne || reviewPunct) closePopover();

    const rect = evt.currentTarget.getBoundingClientRect();
    const x = rect.left;
    const y = rect.bottom + 6;

    const wordOrdinal = tokenIndexToWordOrdinal(outTokens, tokenIdx);
    const srcLatin = latinWords[wordOrdinal] || "";
    const srcAm = tok.text;

    if (!srcLatin) {
      setErr(
        "Review mapping failed (Latin word missing for this output word). Try running again, or ensure input/output tokenization aligns."
      );
      return;
    }

    try {
      setLoading(true);

      const data = await fetchJson(NORMALIZE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: srcLatin,
          options: {
            return_alternatives: true,
            max_alternatives: 10,
            latin_mode: "auto",
            habit_strength: HABIT_STRENGTH,
          },
        }),
      });

      const choices = [];
      const seen = new Set();

      const push = (label, text_am) => {
        if (!text_am) return;
        if (seen.has(text_am)) return;
        seen.add(text_am);
        choices.push({ label, text_am });
      };

      push("Best", data.text_am);
      for (const a of data.alternatives ?? []) push("Alt", a.text_am);
      push("Current", srcAm);

      setReviewOne({
        idxToken: tokenIdx,
        wordOrdinal,
        srcLatin,
        srcAm,
        choices,
      });
      setPopover({ open: true, x, y });
    } catch (e) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  function openPunctReview(tokenIdx, evt) {
    if (!reviewMode) return;
    if (mode !== "lat_to_am") return;
    if (!outTokens || tokenIdx == null) return;

    const tok = outTokens[tokenIdx];
    if (!tok || tok.kind !== "punct") return;

    if (!tok.text.includes("።") && !tok.text.includes(".")) return;

    if (reviewOne || reviewPunct) closePopover();

    const rect = evt.currentTarget.getBoundingClientRect();
    const x = rect.left;
    const y = rect.bottom + 6;

    const src = tok.text;
    const choices = [{ label: "Current", text: src }];

    if (src.includes("።"))
      choices.push({ label: "Use .", text: src.replaceAll("።", ".") });
    if (src.includes(".")) {
      choices.push({ label: "Use ።", text: src.replaceAll(".", "።") });
      choices.push({ label: "Keep .", text: src });
    }

    if (choices.length <= 1) return;

    setReviewPunct({ idxToken: tokenIdx, src, choices });
    setPopover({ open: true, x, y });
  }

  const latinCountLabel = `${latinText.length}/${MAX_CHARS}`;
  const amCountLabel = `${finalAm.length}/${MAX_CHARS}`;

  const latinOver = latinText.length > AUTO_RESIZE_UP_TO;
  const amOver = finalAm.length > AUTO_RESIZE_UP_TO;

  return (
    <div
      className="app"
      onClick={() => {
        if (popover.open) closePopover();
      }}
    >
      <TypingHelp />

      <h2>Amharic Normalizer (AN-v0)</h2>

      <div className="panel">
        <div className="button-row" style={{ marginTop: 0 }}>
          <button
            className={mode === "lat_to_am" ? "active-toggle" : "inactive-toggle"}
            onClick={() => {
              setMode("lat_to_am");
              setErr("");
              resetReviewState();
              setResult(null);
            }}
          >
            Latin → Ethiopic
          </button>
          <button
            className={mode === "am_to_lat" ? "active-toggle" : "inactive-toggle"}
            onClick={() => {
              setMode("am_to_lat");
              setErr("");
              resetReviewState();
              setResult(null);
            }}
          >
            Latin ← Ethiopic
          </button>
        </div>
      </div>

      <div className="grid-2">
        {/* LEFT: Latin box */}
        <div className="panel io-panel">
          <h3>{latinLabel}</h3>

          <textarea
            ref={latinTaRef}
            className="text-surface"
            rows={MIN_ROWS}
            maxLength={MAX_CHARS}
            value={latinText}
            onChange={(e) => latinIsInput && setLatinText(e.target.value)}
            readOnly={!latinIsInput}
            placeholder={latinIsInput ? "Type Latin…\ne.g. selam! _nkoan dehna metxu!" : ""}
            style={{ resize: "none" }}
          />

          <div className="io-footer">
            <div className="hintline hintline--slot">
              {latinIsInput ? (
                <>
                  {latinCountLabel}
                  {latinOver && (
                    <>
                      {" "}
                      · fixed display size after {AUTO_RESIZE_UP_TO} chars (scroll enabled)
                    </>
                  )}
                </>
              ) : (
                "\u00A0"
              )}
            </div>

            <div className="button-row io-actions">
              {latinIsInput ? (
                <button onClick={runNormalize} disabled={loading || !latinText.trim()}>
                  {loading ? "Running…" : "Run"}
                </button>
              ) : (
                <button
                  className="secondary"
                  onClick={async () => await copyToClipboard(latinText)}
                  disabled={!latinText.trim()}
                >
                  Copy
                </button>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: Amharic box */}
        <div className="panel io-panel">
          <h3>{amLabel}</h3>

          {mode === "lat_to_am" && reviewMode ? (
            <div className="review-surface text-surface">
              {(outTokens ?? tokenizeForReview(finalAm)).map((t, idx) =>
                t.kind === "ws" ? (
                  <span key={idx} style={{ whiteSpace: "pre-wrap" }}>
                    {t.text}
                  </span>
                ) : t.kind === "word" ? (
                  <span
                    key={idx}
                    className="word"
                    title="Click to review this word"
                    onClick={(e) => {
                      e.stopPropagation();
                      openWordReview(idx, e);
                    }}
                  >
                    {t.text}
                  </span>
                ) : (
                  <span
                    key={idx}
                    className="word"
                    title="Click to edit punctuation"
                    onClick={(e) => {
                      e.stopPropagation();
                      openPunctReview(idx, e);
                    }}
                  >
                    {t.text}
                  </span>
                )
              )}
            </div>
          ) : (
            <textarea
              ref={amTaRef}
              className="text-surface"
              rows={MIN_ROWS}
              maxLength={MAX_CHARS}
              value={finalAm}
              onChange={(e) => amIsInput && setAmText(e.target.value)}
              readOnly={!amIsInput}
              placeholder={amIsInput ? "Paste Amharic text…\ne.g. ሰላም! እንኳን ደህና መጡ!" : ""}
              style={{ resize: "none" }}
            />
          )}

          <div className="io-footer">
            <div className="hintline hintline--slot">
              {amIsInput ? (
                <>
                  {amCountLabel}
                  {amOver && (
                    <>
                      {" "}
                      · fixed display size after {AUTO_RESIZE_UP_TO} chars (scroll enabled)
                    </>
                  )}
                </>
              ) : (
                "\u00A0"
              )}
            </div>

            <div className="button-row io-actions">
              {amIsInput ? (
                <button onClick={runNormalize} disabled={loading || !amText.trim()}>
                  {loading ? "Running…" : "Run"}
                </button>
              ) : (
                <>
                  <button
                    className="secondary"
                    onClick={async (e) => {
                      e.stopPropagation();
                      await copyToClipboard(finalAm);
                    }}
                    disabled={!finalAm.trim()}
                  >
                    Copy
                  </button>

                  {mode === "lat_to_am" && (
                    <>
                      {!reviewMode ? (
                        <button
                          className="secondary"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (outTokens == null) setOutTokens(tokenizeForReview(finalAm));
                            setReviewMode(true);
                          }}
                          disabled={!finalAm.trim()}
                        >
                          Enter review
                        </button>
                      ) : (
                        <button
                          className="secondary"
                          onClick={(e) => {
                            e.stopPropagation();
                            closePopover();
                            setReviewMode(false);
                            setAmText(finalAm);
                          }}
                        >
                          Exit review
                        </button>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          </div>

          {popover.open && (reviewOne || reviewPunct) ? (
            <div
              className="popover"
              style={{ left: popover.x, top: popover.y }}
              onClick={(e) => e.stopPropagation()}
            >
              {reviewOne ? (
                <>
                  <div className="mono soft" style={{ marginBottom: 6 }}>
                    {reviewOne.srcLatin} → {reviewOne.srcAm}
                  </div>

                  {reviewOne.choices.map((c, k) => (
                    <button
                      key={k}
                      className="popover-item"
                      onClick={() => {
                        setOutTokens((prev) => {
                          const base = prev ?? tokenizeForReview(finalAm);
                          return base.map((tok, i) =>
                            i === reviewOne.idxToken ? { ...tok, text: c.text_am } : tok
                          );
                        });
                        closePopover();
                      }}
                    >
                      {c.label === "Best"
                        ? "Best: "
                        : c.label === "Current"
                        ? "Current: "
                        : "Alt: "}
                      {c.text_am}
                    </button>
                  ))}

                  <div className="hintline" style={{ marginTop: 6 }}>
                    Alternatives come from the original Latin word (not Ethiopic normalization).
                  </div>
                </>
              ) : (
                <>
                  <div className="mono soft" style={{ marginBottom: 6 }}>
                    Punctuation: {reviewPunct.src}
                  </div>

                  {reviewPunct.choices.map((c, k) => (
                    <button
                      key={k}
                      className="popover-item"
                      onClick={() => {
                        setOutTokens((prev) => {
                          const base = prev ?? tokenizeForReview(finalAm);
                          return base.map((tok, i) =>
                            i === reviewPunct.idxToken ? { ...tok, text: c.text } : tok
                          );
                        });
                        closePopover();
                      }}
                    >
                      {c.label}: {c.text}
                    </button>
                  ))}

                  <div className="hintline" style={{ marginTop: 6 }}>
                    Full stop style is user-editable (no automatic conversion).
                  </div>
                </>
              )}

              <div className="button-row" style={{ marginTop: 8 }}>
                <button className="secondary" onClick={closePopover}>
                  Cancel
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {err && (
        <div className="panel">
          <pre className="error">{err}</pre>
        </div>
      )}
    </div>
  );
}

