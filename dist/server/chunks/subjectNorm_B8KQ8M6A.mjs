function cleanSubjectName(name) {
  return name.replace(/\s*(п\/г|гр\.|подгруппа)\s*\d+/gi, "").replace(/\s+\d+$/g, "").replace(/[,;.]+$/, "").trim();
}
function normalizeForCompare(name) {
  return cleanSubjectName(name).normalize("NFD").toLowerCase().replace(/\s+/g, " ").trim();
}
function levenshtein(a, b) {
  const m = a.length;
  const n = b.length;
  const dp = Array.from(
    { length: m + 1 },
    (_, i) => Array.from({ length: n + 1 }, (_2, j) => i === 0 ? j : j === 0 ? i : 0)
  );
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
  }
  return dp[m][n];
}
function fuzzyMatch(a, b, threshold) {
  const na = normalizeForCompare(a);
  const nb = normalizeForCompare(b);
  if (na === nb) return true;
  const maxLen = Math.max(na.length, nb.length);
  if (maxLen === 0) return true;
  const effectiveThreshold = Math.floor(maxLen * 0.15);
  return levenshtein(na, nb) <= effectiveThreshold;
}

export { cleanSubjectName as c, fuzzyMatch as f, normalizeForCompare as n };
