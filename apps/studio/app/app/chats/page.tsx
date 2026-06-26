import { Suspense } from "react";
import { ChatsPageClient } from "@/modules/chats/components/ChatsPageClient";
import { Skeleton } from "@/components/ui/skeleton";

function ChatsPageFallback() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 pt-8">
      <Skeleton className="mb-6 h-10 w-48" />
      <Skeleton className="mb-4 h-11 w-full rounded-xl" />
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}

export default function ChatsPage() {
  return (
    <Suspense fallback={<ChatsPageFallback />}>
      <ChatsPageClient />
    </Suspense>
  );
}
