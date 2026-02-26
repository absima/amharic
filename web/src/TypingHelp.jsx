// TypingHelp.jsx
import { useEffect, useMemo, useRef, useState } from "react";

export default function TypingHelp() {
  const [open, setOpen] = useState(false);
  const scrollRef = useRef(null);

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
      { lat: "hxx", am: "ሐ" },
      { lat: "hxxx", am: "ኀ" },
      { lat: "sx", am: "ሠ" },
      { lat: "ax", am: "ዐ" },
    ],
    []
  );

  return (
    <>
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
              height: "85vh",          // ✅ stable modal height
              borderRadius: 14,
              background: "#fff",
              boxShadow: "0 12px 30px rgba(0,0,0,0.25)",
              overflow: "hidden",      // ✅ header/footer stay fixed, body scrolls
              display: "flex",
              flexDirection: "column",
            }}
            className="typing-help-content"
          >
=            <div
              style={{
                position: "sticky",
                top: 0,
                zIndex: 2,
                background: "#fff",
                padding: 16,
                borderBottom: "1px solid rgba(0,0,0,0.08)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: 12,
                  flexWrap: "wrap",
                }}
              >
                <div style={{ minWidth: 0, flex: "1 1 320px" }}>
                  <h3
                    style={{
                      margin: 0,
                      fontSize: "clamp(16px, 2.6vw, 22px)",
                      lineHeight: 1.2,
                      wordBreak: "break-word",
                    }}
                  >
                    Latin-Std Typing Guide (v0)
                  </h3>

                  <p className="muted" style={{ marginTop: 6, marginBottom: 0 }}>
                    Lowercase is standard. Uppercase has no special meaning in the new standard.
                    Underscore (<span className="mono">_</span>) introduces independent አ-family vowels.
                  </p>
                </div>

                <div style={{ display: "flex", gap: 8, flex: "0 0 auto" }}>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => {
                      // jump to top of guide content
                      scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    style={{ whiteSpace: "nowrap" }}
                    title="Back to top of guide"
                  >
                    Top ↑
                  </button>

                  <button
                    type="button"
                    className="secondary"
                    onClick={() => setOpen(false)}
                    style={{ whiteSpace: "nowrap" }}
                    title="Close"
                  >
                    Close ×
                  </button>
                </div>
              </div>
            </div>

            <div
              ref={scrollRef}
              style={{
                padding: 16,
                overflow: "auto",
                WebkitOverflowScrolling: "touch",
              }}
            >
              <section style={{ marginTop: 4 }}>
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
                  carriers (e.g., <span className="mono">enkwan</span> starts with{" "}
                  <span className="mono">e</span> → <span className="mono">እ</span>).
                </p>
              </section>

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

              <section style={{ marginTop: 14 }}>
                <h4>Special / variant consonant bases</h4>
                <p className="muted" style={{ marginTop: 6 }}>
                  Bases that don’t have a clean Latin spelling (or variant families) use{" "}
                  <span className="mono">x</span> / <span className="mono">xx</span>.
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
                  Example: <span className="mono">txa</span> → <span className="mono">ጣ</span>,{" "}
                  <span className="mono">cxxo</span> → <span className="mono">ፆ</span>.
                </p>
              </section>

              <section style={{ marginTop: 14 }}>
                <h4>Ambiguity / alternatives</h4>
                <p className="muted" style={{ marginTop: 6 }}>
                  When multiple interpretations exist, the system may surface alternatives.
                  Review mode lets you switch outputs word by word.
                </p>
                <p className="soft" style={{ marginTop: 6 }}>
                  Tip: Use <span className="mono">_</span> to remove ambiguity explicitly
                  (e.g., <span className="mono">l_u</span>).
                </p>
              </section>

              <div style={{ height: 18 }} />
            </div>

            <div
              style={{
                position: "sticky",
                bottom: 0,
                zIndex: 2,
                background: "#fff",
                padding: 12,
                borderTop: "1px solid rgba(0,0,0,0.08)",
                display: "flex",
                justifyContent: "space-between",
                gap: 8,
              }}
            >
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  scrollRef.current?.scrollTo({
                    top: scrollRef.current?.scrollHeight ?? 0,
                    behavior: "smooth",
                  });
                }}
                title="Jump to end"
              >
                End ↓
              </button>

              <button
                type="button"
                className="secondary"
                onClick={() => setOpen(false)}
                style={{ whiteSpace: "nowrap" }}
              >
                Close ×
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

