import type { ReactNode, SVGProps } from "react";

export type NavigationIconName =
  | "activity"
  | "building"
  | "dashboard"
  | "database"
  | "deal"
  | "inbox"
  | "lead"
  | "note"
  | "planner"
  | "people"
  | "pipeline"
  | "search"
  | "settings"
  | "tag"
  | "task";

type NavigationIconProps = SVGProps<SVGSVGElement> & {
  name: NavigationIconName;
};

const paths: Record<NavigationIconName, ReactNode> = {
  activity: <path d="M4 12h3l2.2-5 4.2 10 2-5H20" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />,
  building: <path d="M5 21V5.8c0-.5.3-.9.8-1.1l8-2.5c.6-.2 1.2.3 1.2.9V21M3 21h18M9 8h2M9 12h2M9 16h2M15 9h3v12" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" />,
  dashboard: <><rect height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7" width="7" x="3" y="3" /><rect height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7" width="7" x="14" y="3" /><rect height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7" width="7" x="3" y="14" /><rect height="7" rx="1.5" stroke="currentColor" strokeWidth="1.7" width="7" x="14" y="14" /></>,
  database: <><ellipse cx="12" cy="5" rx="7.5" ry="3" stroke="currentColor" strokeWidth="1.7" /><path d="M4.5 5v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V5M4.5 11v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6" stroke="currentColor" strokeWidth="1.7" /></>,
  deal: <><path d="M4 7.5h16v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-11Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.7" /><path d="M8 7.5V5.8A2.3 2.3 0 0 1 10.3 3.5h3.4A2.3 2.3 0 0 1 16 5.8v1.7M4 12h16M10 12v2h4v-2" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></>,
  inbox: <><path d="M5.5 5.5h13l2 9.5v3a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-3l2-9.5Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.7" /><path d="M3.5 15h5l1.5 2h4l1.5-2h5" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.7" /></>,
  lead: <><circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.7" /><path d="M3.5 20v-1.3A5.7 5.7 0 0 1 9.2 13h.6a5.7 5.7 0 0 1 3.6 1.3M17 7v6M14 10h6" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></>,
  note: <><path d="M6 3.5h9l3 3V20a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 5 20V5A1.5 1.5 0 0 1 6.5 3.5Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.7" /><path d="M14 3.5V8h4M8.5 12h7M8.5 16h5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></>,
  planner: <><rect height="16" rx="2" stroke="currentColor" strokeWidth="1.7" width="17" x="3.5" y="5" /><path d="M7.5 3v4M16.5 3v4M3.5 9.5h17M7.5 13h2M12 13h2M16.5 13h.01M7.5 17h2M12 17h2" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></>,
  people: <><circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.7" /><path d="M3.5 20v-1.3A5.7 5.7 0 0 1 9.2 13h.6a5.7 5.7 0 0 1 5.7 5.7V20M16 5.5a3 3 0 0 1 0 5.8M18 14a5.5 5.5 0 0 1 2.5 4.6V20" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></>,
  search: <><circle cx="10.5" cy="10.5" r="5.5" stroke="currentColor" strokeWidth="1.7" /><path d="m15 15 4.5 4.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></>,
  pipeline: <><circle cx="6" cy="6" r="2.5" stroke="currentColor" strokeWidth="1.7" /><circle cx="18" cy="18" r="2.5" stroke="currentColor" strokeWidth="1.7" /><circle cx="18" cy="6" r="2.5" stroke="currentColor" strokeWidth="1.7" /><path d="M8.5 6h7M6 8.5v4A5.5 5.5 0 0 0 11.5 18h4" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" /></>,
  settings: <><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.7" /><path d="M19 13.5a7.2 7.2 0 0 0 0-3l2-1.4-2-3.4-2.3 1a7.7 7.7 0 0 0-2.6-1.5L13.8 3h-3.6l-.3 2.2a7.7 7.7 0 0 0-2.6 1.5l-2.3-1-2 3.4 2 1.4a7.2 7.2 0 0 0 0 3l-2 1.4 2 3.4 2.3-1a7.7 7.7 0 0 0 2.6 1.5l.3 2.2h3.6l.3-2.2a7.7 7.7 0 0 0 2.6-1.5l2.3 1 2-3.4-2-1.4Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.5" /></>,
  tag: <path d="M4 4h7l9 9-7 7-9-9V4Zm4 4h.01" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" />,
  task: <><rect height="17" rx="2" stroke="currentColor" strokeWidth="1.7" width="15" x="4.5" y="3.5" /><path d="m8 9 1.5 1.5L12 8M13.5 10H16M8 15h8" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" /></>,
};

export function NavigationIcon({ name, ...props }: NavigationIconProps) {
  return (
    <svg aria-hidden="true" fill="none" viewBox="0 0 24 24" {...props}>
      {paths[name]}
    </svg>
  );
}
