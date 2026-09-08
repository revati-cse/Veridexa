import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/ui";

export function Logo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const iconBox = { sm: "h-6 w-6", md: "h-8 w-8", lg: "h-11 w-11" }[size];
  const iconGlyph = { sm: 14, md: 18, lg: 24 }[size];
  const text = { sm: "text-sm", md: "text-lg", lg: "text-2xl sm:text-3xl" }[size];

  return (
    <span className="inline-flex items-center gap-2">
      <span className={cn("grid shrink-0 place-items-center rounded-lg bg-indigo-600", iconBox)}>
        <ShieldCheck size={iconGlyph} className="text-white" strokeWidth={2.25} />
      </span>
      <span className={cn("font-bold tracking-tight text-slate-900", text)}>
        VERIDEXA <span className="text-indigo-600">AI</span>
      </span>
    </span>
  );
}
