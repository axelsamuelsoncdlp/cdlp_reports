'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface ChartSettingsContextType {
  animationsEnabled: boolean
  setAnimationsEnabled: (enabled: boolean) => void
  isPdfGeneration: boolean // True when PDF is being generated
  setIsPdfGeneration: (isGenerating: boolean) => void
}

const ChartSettingsContext = createContext<ChartSettingsContextType | undefined>(undefined)

const STORAGE_KEY = 'chart_animations_enabled'

export function ChartSettingsProvider({ children }: { children: ReactNode }) {
  // Start with default value (true) to avoid hydration mismatch
  // We'll load from localStorage in useEffect after mount
  const [animationsEnabled, setAnimationsEnabledState] = useState<boolean>(true)
  
  const [isPdfGeneration, setIsPdfGeneration] = useState(false)

  // Load from localStorage after mount to avoid hydration mismatch
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored !== null) {
        setAnimationsEnabledState(stored === 'true')
      }
    }
  }, [])

  const setAnimationsEnabled = (enabled: boolean) => {
    setAnimationsEnabledState(enabled)
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, String(enabled))
    }
  }

  return (
    <ChartSettingsContext.Provider
      value={{
        animationsEnabled,
        setAnimationsEnabled,
        isPdfGeneration,
        setIsPdfGeneration,
      }}
    >
      {children}
    </ChartSettingsContext.Provider>
  )
}

export function useChartSettings() {
  const context = useContext(ChartSettingsContext)
  if (context === undefined) {
    throw new Error('useChartSettings must be used within a ChartSettingsProvider')
  }
  return context
}

// Helper hook to determine if animations should be active
export function useChartAnimations() {
  const { animationsEnabled, isPdfGeneration } = useChartSettings()
  // Always disable animations during PDF generation
  return animationsEnabled && !isPdfGeneration
}

