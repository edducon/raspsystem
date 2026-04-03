const GROUP_HEAD_LENGTH = 3;
const GROUP_MAX_TAIL_LENGTH = 4;
const GROUP_MAX_NORMALIZED_LENGTH = GROUP_HEAD_LENGTH + GROUP_MAX_TAIL_LENGTH;

export function normalizeGroupValue(value: string): string {
  return value
    .toUpperCase()
    .replace(/[^0-9A-ZА-ЯЁ]/gi, '')
    .slice(0, GROUP_MAX_NORMALIZED_LENGTH);
}

export function formatGroupValue(value: string): string {
  const normalized = normalizeGroupValue(value);
  if (normalized.length <= GROUP_HEAD_LENGTH) return normalized;
  return `${normalized.slice(0, GROUP_HEAD_LENGTH)}-${normalized.slice(GROUP_HEAD_LENGTH)}`;
}

export function getGroupSearchValue(value: string): string {
  return normalizeGroupValue(value).toLowerCase();
}

export function matchesGroupQuery(groupNumber: string, query: string): boolean {
  const normalizedQuery = getGroupSearchValue(query);
  if (!normalizedQuery) return true;
  return getGroupSearchValue(groupNumber).includes(normalizedQuery);
}

export function getNormalizedCursorIndex(value: string, cursorIndex: number | null): number {
  const safeIndex = cursorIndex ?? value.length;
  return normalizeGroupValue(value.slice(0, safeIndex)).length;
}

export function getFormattedCursorIndex(formattedValue: string, normalizedCursorIndex: number): number {
  if (normalizedCursorIndex <= GROUP_HEAD_LENGTH) {
    return Math.min(normalizedCursorIndex, formattedValue.length);
  }
  return Math.min(normalizedCursorIndex + 1, formattedValue.length);
}
