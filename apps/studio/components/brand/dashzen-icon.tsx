import { cn } from "@/lib/utils";

type DashZenIconProps = {
  size?: number;
  className?: string;
};

export function DashZenIcon({ size = 32, className }: DashZenIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={cn("shrink-0 text-foreground", className)}
    >
      <rect x="2" y="2" width="13" height="13" rx="3" className="fill-foreground/10 stroke-foreground/30" strokeWidth="1" />
      <rect x="17" y="2" width="13" height="13" rx="3" className="fill-foreground/10 stroke-foreground/30" strokeWidth="1" />
      <rect x="2" y="17" width="13" height="13" rx="3" className="fill-foreground/10 stroke-foreground/30" strokeWidth="1" />
      <rect x="17" y="17" width="13" height="13" rx="3" className="fill-foreground stroke-foreground" strokeWidth="1" />

      <path
        d="M23.5 20.2 24.1 22.6 26.5 23.2 24.1 23.8 23.5 26.2 22.9 23.8 20.5 23.2 22.9 22.6Z"
        className="fill-background"
      />
      <circle cx="25.8" cy="20.4" r="0.9" className="fill-background" />
    </svg>
  );
}
