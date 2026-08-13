import { apiClient } from "@/services/api-client";
import type { Contact, ContactInput, ContactsListParams } from "@/types/contact";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const contactService = {
  create(contact: ContactInput): Promise<Contact> {
    return apiClient.post<Contact>("/contacts", JSON.stringify(contact));
  },

  get(contactId: string): Promise<Contact> {
    return apiClient.get<Contact>(`/contacts/${contactId}`, { cache: "no-store" });
  },

  list(params: ContactsListParams = {}): Promise<PaginatedResponse<Contact>> {
    return apiClient.get<PaginatedResponse<Contact>>(
      `/contacts${toQueryString(params)}`,
      { cache: "no-store" },
    );
  },

  remove(contactId: string): Promise<void> {
    return apiClient.delete<void>(`/contacts/${contactId}`);
  },

  update(contactId: string, contact: Partial<ContactInput>): Promise<Contact> {
    return apiClient.patch<Contact>(`/contacts/${contactId}`, JSON.stringify(contact));
  },
};
