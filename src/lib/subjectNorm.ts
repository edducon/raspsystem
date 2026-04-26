const GROUP_SUFFIX_WORD_RE = '(?:\\u043f\\u043e\\u0434\\u0433\\u0440\\u0443\\u043f\\u043f\\u0430|\\u0433\\u0440\\u0443\\u043f\\u043f\\u0430|\\u0433\\u0440\\u0443\\u043f\\u043f\\u044b|\\u0433\\u0440\\u0443\\u043f\\.?|\\u043f\\s*\\/?\\s*\\u0433|\\u043f\\s*\\.?\\s*\\u0433\\.?|\\u0433\\u0440\\.?|\\u0433\\b)';
const GROUP_SUFFIX_BEFORE_NUMBER_RE = new RegExp(`\\s*\\(?\\s*${GROUP_SUFFIX_WORD_RE}\\s*\\d+\\s*\\)?`, 'gi');
const GROUP_SUFFIX_AFTER_NUMBER_RE = new RegExp(`\\s*\\(?\\s*\\d+\\s*(?:-?\\s*\\u044f\\s*)?${GROUP_SUFFIX_WORD_RE}\\s*\\)?`, 'gi');

export function cleanSubjectName(name: string): string {
  return name
    .replace(GROUP_SUFFIX_AFTER_NUMBER_RE, '')
    .replace(GROUP_SUFFIX_BEFORE_NUMBER_RE, '')
    .replace(/\s+\d+$/g, '')
    .replace(/[,;.]+$/, '')
    .replace(/\s+/g, ' ')
    .trim();
}

export function normalizeForCompare(name: string): string {
  return cleanSubjectName(name)
    .normalize('NFD')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

export function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
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

export function fuzzyMatch(a: string, b: string, threshold?: number): boolean {
  const na = normalizeForCompare(a);
  const nb = normalizeForCompare(b);
  if (na === nb) return true;
  const maxLen = Math.max(na.length, nb.length);
  if (maxLen === 0) return true;
  const effectiveThreshold = threshold ?? Math.floor(maxLen * 0.15);
  return levenshtein(na, nb) <= effectiveThreshold;
}
