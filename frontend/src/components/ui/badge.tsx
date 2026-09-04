import { cn } from "@/lib/utils"
export function Badge({className, variant="default", ...props}: React.HTMLAttributes<HTMLSpanElement> & {variant?:string}) {
  const v:Record<string,string>={default:"bg-orange-600 text-white", secondary:"bg-zinc-800 text-zinc-300", outline:"border border-zinc-700", success:"bg-emerald-600 text-white", warning:"bg-amber-600 text-white", danger:"bg-red-600 text-white"}
  return <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold", v[variant]||v.default, className)} {...props} />
}
