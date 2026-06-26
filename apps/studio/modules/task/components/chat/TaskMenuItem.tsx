import { cn } from "@/lib/utils";

type TaskMenuItemProps = {
  icon: React.ReactNode;
  label: string;
  onClick?: () => void;
  className?: string;
  trailing?: React.ReactNode;
};

export function TaskMenuItem({
  icon,
  label,
  onClick,
  className,
  trailing,
}: TaskMenuItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm hover:bg-muted",
        className,
      )}
    >
      <span className="text-muted-foreground">{icon}</span>
      <span className="flex-1 text-left">{label}</span>
      {trailing}
    </button>
  );
}
