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
      viewBox="140 140 400 400"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={cn("shrink-0", className)}
    >
      <rect x="140" y="140" width="400" height="400" rx="92" fill="#000000" />
      <path
        d="M272 365A105 105 0 1 1 408 365"
        stroke="#FFFFFF"
        strokeWidth="20"
        strokeLinecap="round"
      />
      <rect x="242" y="456" width="48" height="36" rx="9" fill="#FFFFFF" fillOpacity="0.33" />
      <rect x="306" y="428" width="48" height="64" rx="9" fill="#FFFFFF" fillOpacity="0.62" />
      <rect x="370" y="392" width="48" height="100" rx="9" fill="#FFFFFF" />
    </svg>
  );
}
