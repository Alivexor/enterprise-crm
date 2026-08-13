"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@/services/api-client";
import { contactService } from "@/services/contact-service";
import type { Contact } from "@/types/contact";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Unable to load contact options.";
}

export function useContactOptions() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    async function loadContacts() {
      try {
        const response = await contactService.list({
          page: 1,
          page_size: 100,
          sort_by: "last_name",
        });
        if (isActive) {
          setContacts(response.items);
          setError(null);
        }
      } catch (caughtError) {
        if (isActive) {
          setError(getErrorMessage(caughtError));
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadContacts();
    return () => {
      isActive = false;
    };
  }, []);

  return { contacts, error, isLoading };
}
