import * as React from "react"
import { cn } from "@/lib/utils"
export function Button({className, variant="default", size="default", ...props}: React.ButtonHTMLAttributes<HTMLButtonElement> & {variant?:string, size?:string}) {
  const base="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50"
  const variants:Record<string,string>={default:"bg-orange-600 text-white hover:bg-orange-700", outline:"border border-zinc-700 bg-transparent hover:bg-zinc-800", ghost:"hover:bg-zinc-800", destructive:"bg-red-600 text-white hover:bg-red-700"}
  const sizes:Record<string,string>={default:"h-9 px-4 py-2", sm:"h-8 px-3", lg:"h-10 px-8", icon:"h-9 w-9"}
  return <button className={cn(base, variants[variant]||variants.default, sizes[size]||sizes.default, className)} {...props} />
}
