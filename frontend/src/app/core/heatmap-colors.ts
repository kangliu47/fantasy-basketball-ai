/** Shared diverging heatmap palette: red is lower, green is higher. */
export const HEATMAP_COLORS = [
  '#b84e46',
  '#cf7045',
  '#e7a38d',
  '#f1d6cf',
  '#f5f7f2',
  '#d7e8da',
  '#a7c9ae',
  '#6e9f7b',
  '#397050',
] as const;

export function heatmapColor(normalized: number): string {
  const index = Math.round(Math.max(0, Math.min(1, normalized)) * (HEATMAP_COLORS.length - 1));
  return HEATMAP_COLORS[index];
}

export function heatmapIsDark(normalized: number): boolean {
  return normalized < 0.25 || normalized > 0.75;
}
