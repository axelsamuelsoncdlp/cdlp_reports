import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Normalizes data structure from Supabase or API to handle both:
 * - Direct array: [...]
 * - Wrapped in object: { key: [...] }
 * - Object with key: { key: {...} }
 */
export function normalizeDataArray<T = any>(
  data: any,
  key?: string
): T[] {
  if (!data) return []
  
  // If key is provided, try to extract from object
  if (key) {
    if (data[key] && Array.isArray(data[key])) {
      return data[key] as T[]
    } else if (data[key] && typeof data[key] === 'object') {
      return Object.values(data[key]) as T[]
    }
  }
  
  // If data is already an array, return it
  if (Array.isArray(data)) {
    return data as T[]
  }
  
  // If data is an object with the key, extract it
  if (typeof data === 'object') {
    const firstKey = Object.keys(data)[0]
    if (firstKey && data[firstKey]) {
      if (Array.isArray(data[firstKey])) {
        return data[firstKey] as T[]
      } else if (typeof data[firstKey] === 'object') {
        return Object.values(data[firstKey]) as T[]
      }
    }
  }
  
  return []
}
