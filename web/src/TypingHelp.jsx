// TypingHelp.jsx
import { useEffect, useMemo, useState } from "react";

export default function TypingHelp() {
  const [open, setOpen] = useState(false);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const carriers = useMemo(
    () => [
      { lat: "_a", am: "አ" },
      { lat: "_u", am: "ኡ" },
      { lat: "_i", am: "ኢ" },
      { lat: "_aa", am: "ኣ" },
      { lat: "_ei", am: "ኤ" },
      { lat: "_", am: "እ" },
      { lat: "_o", am: "ኦ" },
    ],
    []
  );

  const attachedVowels = useMemo(
    () => [
      { lat: "e", meaning: "order 1", ex: "le → ለ" },
      { lat: "u", meaning: "order 2", ex: "lu → ሉ" },
      { lat: "i", meaning: "order 3", ex: "li → ሊ" },
      { lat: "a", meaning: "order 4", ex: "la → ላ" },
      { lat: "ei", meaning: "order 5", ex: "lei → ሌ" },
      { lat: "(none)", meaning: "order 6", ex: "l → ል" },
      { lat: "o", meaning: "order 7", ex: "lo → ሎ" },
      { lat: "oa", meaning: "order 8 (labialized)", ex: "loa → ሏ" },
    ],
    []
  );

  const specialBases = useMemo(
    () => [
      { lat: "kx", am: "ኸ" },
      { lat: "nx", am: "ኘ" },
      { lat: "zx", am: "ዠ" },
      { lat: "cx", am: "ጸ" },
      { lat: "cxx", am: "ፀ" },
      { lat: "px", am: "ጰ" },
      { lat: "tx", am: "ጠ" },
      { lat: "ch", am: "ቸ" },
      { lat: "chx", am: "ጨ" },
      { lat: "shx", am: "ሽ" },
      { lat: "hx", am: "ሐ" },
      { lat: "hxx", am: "ኀ" },
      { lat: "sx", am: "ሠ" },
      { lat: "ax", am: "ዐ" },
    ],
    []
  );

  return (
    <>
      {/* Floating toggle button (always reachable) */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open Latin-Std typing guide"
        title="Typing guide"
        style={{
          position: "fixed",
          right: 16,
          bottom: 16,
          zIndex: 1000,
          borderRadius: 999,
          padding: "10px 14px",
          fontWeight: 600,
        }}
        className="typing-help-fab"
      >
        ? Typing guide
      </button>

      {/* Modal */}
      {open && (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => setOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.35)",
            zIndex: 1001,
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "center",
            padding: 12,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "min(960px, 100%)",
              maxHeight: "85vh",
              overflow: "auto",
              borderRadius: 14,
              background: "#fff",
              padding: 16,
              boxShadow: "0 12px 30px rgba(0,0,0,0.25)",
            }}
            className="typing-help-content"
          >
            {/* <div
              style={{
                display: "flex",
                alignItems: "start",
                justifyContent: "space-between",
                gap: 12,
                marginBottom: 10,
              }}
            >
              <div>
                <h3 style={{ margin: 0 }}>Latin-Std Typing Guide (v0)</h3>
                <p className="muted" style={{ marginTop: 6 }}>
                  Lowercase is standard. Uppercase has no special meaning in the
                  new standard. Underscore (<span className="mono">_</span>)
                  introduces independent አ-family vowels.
                </p>
              </div>

              <button
                type="button"
                className="secondary"
                onClick={() => setOpen(false)}
                style={{ whiteSpace: "nowrap" }}
              >
                Close ×
              </button>
            </div> */}
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: 12,
                marginBottom: 10,
                flexWrap: "wrap",        // ✅ allow wrap on mobile
              }}
            >
              <div style={{ minWidth: 0, flex: "1 1 320px" }}> {/* ✅ allow title to wrap nicely */}
                <h3
                  style={{
                    margin: 0,
                    fontSize: "clamp(16px, 2.6vw, 22px)",       // ✅ responsive
                    lineHeight: 1.2,
                    wordBreak: "break-word",
                  }}
                >
                  Latin-Std Typing Guide (v0)
                </h3>

                <p className="muted" style={{ marginTop: 6 }}>
                  Lowercase is standard. Uppercase has no special meaning in the new standard.
                  Underscore (<span className="mono">_</span>) introduces independent አ-family vowels.
                </p>
              </div>

              <button
                type="button"
                className="secondary"
                onClick={() => setOpen(false)}
                style={{
                  whiteSpace: "nowrap",
                  flex: "0 0 auto",
                  alignSelf: "flex-start",
                }}
              >
                Close ×
              </button>
            </div>

            {/* QUICK RULES */}
            <section style={{ marginTop: 10 }}>
              <h4>Quick rules</h4>
              <ul className="soft" style={{ marginTop: 6 }}>
                <li>
                  <b>Vowels normally attach</b> to the previous consonant:
                  <span className="mono"> le lu li la lei l lo </span> →{" "}
                  <span className="mono">ለ ሉ ሊ ላ ሌ ል ሎ</span>
                </li>
                <li>
                  <b>Independent vowels</b> use underscore carriers:
                  <span className="mono"> _a _u _i _aa _ei _ _o </span> →{" "}
                  <span className="mono">አ ኡ ኢ ኣ ኤ እ ኦ</span>
                </li>
                <li>
                  <b>Override after consonant</b> (force አ-family vowel) with{" "}
                  <span className="mono">C_V</span>:{" "}
                  <span className="mono">l_u</span> →{" "}
                  <span className="mono">ልኡ</span>
                </li>
                <li>
                  <b>Word-initial vowels</b> are treated like underscore carriers
                  (convenience): <span className="mono">enkwan</span> begins with{" "}
                  <span className="mono">e</span> →{" "}
                  <span className="mono">እ</span>.
                </li>
                <li>
                  <b>Order-8</b> uses <span className="mono">oa</span>:{" "}
                  <span className="mono">loa</span> →{" "}
                  <span className="mono">ሏ</span>
                </li>
              </ul>
            </section>

            {/* VOWEL CARRIERS */}
            <section style={{ marginTop: 14 }}>
              <h4>Independent vowel carriers (underscore)</h4>
              <table>
                <thead>
                  <tr>
                    <th>Latin</th>
                    <th>Ethiopic</th>
                  </tr>
                </thead>
                <tbody>
                  {carriers.map((r) => (
                    <tr key={r.lat}>
                      <td className="mono">{r.lat}</td>
                      <td>{r.am}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="soft" style={{ marginTop: 8 }}>
                Note: At the start of a word, leading vowels behave like these
                carriers (e.g., <span className="mono">enkwan</span> starts with
                <span className="mono"> e</span> → <span className="mono">እ</span>).
              </p>
            </section>

            {/* VOWELS AFTER CONSONANTS */}
            <section style={{ marginTop: 14 }}>
              <h4>Vowels after consonants (orders)</h4>
              <table>
                <thead>
                  <tr>
                    <th>Latin</th>
                    <th>Meaning</th>
                    <th>Example</th>
                  </tr>
                </thead>
                <tbody>
                  {attachedVowels.map((r) => (
                    <tr key={r.lat}>
                      <td className="mono">{r.lat}</td>
                      <td>{r.meaning}</td>
                      <td className="mono">{r.ex}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            {/* SPECIAL BASES */}
            <section style={{ marginTop: 14 }}>
              <h4>Special / variant consonant bases</h4>
              <p className="muted" style={{ marginTop: 6 }}>
                Bases that don’t have a clean Latin spelling (or variant
                families) use <span className="mono">x</span> /{" "}
                <span className="mono">xx</span>.
              </p>

              <table>
                <thead>
                  <tr>
                    <th>Latin base</th>
                    <th>Ethiopic base</th>
                  </tr>
                </thead>
                <tbody>
                  {specialBases.map((r) => (
                    <tr key={r.lat}>
                      <td className="mono">{r.lat}</td>
                      <td>{r.am}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <p className="soft" style={{ marginTop: 8 }}>
                Example: <span className="mono">txa</span> →{" "}
                <span className="mono">ጣ</span>,{" "}
                <span className="mono">cxxo</span> →{" "}
                <span className="mono">ፆ</span>.
              </p>
            </section>

            {/* SLIDER NOTE (if you still want it) */}
            <section style={{ marginTop: 14 }}>
              <h4>Ambiguity / alternatives</h4>
              <p className="muted" style={{ marginTop: 6 }}>
                When multiple interpretations exist, the system may surface
                alternatives. (Your UI review mode lets you switch outputs word by
                word.)
              </p>
              <p className="soft" style={{ marginTop: 6 }}>
                Tip: Use <span className="mono">_</span> to remove ambiguity
                explicitly (e.g., <span className="mono">l_u</span>).
              </p>
            </section>
          </div>
        </div>
      )}
    </>
  );
}

// import { useState } from "react";

// export default function TypingHelp() {
//   const [open, setOpen] = useState(false);

//   return (
//     <div className="typing-help">
//       <button
//         className="typing-help-toggle"
//         onClick={() => setOpen(!open)}
//       >
//         {open ? "Hide ×" : "Show standard typing rules"}
//       </button>

//       {open && (
//         <div className="typing-help-content">
//           <h3>Latin-Std Typing Guide (v0)</h3>

//           <p className="muted">
//             Lowercase is standard. Uppercase has semantic meaning.
//           </p>

//           {/* ---------------- VOWEL CARRIERS ---------------- */}
//           <section>
//             <h4>Standalone vowel carriers (uppercase)</h4>
//             <table>
//               <thead>
//                 <tr>
//                   <th>Latin</th>
//                   <th>Ethiopic</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 <tr><td>A</td><td>አ</td></tr>
//                 <tr><td>U</td><td>ኡ</td></tr>
//                 <tr><td>I</td><td>ኢ</td></tr>
//                 <tr><td>AA</td><td>ኣ</td></tr>
//                 <tr><td>EE</td><td>ኤ</td></tr>
//                 <tr><td>E</td><td>እ</td></tr>
//                 <tr><td>O</td><td>ኦ</td></tr>
//               </tbody>
//             </table>
//           </section>

//           {/* ---------------- VOWELS AFTER CONSONANTS ---------------- */}
//           <section>
//             <h4>Vowels after consonants</h4>
//             <table>
//               <thead>
//                 <tr>
//                   <th>Latin</th>
//                   <th>Meaning</th>
//                   <th>Example</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 <tr><td>e</td><td>order 1</td><td>le → ለ</td></tr>
//                 <tr><td>u</td><td>order 2</td><td>lu → ሉ</td></tr>
//                 <tr><td>i</td><td>order 3</td><td>li → ሊ</td></tr>
//                 <tr><td>a</td><td>order 4</td><td>la → ላ</td></tr>
//                 <tr><td>Ei</td><td>order 5 (locked)</td><td>lEi → ሌ</td></tr>
//                 <tr><td>(none)</td><td>order 6</td><td>l → ል</td></tr>
//                 <tr><td>o</td><td>order 7</td><td>lo → ሎ</td></tr>
//               </tbody>
//             </table>
//           </section>

//           {/* ---------------- EXPLICIT BASES ---------------- */}
//           <section>
//             <h4>Explicit consonant bases (uppercase)</h4>
//             <table>
//               <thead>
//                 <tr>
//                   <th>Latin</th>
//                   <th>Ethiopic</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 <tr><td>S</td><td>ሸ</td></tr>
//                 <tr><td>K</td><td>ኸ</td></tr>
//                 <tr><td>N</td><td>ኘ</td></tr>
//                 <tr><td>Z</td><td>ዠ</td></tr>
//                 <tr><td>X</td><td>ጸ</td></tr>
//                 <tr><td>P</td><td>ጰ</td></tr>
//                 <tr><td>T</td><td>ጠ</td></tr>
//                 <tr><td>C</td><td>ጨ</td></tr>
//                 <tr><td>c</td><td>ቸ</td></tr>
//               </tbody>
//             </table>
//           </section>

//           {/* ---------------- SLIDER EXPLANATION ---------------- */}
//           <section className="slider-help">
//             <h4>Ambiguity preference (slider)</h4>

//             <p className="muted">
//               The slider controls how strongly the system prefers the
//               <b> standard rule</b> versus <b>common typing habits</b>.
//               <br />
//               The standard interpretation is never changed — habits only affect
//               alternative suggestions and their priority.
//             </p>

//             <table className="example-table">
//               <thead>
//                 <tr>
//                   <th>Input</th>
//                   <th>Standard (rule)</th>
//                   <th>Customary (habit)</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 <tr>
//                   <td className="mono">tewash</td>
//                   <td>ተዋስህ</td>
//                   <td>ተዋሽ</td>
//                 </tr>
//                 <tr>
//                   <td className="mono">mgib</td>
//                   <td>ምጊብ</td>
//                   <td>ምግብ</td>
//                 </tr>
//               </tbody>
//             </table>

//             <p className="soft">
//               • Move the slider toward <b>Standard</b> to prioritize strict Latin-Std rules.<br />
//               • Move it toward <b>Habit</b> to surface common user interpretations more prominently.
//             </p>
//           </section>

//           <p className="soft">
//             Tip: Convert ALL-CAPS text to lowercase before typing for best results.
//           </p>
//         </div>
//       )}
//     </div>
//   );
// }
