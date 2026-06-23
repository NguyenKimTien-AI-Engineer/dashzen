import { Archive, MessagesSquare, Plus, Shapes } from "lucide-react";

import { cn } from "@/lib/utils";

export function NewChatIcon({ className }: { className?: string }) {
  return <Plus className={cn("size-4 shrink-0 stroke-[2.5]", className)} aria-hidden />;
}

export function ChatsIcon({ className }: { className?: string }) {
  return <MessagesSquare className={cn("size-4 shrink-0 stroke-[1.75]", className)} aria-hidden />;
}

export function ProjectsIcon({ className }: { className?: string }) {
  return <Archive className={cn("size-4 shrink-0 stroke-[1.75]", className)} aria-hidden />;
}

export function ArtifactsIcon({ className }: { className?: string }) {
  return <Shapes className={cn("size-4 shrink-0 stroke-[1.75]", className)} aria-hidden />;
}
