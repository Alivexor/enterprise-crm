import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Enterprise CRM V3",
    short_name: "CRM V3",
    description: "Bilingual local-first sales CRM and revenue operating system.",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#070b18",
    theme_color: "#111827",
    orientation: "any",
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml" },
    ],
  };
}
