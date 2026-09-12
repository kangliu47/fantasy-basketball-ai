/** Shared display order for the league's eight rotisserie categories. */
export const CATEGORY_ORDER = ['PTS', 'REB', 'AST', '3PM', 'STL', 'BLK', 'FG%', 'FT%'] as const;

const CATEGORY_RANK = new Map<string, number>(CATEGORY_ORDER.map((code, index) => [code, index]));

export function sortCategoryCodes(codes: Iterable<string>): string[] {
  return [...new Set(codes)].sort(
    (left, right) =>
      (CATEGORY_RANK.get(left) ?? CATEGORY_ORDER.length) -
      (CATEGORY_RANK.get(right) ?? CATEGORY_ORDER.length) || left.localeCompare(right),
  );
}

export function sortCategoryObjects<T extends { category: string }>(items: readonly T[]): T[] {
  return [...items].sort(
    (left, right) =>
      (CATEGORY_RANK.get(left.category) ?? CATEGORY_ORDER.length) -
      (CATEGORY_RANK.get(right.category) ?? CATEGORY_ORDER.length) ||
      left.category.localeCompare(right.category),
  );
}

export function sortCategoryRules<T extends { code: string }>(items: readonly T[]): T[] {
  return [...items].sort(
    (left, right) =>
      (CATEGORY_RANK.get(left.code) ?? CATEGORY_ORDER.length) -
      (CATEGORY_RANK.get(right.code) ?? CATEGORY_ORDER.length) ||
      left.code.localeCompare(right.code),
  );
}
