import { ContactsWorkspace } from "@/features/contacts/contacts-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function ContactsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <ContactsWorkspace initialCreate={params.create === "1"} />;
}
