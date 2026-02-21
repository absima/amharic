// App.jsx
import { useMemo, useState } from "react";
import TypingHelp from "./TypingHelp";
import "./App.css";

const API_BASE_RAW = import.meta.env.VITE_API_BASE_URL;
const API_BASE = API_BASE_RAW.endsWith("/") ? API_BASE_RAW : API_BASE_RAW + "/";
const NORMALIZE_URL = API_BASE + "normalize";

const DEFAULT_LAT = "selam! EnkWan dehna meTu!";
const DEFAULT_AM = "ሰላም! እንኳን ደህና መጡ!";

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

async function copyToClipboard(text) {
  await navigator.clipboard.writeText(text);
}

/**
 * Review tokenization:
 * - ws: whitespace
 * - word: letters/digits/'/_ (any script via \p{L}\p{N})
 * - punct: everything else (including ። and .)
 *
 * This allows punctuation to be clicked/edited independently in review mode.
 */
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

export default function App() {
  // mode: "lat_to_am" | "am_to_lat"
  const [mode, setMode] = useState("lat_to_am");

  // canonical “current inputs”
  const [latinText, setLatinText] = useState(DEFAULT_LAT);
  const [amText, setAmText] = useState(DEFAULT_AM);

  // slider
  const [habitStrength, setHabitStrength] = useState(0.85);

  // output state
  const [result, setResult] = useState(null);

  // review state (Amharic output only, for lat_to_am)
  const [reviewMode, setReviewMode] = useState(false);
  const [outTokens, setOutTokens] = useState(null);

  // IMPORTANT: store the Latin word list that produced the current output
  // We use this to fetch alternatives during review, since Ethiopic->Ethiopic is deterministic.
  const [latinWords, setLatinWords] = useState([]);

  // Single active review popover (word alternatives)
  const [reviewOne, setReviewOne] = useState(null); // { idxToken, wordOrdinal, srcLatin, srcAm, choices:[{label,text_am}] }

  // Single active punctuation popover (minimal: full stop only)
  const [reviewPunct, setReviewPunct] = useState(null); // { idxToken, src, choices:[{label,text}] }

  const [popover, setPopover] = useState({ open: false, x: 0, y: 0 });

  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const latinIsInput = mode === "lat_to_am";
  const amIsInput = mode === "am_to_lat";

  const latinLabel = `Latin ${latinIsInput ? "(input)" : "(output)"}`;
  const amLabel = `Amharic ${amIsInput ? "(input)" : "(output)"}`;

  function resetReviewState() {
    setReviewMode(false);
    setOutTokens(null);
    setReviewOne(null);
    setReviewPunct(null);
    setPopover({ open: false, x: 0, y: 0 });
    // latinWords persists until next RUN in lat_to_am
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
              habit_strength: habitStrength,
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

        // Store Latin word list for review mapping
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
    // Count how many word tokens occur before tokenIdx
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

    // allow switching focus by closing current popover
    if (reviewOne || reviewPunct) closePopover();

    const rect = evt.currentTarget.getBoundingClientRect();
    const x = rect.left;
    const y = rect.bottom + 6;

    const wordOrdinal = tokenIndexToWordOrdinal(outTokens, tokenIdx);
    const srcLatin = latinWords[wordOrdinal] || "";
    const srcAm = tok.text;

    // If we can't map back to a Latin word, we cannot fetch ambiguity alternatives.
    if (!srcLatin) {
      setErr(
        "Review mapping failed (Latin word missing for this output word). Try running again, or ensure input/output tokenization aligns."
      );
      return;
    }

    try {
      setLoading(true);

      // Fetch alternatives using the *Latin source word*, not the Ethiopic output word.
      const data = await fetchJson(NORMALIZE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: srcLatin,
          options: {
            return_alternatives: true,
            max_alternatives: 10,
            latin_mode: "auto",
            habit_strength: habitStrength,
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

      // Ensure current shown Amharic is selectable even if it isn't in the candidate set
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

  /**
   * Minimal punctuation review: allow toggling sentence full-stop rendering.
   *
   * Requirement you stated:
   * - From Latin -> Amharic output, user may prefer "." instead of "።".
   * - But "." in output could be a real ASCII period (decimal/abbr), so we must NOT blindly
   *   convert "." to "።". We only offer controlled replacements on the clicked token.
   *
   * Therefore:
   * - If token contains "።", offer "። → ." (always safe).
   * - If token contains ".", offer a CHOICE: keep "." OR convert only those periods to "።".
   *   (User-driven, explicit.)
   */
  function openPunctReview(tokenIdx, evt) {
    if (!reviewMode) return;
    if (mode !== "lat_to_am") return;
    if (!outTokens || tokenIdx == null) return;

    const tok = outTokens[tokenIdx];
    if (!tok || tok.kind !== "punct") return;

    // Only care about tokens that include ። or .
    if (!tok.text.includes("።") && !tok.text.includes(".")) return;

    // allow switching focus by closing current popover
    if (reviewOne || reviewPunct) closePopover();

    const rect = evt.currentTarget.getBoundingClientRect();
    const x = rect.left;
    const y = rect.bottom + 6;

    const src = tok.text;
    const choices = [];

    // Always include current
    choices.push({ label: "Current", text: src });

    // Ethiopic full stop -> ASCII period (always safe)
    if (src.includes("።")) {
      choices.push({ label: "Use .", text: src.replaceAll("።", ".") });
    }

    // ASCII period -> Ethiopic full stop (user choice; not automatic)
    if (src.includes(".")) {
      choices.push({ label: "Use ።", text: src.replaceAll(".", "።") });
      choices.push({ label: "Keep .", text: src }); // explicit option
    }

    // If only "Current" exists, no reason to open
    if (choices.length <= 1) return;

    setReviewPunct({ idxToken: tokenIdx, src, choices });
    setPopover({ open: true, x, y });
  }

  const finalAm = useMemo(() => {
    if (mode !== "lat_to_am") return amText;
    if (outTokens) return tokensToText(outTokens);
    return amText;
  }, [mode, outTokens, amText]);

  return (
    <div
      className="app"
      onClick={() => {
        if (popover.open) closePopover();
      }}
    >
      <h2>Amharic Normalizer (AN-v0)</h2>
      <p className="muted">
        Two consistent boxes: Latin and Amharic. Switch direction as needed.
      </p>

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

        {mode === "lat_to_am" && (
          <div className="controls">
            <div className="control">
              <label>
                Habit strength{" "}
                <span className="muted">({habitStrength.toFixed(2)})</span>
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={habitStrength}
                onChange={(e) => setHabitStrength(Number(e.target.value))}
              />
              <div className="hintline">
                0 = strict-ish, 1 = assistive (habit-biased).
              </div>
            </div>
            <TypingHelp />
          </div>
        )}
      </div>

      <div className="grid-2">
        {/* LEFT: Latin box */}
        <div className="panel">
          <h3>{latinLabel}</h3>

          <textarea
            rows={8}
            value={latinText}
            onChange={(e) => latinIsInput && setLatinText(e.target.value)}
            readOnly={!latinIsInput}
            placeholder={
              latinIsInput ? "Type Latin… e.g. tarfiyalesh, migib, hEi" : ""
            }
          />

          {latinIsInput && (
            <div className="button-row">
              <button onClick={runNormalize} disabled={loading || !latinText.trim()}>
                {loading ? "Running…" : "Run"}
              </button>
              <button
                className="secondary"
                onClick={() => setLatinText("tarfiyalesh")}
              >
                Example: sh ambiguity
              </button>
              <button className="secondary" onClick={() => setLatinText("migib")}>
                Example: habit (migib)
              </button>
            </div>
          )}
        </div>

        {/* RIGHT: Amharic box */}
        <div className="panel">
          <h3>{amLabel}</h3>

          {/* Same box becomes interactive in review mode (lat_to_am output only) */}
          {mode === "lat_to_am" && reviewMode ? (
            <div className="review-surface">
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
                    // className="punct"
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
              rows={8}
              value={finalAm}
              onChange={(e) => amIsInput && setAmText(e.target.value)}
              readOnly={!amIsInput}
              placeholder={amIsInput ? "Paste Ethiopic text… e.g. ታርፋለህ" : ""}
            />
          )}

          {/* Buttons under Amharic when it's input OR when it's output (copy/review) */}
          <div className="button-row">
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
                          if (outTokens == null)
                            setOutTokens(tokenizeForReview(finalAm));
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
                          // persist edits into the textarea view
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

          <TypingHelp />

          {/* unified popover: word OR punctuation */}
          {(popover.open && (reviewOne || reviewPunct)) ? (
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
                            i === reviewOne.idxToken
                              ? { ...tok, text: c.text_am }
                              : tok
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

      {/* --- dev details (comment out when you’re ready) ---
      <div className="panel">
        <details>
          <summary>Debug: raw JSON</summary>
          <pre className="mono">{JSON.stringify(result, null, 2)}</pre>
        </details>
      </div>
      --- */}
    </div>
  );
}


// // App.jsx
// import { useMemo, useState } from "react";
// import TypingHelp from "./TypingHelp";
// import "./App.css";

// const API_BASE_RAW =
//   import.meta.env.VITE_API_BASE_URL 
//   // import.meta.env.VITE_API_BASE_URL2;
// const API_BASE = API_BASE_RAW.endsWith("/") ? API_BASE_RAW : API_BASE_RAW + "/";
// const NORMALIZE_URL = API_BASE + "normalize";

// const DEFAULT_LAT = "selam! EnkWan dehna meTu!";
// const DEFAULT_AM = "ሰላም! እንኳን ደህና መጡ!";

// const [punctMode, setPunctMode] = useState("ethiopic"); // "ethiopic" | "ascii" for . and ::

// async function fetchJson(url, options) {
//   const res = await fetch(url, options);
//   if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
//   return res.json();
// }

// async function copyToClipboard(text) {
//   await navigator.clipboard.writeText(text);
// }

// function splitPreserveWhitespace(s) {
//   const out = [];
//   let buf = "";
//   let inWord = null;
//   const isWordChar = (ch) => !/\s/.test(ch);

//   for (const ch of s) {
//     const w = isWordChar(ch);
//     if (inWord === null) {
//       inWord = w;
//       buf = ch;
//       continue;
//     }
//     if (w === inWord) buf += ch;
//     else {
//       out.push({ t: buf, isWord: inWord });
//       buf = ch;
//       inWord = w;
//     }
//   }
//   if (buf) out.push({ t: buf, isWord: inWord });
//   return out;
// }

// function tokenizeForReview(text) {
//   return splitPreserveWhitespace(text).map((p) => ({
//     kind: p.isWord ? "word" : "ws",
//     text: p.t,
//   }));
// }

// function tokensToText(tokens) {
//   return (tokens ?? []).map((t) => t.text).join("");
// }

// function extractWords(text) {
//   return splitPreserveWhitespace(text)
//     .filter((p) => p.isWord)
//     .map((p) => p.t);
// }

// export default function App() {
//   // mode: "lat_to_am" | "am_to_lat"
//   const [mode, setMode] = useState("lat_to_am");

//   // canonical “current inputs”
//   const [latinText, setLatinText] = useState(DEFAULT_LAT);
//   const [amText, setAmText] = useState(DEFAULT_AM);

//   // slider
//   const [habitStrength, setHabitStrength] = useState(0.85);

//   // output state
//   const [result, setResult] = useState(null);

//   // review state (Amharic output only, for lat_to_am)
//   const [reviewMode, setReviewMode] = useState(false);
//   const [outTokens, setOutTokens] = useState(null);

//   // IMPORTANT: store the Latin word list that produced the current output
//   // We use this to fetch alternatives during review, since Ethiopic->Ethiopic is deterministic.
//   const [latinWords, setLatinWords] = useState([]);

//   // Single active review popover
//   const [reviewOne, setReviewOne] = useState(null); // { idxToken, wordOrdinal, srcLatin, srcAm, choices:[{label,text_am}] }
//   const [popover, setPopover] = useState({ open: false, x: 0, y: 0 });

//   const [err, setErr] = useState("");
//   const [loading, setLoading] = useState(false);

//   const latinIsInput = mode === "lat_to_am";
//   const amIsInput = mode === "am_to_lat";

//   const latinLabel = `Latin ${latinIsInput ? "(input)" : "(output)"}`;
//   const amLabel = `Amharic ${amIsInput ? "(input)" : "(output)"}`;

//   function resetReviewState() {
//     setReviewMode(false);
//     setOutTokens(null);
//     setReviewOne(null);
//     setPopover({ open: false, x: 0, y: 0 });
//     // latinWords persists until next RUN in lat_to_am
//   }

//   function closePopover() {
//     setReviewOne(null);
//     setPopover({ open: false, x: 0, y: 0 });
//   }

//   async function runNormalize() {
//     setErr("");
//     setLoading(true);
//     setResult(null);
//     closePopover();
//     resetReviewState();

//     try {
//       const text = latinIsInput ? latinText : amText;

//       const options =
//         mode === "am_to_lat"
//           ? { return_latin_std: true, return_alternatives: false }
//           : {
//               return_alternatives: true,
//               max_alternatives: 5,
//               latin_mode: "auto",
//               habit_strength: habitStrength,
//             };

//       const data = await fetchJson(NORMALIZE_URL, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ text, options }),
//       });

//       setResult(data);

//       if (mode === "lat_to_am") {
//         const bestAm = data.text_am ?? "";
//         setAmText(bestAm);
//         setOutTokens(tokenizeForReview(bestAm));

//         // Store Latin word list for review mapping
//         setLatinWords(extractWords(latinText));
//       } else {
//         setLatinText(data.latin_std ?? "");
//       }
//     } catch (e) {
//       setErr(e?.message ?? String(e));
//     } finally {
//       setLoading(false);
//     }
//   }

//   function tokenIndexToWordOrdinal(tokens, tokenIdx) {
//     // Count how many word tokens occur before tokenIdx
//     let ord = 0;
//     for (let i = 0; i < tokenIdx; i++) {
//       if (tokens[i]?.kind === "word") ord += 1;
//     }
//     return ord;
//   }

//   async function openWordReview(tokenIdx, evt) {
//     if (!reviewMode) return;
//     if (mode !== "lat_to_am") return;
//     if (!outTokens || tokenIdx == null) return;

//     const tok = outTokens[tokenIdx];
//     if (!tok || tok.kind !== "word") return;

//     // allow switching focus by closing current popover
//     if (reviewOne) closePopover();

//     const rect = evt.currentTarget.getBoundingClientRect();
//     const x = rect.left;
//     const y = rect.bottom + 6;

//     const wordOrdinal = tokenIndexToWordOrdinal(outTokens, tokenIdx);
//     const srcLatin = latinWords[wordOrdinal] || "";
//     const srcAm = tok.text;

//     // If we can't map back to a Latin word, we cannot fetch ambiguity alternatives.
//     // (Ethiopic->Ethiopic is deterministic and won't return alternatives.)
//     if (!srcLatin) {
//       setErr(
//         "Review mapping failed (Latin word missing for this output word). Try running again, or ensure input/output tokenization aligns."
//       );
//       return;
//     }

//     try {
//       setLoading(true);

//       // Fetch alternatives using the *Latin source word*, not the Ethiopic output word.
//       const data = await fetchJson(NORMALIZE_URL, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           text: srcLatin,
//           options: {
//             return_alternatives: true,
//             max_alternatives: 10,
//             latin_mode: "auto",
//             habit_strength: habitStrength,
//           },
//         }),
//       });

//       const choices = [];
//       const seen = new Set();

//       const push = (label, text_am) => {
//         if (!text_am) return;
//         if (seen.has(text_am)) return;
//         seen.add(text_am);
//         choices.push({ label, text_am });
//       };

//       push("Best", data.text_am);
//       for (const a of data.alternatives ?? []) push("Alt", a.text_am);

//       // Ensure current shown Amharic is selectable even if it isn't in the candidate set
//       // (can happen if mapping drifted or user already edited tokens).
//       push("Current", srcAm);

//       setReviewOne({
//         idxToken: tokenIdx,
//         wordOrdinal,
//         srcLatin,
//         srcAm,
//         choices,
//       });
//       setPopover({ open: true, x, y });
//     } catch (e) {
//       setErr(e?.message ?? String(e));
//     } finally {
//       setLoading(false);
//     }
//   }

//   const finalAm = useMemo(() => {
//     if (mode !== "lat_to_am") return amText;
//     if (outTokens) return tokensToText(outTokens);
//     return amText;
//   }, [mode, outTokens, amText]);

//   return (
//     <div
//       className="app"
//       onClick={() => {
//         if (popover.open) closePopover();
//       }}
//     >
//       <h2>Amharic Normalizer (AN-v0)</h2>
//       <p className="muted">
//         Two consistent boxes: Latin and Amharic. Switch direction as needed.
//       </p>

//       <div className="panel">
//         <div className="button-row" style={{ marginTop: 0 }}>
//           <button
//             // className={mode === "lat_to_am" ? "" : "secondary"}
//             className={mode === "lat_to_am" ? "active-toggle" : "inactive-toggle"}
//             onClick={() => {
//               setMode("lat_to_am");
//               setErr("");
//               resetReviewState();
//               setResult(null);
//             }}
//           >
//             Latin → Ethiopic
//           </button>
//           <button
//             // className={mode === "am_to_lat" ? "" : "secondary"}
//             className={mode === "am_to_lat" ? "active-toggle" : "inactive-toggle"}
//             onClick={() => {
//               setMode("am_to_lat");
//               setErr("");
//               resetReviewState();
//               setResult(null);
//             }}
//           >
//             Latin ← Ethiopic
//           </button>
//         </div>

//         {mode === "lat_to_am" && (
//           <div className="controls">
//             <div className="control">
//               <label>
//                 Habit strength <span className="muted">({habitStrength.toFixed(2)})</span>
//               </label>
//               <input
//                 type="range"
//                 min="0"
//                 max="1"
//                 step="0.05"
//                 value={habitStrength}
//                 onChange={(e) => setHabitStrength(Number(e.target.value))}
//               />
//               <div className="hintline">
//                 0 = strict-ish, 1 = assistive (habit-biased).
//               </div>
//             </div>
//             <TypingHelp />
 
//           </div>
//         )}
//       </div>

//       <div className="grid-2">
//         {/* LEFT: Latin box */}
//         <div className="panel">
//           <h3>{latinLabel}</h3>

//           <textarea
//             rows={8}
//             value={latinText}
//             onChange={(e) => latinIsInput && setLatinText(e.target.value)}
//             readOnly={!latinIsInput}
//             placeholder={
//               latinIsInput ? "Type Latin… e.g. tarfiyalesh, migib, hEi" : ""
//             }
//           />

//           {latinIsInput && (
//             <div className="button-row">
//               <button onClick={runNormalize} disabled={loading || !latinText.trim()}>
//                 {loading ? "Running…" : "Run"}
//               </button>
//               <button className="secondary" onClick={() => setLatinText("tarfiyalesh")}>
//                 Example: sh ambiguity
//               </button>
//               <button className="secondary" onClick={() => setLatinText("migib")}>
//                 Example: habit (migib)
//               </button>
//             </div>
//           )}
//         </div>

//         {/* RIGHT: Amharic box */}
//         <div className="panel">
//           <h3>{amLabel}</h3>

//           {/* Same box becomes interactive in review mode (lat_to_am output only) */}
//           {mode === "lat_to_am" && reviewMode ? (
//             <div className="review-surface">
//               {(outTokens ?? tokenizeForReview(finalAm)).map((t, idx) =>
//                 t.kind === "ws" ? (
//                   <span key={idx} style={{ whiteSpace: "pre-wrap" }}>
//                     {t.text}
//                   </span>
//                 ) : (
//                   <span
//                     key={idx}
//                     className="word"
//                     title="Click to review this word"
//                     onClick={(e) => {
//                       e.stopPropagation();
//                       openWordReview(idx, e);
//                     }}
//                   >
//                     {t.text}
//                   </span>
//                 )
//               )}
//             </div>
//           ) : (
//             <textarea
//               rows={8}
//               value={finalAm}
//               onChange={(e) => amIsInput && setAmText(e.target.value)}
//               readOnly={!amIsInput}
//               placeholder={amIsInput ? "Paste Ethiopic text… e.g. ታርፋለህ" : ""}
//             />
//           )}

//           {/* Buttons under Amharic when it's input OR when it's output (copy/review) */}
//           <div className="button-row">
//             {amIsInput ? (
//               <button onClick={runNormalize} disabled={loading || !amText.trim()}>
//                 {loading ? "Running…" : "Run"}
//               </button>
//             ) : (
//               <>
//                 <button
//                   className="secondary"
//                   onClick={async (e) => {
//                     e.stopPropagation();
//                     await copyToClipboard(finalAm);
//                   }}
//                   disabled={!finalAm.trim()}
//                 >
//                   Copy
//                 </button>

//                 {mode === "lat_to_am" && (
//                   <>
//                     {!reviewMode ? (
//                       <button
//                         className="secondary"
//                         onClick={(e) => {
//                           e.stopPropagation();
//                           if (outTokens == null) setOutTokens(tokenizeForReview(finalAm));
//                           setReviewMode(true);
//                         }}
//                         disabled={!finalAm.trim()}
//                       >
//                         Enter review
//                       </button>
//                     ) : (
//                       <button
//                         className="secondary"
//                         onClick={(e) => {
//                           e.stopPropagation();
//                           closePopover();
//                           setReviewMode(false);
//                           // persist edits into the textarea view
//                           setAmText(finalAm);
//                         }}
//                       >
//                         Exit review
//                       </button>
//                     )}
//                   </>
//                 )}
//               </>
//             )}
//           </div>
//           <TypingHelp />
//           {/* single-word popover */}
//           {reviewOne && popover.open ? (
//             <div
//               className="popover"
//               style={{ left: popover.x, top: popover.y }}
//               onClick={(e) => e.stopPropagation()}
//             >
//               <div className="mono soft" style={{ marginBottom: 6 }}>
//                 {reviewOne.srcLatin} → {reviewOne.srcAm}
//               </div>

//               {reviewOne.choices.map((c, k) => (
//                 <button
//                   key={k}
//                   className="popover-item"
//                   onClick={() => {
//                     setOutTokens((prev) => {
//                       const base = prev ?? tokenizeForReview(finalAm);
//                       return base.map((tok, i) =>
//                         i === reviewOne.idxToken ? { ...tok, text: c.text_am } : tok
//                       );
//                     });
//                     closePopover();
//                   }}
//                 >
//                   {c.label === "Best" ? "Best: " : c.label === "Current" ? "Current: " : "Alt: "}
//                   {c.text_am}
//                 </button>
//               ))}

//               <div className="button-row" style={{ marginTop: 8 }}>
//                 <button className="secondary" onClick={closePopover}>
//                   Cancel
//                 </button>
//               </div>

//               <div className="hintline" style={{ marginTop: 6 }}>
//                 Alternatives come from the original Latin word (not Ethiopic normalization).
//               </div>
//             </div>
//           ) : null}
//         </div>
//       </div>

//       {err && (
//         <div className="panel">
//           <pre className="error">{err}</pre>
//         </div>
//       )}

//       {/* --- dev details (comment out when you’re ready) ---
//       <div className="panel">
//         <details>
//           <summary>Debug: raw JSON</summary>
//           <pre className="mono">{JSON.stringify(result, null, 2)}</pre>
//         </details>
//       </div>
//       --- */}
//     </div>
//   );
// }
