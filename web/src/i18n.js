export function buildDict(lex) {
  const dict = {};
  for (const item of lex.items || []) dict[item.key] = item.am;
  return dict;
}

export function t(dict, key) {
  return (dict && dict[key]) || key; // fail loud
}
