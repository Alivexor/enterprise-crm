import { ContactDetail } from "@/features/contacts/contact-detail";

type ContactDetailPageProps = { params: Promise<{ contactId: string }> };

export default async function ContactDetailPage({ params }: ContactDetailPageProps) {
  const { contactId } = await params;
  return <ContactDetail contactId={contactId} />;
}
