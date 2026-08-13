type CalendarExportEntry = {
  dueDate: string;
  id: string;
  kind: string;
  title: string;
  meta?: string;
};

function escapeIcs(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/,/g, "\\,").replace(/;/g, "\\;");
}

function utcStamp(value: Date): string {
  return value.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

export function downloadPlannerCalendar(entries: CalendarExportEntry[]): void {
  const now = utcStamp(new Date());
  const events = entries.flatMap((entry) => {
    const due = new Date(entry.dueDate);
    if (Number.isNaN(due.getTime())) return [];
    const uid = `${entry.kind}-${entry.id}@enterprise-crm.local`;
    return [
      "BEGIN:VEVENT",
      `UID:${escapeIcs(uid)}`,
      `DTSTAMP:${now}`,
      `DTSTART:${utcStamp(due)}`,
      `SUMMARY:${escapeIcs(entry.title)}`,
      `DESCRIPTION:${escapeIcs(entry.meta ? `${entry.kind} · ${entry.meta}` : entry.kind)}`,
      "END:VEVENT",
    ].join("\r\n");
  });
  const content = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Enterprise CRM//V3 Planner//EN", "CALSCALE:GREGORIAN", ...events, "END:VCALENDAR", ""].join("\r\n");
  const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = "enterprise-crm-planner.ics";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(href);
}
