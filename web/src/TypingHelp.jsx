import { useState } from "react";

export default function TypingHelp() {
  const [open, setOpen] = useState(false);

  return (
    <div className="typing-help">
      <button
        className="typing-help-toggle"
        onClick={() => setOpen(!open)}
      >
        {open ? "Hide ×" : "Show standard typing rules"}
      </button>

      {open && (
        <div className="typing-help-content">
          <h3>Latin-Std Typing Guide (v0)</h3>

          <p className="muted">
            Lowercase is standard. Uppercase has semantic meaning.
          </p>

          {/* ---------------- VOWEL CARRIERS ---------------- */}
          <section>
            <h4>Standalone vowel carriers (uppercase)</h4>
            <table>
              <thead>
                <tr>
                  <th>Latin</th>
                  <th>Ethiopic</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>A</td><td>አ</td></tr>
                <tr><td>U</td><td>ኡ</td></tr>
                <tr><td>I</td><td>ኢ</td></tr>
                <tr><td>AA</td><td>ኣ</td></tr>
                <tr><td>EE</td><td>ኤ</td></tr>
                <tr><td>E</td><td>እ</td></tr>
                <tr><td>O</td><td>ኦ</td></tr>
              </tbody>
            </table>
          </section>

          {/* ---------------- VOWELS AFTER CONSONANTS ---------------- */}
          <section>
            <h4>Vowels after consonants</h4>
            <table>
              <thead>
                <tr>
                  <th>Latin</th>
                  <th>Meaning</th>
                  <th>Example</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>e</td><td>order 1</td><td>le → ለ</td></tr>
                <tr><td>u</td><td>order 2</td><td>lu → ሉ</td></tr>
                <tr><td>i</td><td>order 3</td><td>li → ሊ</td></tr>
                <tr><td>a</td><td>order 4</td><td>la → ላ</td></tr>
                <tr><td>Ei</td><td>order 5 (locked)</td><td>lEi → ሌ</td></tr>
                <tr><td>(none)</td><td>order 6</td><td>l → ል</td></tr>
                <tr><td>o</td><td>order 7</td><td>lo → ሎ</td></tr>
              </tbody>
            </table>
          </section>

          {/* ---------------- EXPLICIT BASES ---------------- */}
          <section>
            <h4>Explicit consonant bases (uppercase)</h4>
            <table>
              <thead>
                <tr>
                  <th>Latin</th>
                  <th>Ethiopic</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>S</td><td>ሸ</td></tr>
                <tr><td>K</td><td>ኸ</td></tr>
                <tr><td>N</td><td>ኘ</td></tr>
                <tr><td>Z</td><td>ዠ</td></tr>
                <tr><td>X</td><td>ጸ</td></tr>
                <tr><td>P</td><td>ጰ</td></tr>
                <tr><td>T</td><td>ጠ</td></tr>
                <tr><td>C</td><td>ጨ</td></tr>
                <tr><td>c</td><td>ቸ</td></tr>
              </tbody>
            </table>
          </section>

          {/* ---------------- SLIDER EXPLANATION ---------------- */}
          <section className="slider-help">
            <h4>Ambiguity preference (slider)</h4>

            <p className="muted">
              The slider controls how strongly the system prefers the
              <b> standard rule</b> versus <b>common typing habits</b>.
              <br />
              The standard interpretation is never changed — habits only affect
              alternative suggestions and their priority.
            </p>

            <table className="example-table">
              <thead>
                <tr>
                  <th>Input</th>
                  <th>Standard (rule)</th>
                  <th>Customary (habit)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="mono">tewash</td>
                  <td>ተዋስህ</td>
                  <td>ተዋሽ</td>
                </tr>
                <tr>
                  <td className="mono">mgib</td>
                  <td>ምጊብ</td>
                  <td>ምግብ</td>
                </tr>
              </tbody>
            </table>

            <p className="soft">
              • Move the slider toward <b>Standard</b> to prioritize strict Latin-Std rules.<br />
              • Move it toward <b>Habit</b> to surface common user interpretations more prominently.
            </p>
          </section>

          <p className="soft">
            Tip: Convert ALL-CAPS text to lowercase before typing for best results.
          </p>
        </div>
      )}
    </div>
  );
}
