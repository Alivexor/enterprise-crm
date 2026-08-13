export function formatMoney(value: number | string, currency: string): string {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return "—";
  try {
    return new Intl.NumberFormat(undefined, { currency, style: "currency" }).format(numericValue);
  } catch {
    return `${numericValue.toLocaleString()} ${currency}`;
  }
}
