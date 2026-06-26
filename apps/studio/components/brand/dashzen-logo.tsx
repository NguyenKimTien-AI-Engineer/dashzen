import Link from "next/link";
import { cn } from "@/lib/utils";
import { DashZenIcon } from "./dashzen-icon";

type DashZenLogoProps = {
  showStudio?: boolean;
  showIcon?: boolean;
  iconSize?: number;
  href?: string | null;
  className?: string;
};

export function DashZenLogo({
  showStudio = false,
  showIcon = true,
  iconSize = 36,
  href = null,
  className,
}: DashZenLogoProps) {
  const content = (
    <>
      {showIcon && <DashZenIcon size={iconSize} />}
      <div className="flex items-baseline gap-1 leading-none">
        <span className="text-xl font-semibold tracking-tight">DashZen</span>
        {showStudio && (
          <span className="text-sm font-medium text-muted-foreground">Studio</span>
        )}
      </div>
    </>
  );

  const classes = cn("inline-flex items-center gap-2.5", className);

  if (href) {
    return (
      <Link href={href} className={cn(classes, "transition-opacity hover:opacity-80")}>
        {content}
      </Link>
    );
  }

  return <div className={classes}>{content}</div>;
}
