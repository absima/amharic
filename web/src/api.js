export async function fetchLexicon() {
  const r = await fetch("http://127.0.0.1:8000/ui-lexicon?v=1");
  if (!r.ok) throw new Error("Failed to fetch lexicon");
  return r.json();
}

export async function resolveUi(text, latinMode = "auto") {
  const r = await fetch("http://127.0.0.1:8000/resolve-ui", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, latin_mode: latinMode }),
  });
  if (!r.ok) throw new Error("Failed to resolve UI");
  return r.json();
}
