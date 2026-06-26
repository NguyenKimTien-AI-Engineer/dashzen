import { cn } from "@/lib/utils";

type UserAvatarProps = {
  displayName?: string | null;
  email: string;
  avatarUrl?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const sizeClasses = {
  sm: "size-8 text-sm",
  md: "size-12 text-lg",
  lg: "size-16 text-xl",
} as const;

function getUserInitial(displayName: string | null | undefined, email: string): string {
  const source = displayName?.trim() || email;
  return source.charAt(0).toUpperCase() || "?";
}

export function UserAvatar({
  displayName,
  email,
  avatarUrl,
  size = "md",
  className,
}: UserAvatarProps) {
  const sizeClass = sizeClasses[size];

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt=""
        className={cn("shrink-0 rounded-full object-cover", sizeClass, className)}
      />
    );
  }

  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full bg-foreground font-semibold text-background",
        sizeClass,
        className,
      )}
      aria-hidden
    >
      {getUserInitial(displayName, email)}
    </span>
  );
}
