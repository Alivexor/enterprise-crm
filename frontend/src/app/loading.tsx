import { LoadingState } from "@/components/ui/page-state";

export default function Loading() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-6xl items-center px-4 py-6 sm:px-6 lg:px-8">
      <div className="w-full">
        <LoadingState label="Loading Enterprise CRM…" />
      </div>
    </main>
  );
}
