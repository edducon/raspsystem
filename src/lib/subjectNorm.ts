/**
 * Нормализация названий предметов для сравнения и fuzzy-поиска.
 */

/**
 * Очищает название предмета от суффиксов подгрупп, лишних символов и т.п.
 */
export function cleanSubjectName(name: string): string {
  return name
    .replace(/\s*(п\/г|гр\.|подгруппа)\s*\d+/gi, '')
    .replace(/\s+\d+$/g, '')
    .replace(/[,;.]+$/, '')
    .trim();
}

/**
 * Нормализует строку для сравнения: NFD, нижний регистр, схлопывает пробелы.
 */
export function normalizeForCompare(name: string): string {
  return cleanSubjectName(name)
    .normalize('NFD')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Расстояние Левенштейна между двумя строками.
 */
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

/**
 * Нечёткое сравнение двух названий предметов.
 * Порог по умолчанию — 15% от длины более длинной строки.
 */
export function fuzzyMatch(a: string, b: string, threshold?: number): boolean {
  const na = normalizeForCompare(a);
  const nb = normalizeForCompare(b);
  if (na === nb) return true;
  const maxLen = Math.max(na.length, nb.length);
  if (maxLen === 0) return true;
  const effectiveThreshold = threshold ?? Math.floor(maxLen * 0.15);
  return levenshtein(na, nb) <= effectiveThreshold;
}
