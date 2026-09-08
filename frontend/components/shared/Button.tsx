import type { ButtonHTMLAttributes, ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/ui";

type Variant = "primary" | "secondary" | "ghost";

const VARIANT_CLASS: Record<Variant, string> = {
  primary:
    "bg-indigo-600 text-white shadow-soft hover:bg-indigo-500 disabled:hover:bg-indigo-600",
  secondary:
    "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50 disabled:hover:bg-white",
  ghost: "text-slate-600 hover:bg-slate-100 disabled:hover:bg-transparent",
};

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  icon?: ReactNode;
}

export function Button({ variant = "primary", icon, className, children, ...props }: ButtonProps) {
  return (
    <button className={cn(BASE, VARIANT_CLASS[variant], className)} {...props}>
      {icon}
      {children}
    </button>
  );
}

export function LinkButton({
  href,
  variant = "primary",
  icon,
  className,
  children,
}: {
  href: string;
  variant?: Variant;
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={cn(BASE, VARIANT_CLASS[variant], className)}>
      {icon}
      {children}
    </Link>
  );
}
