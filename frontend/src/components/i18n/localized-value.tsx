"use client";

import { useI18n } from "@/components/i18n/i18n-provider";

export function LocalizedDateTime({ value }: { value: string | null }) {
  const { formatDateTime } = useI18n();
  return <>{formatDateTime(value)}</>;
}

export function LocalizedDate({ value }: { value: string | null }) {
  const { formatDate } = useI18n();
  return <>{formatDate(value)}</>;
}

export function LocalizedMoney({ value, currency }: { value: number | string; currency: string }) {
  const { formatMoney } = useI18n();
  return <>{formatMoney(value, currency)}</>;
}

export function LocalizedNumber({ value }: { value: number | string }) {
  const { formatNumber } = useI18n();
  return <>{formatNumber(value)}</>;
}

export function LocalizedPercent({ value }: { value: number | string }) {
  const { formatNumber, locale } = useI18n();
  return <>{formatNumber(value)}{locale === "fa" ? "٪" : "%"}</>;
}

export function LocalizedEnum({ value }: { value: string }) {
  const { enumLabel } = useI18n();
  return <>{enumLabel(value)}</>;
}
