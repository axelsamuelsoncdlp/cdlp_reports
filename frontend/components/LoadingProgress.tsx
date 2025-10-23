'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Loader2 } from 'lucide-react'

interface LoadingProgressProps {
  progress: {
    step: 'periods' | 'metrics' | 'markets' | 'kpis' | 'complete'
    stepNumber: number
    totalSteps: number
    message: string
    percentage: number
  }
}

export default function LoadingProgress({ progress }: LoadingProgressProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="max-w-md w-full mx-4">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
              <div>
                <h3 className="font-semibold text-gray-900">Loading Dashboard Data</h3>
                <p className="text-sm text-gray-600">
                  Step {progress.stepNumber} of {progress.totalSteps}: {progress.message}
                </p>
              </div>
            </div>
            <Progress value={progress.percentage} className="h-2" />
            <div className="text-xs text-gray-500 text-center">
              {progress.percentage}% complete
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

