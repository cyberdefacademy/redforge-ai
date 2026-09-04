import * as React from "react"
import { cn } from "@/lib/utils"
export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(({className, ...props}, ref)=>
  <input className={cn("flex h-9 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-1 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-orange-600", className)} ref={ref} {...props} />
)
Input.displayName="Input"
