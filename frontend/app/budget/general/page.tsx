'use client'

import { useEffect, useState, Fragment } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'
import { useDataCache } from '@/contexts/DataCacheContext'
import { loadBudgetGeneralFromSupabase } from '@/lib/supabase-queries'

export default function BudgetGeneral() {
  const { baseWeek, budget_general, actuals_general } = useDataCache()
  const [budgetData, setBudgetData] = useState<any>(budget_general ?? null)
  const [actualsData, setActualsData] = useState<any>(actuals_general ?? null)
  const [loading, setLoading] = useState(!budget_general)
  const [selectedTabs, setSelectedTabs] = useState<string[]>([])
  const [collapsed, setCollapsed] = useState<boolean>(false)

  useEffect(() => {
    const loadBudgetData = async () => {
      if (!baseWeek) return
      // If budget cached, render immediately; fetch actuals in background if needed
      if (budget_general && budget_general.week === baseWeek) {
        setBudgetData(budget_general)
        if (actuals_general && actuals_general.week === baseWeek) {
          setActualsData(actuals_general)
        } else {
          // background fetch actuals
          ;(async () => {
            try {
              const { budget, actuals } = await loadBudgetGeneralFromSupabase(baseWeek, true)
              if (actuals) setActualsData(actuals)
            } catch {}
          })()
        }
        setLoading(false)
        return
      }
      setLoading(true)
      try {
        // Try Supabase first (with API fallback)
        const { budget, actuals } = await loadBudgetGeneralFromSupabase(baseWeek, true)
        if (budget) {
          setBudgetData(budget)
        } else {
          setBudgetData({ error: 'Failed to load budget data' })
        }
        if (actuals) {
          setActualsData(actuals)
        } else {
          setActualsData({ error: 'Failed to load actuals data' })
        }
      } catch (e) {
        setBudgetData({ error: 'Failed to load budget data' })
        setActualsData({ error: 'Failed to load actuals data' })
      } finally {
        setLoading(false)
      }
    }
    loadBudgetData()
  }, [baseWeek, budget_general, actuals_general])
  
  // Keep selection defaults in sync with months
  const months: string[] = budgetData?.months || []
  useEffect(() => {
    // Restore persisted UI state once on mount
    try {
      const savedTabs = localStorage.getItem('budget_general_selectedTabs')
      if (savedTabs) {
        const arr = JSON.parse(savedTabs)
        if (Array.isArray(arr)) setSelectedTabs(arr)
      }
      const savedCollapsed = localStorage.getItem('budget_general_collapsed')
      if (savedCollapsed !== null) setCollapsed(savedCollapsed === 'true')
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Persist selected tabs and collapsed state
  useEffect(() => {
    try {
      localStorage.setItem('budget_general_selectedTabs', JSON.stringify(selectedTabs))
      localStorage.setItem('budget_general_collapsed', String(collapsed))
    } catch {}
  }, [selectedTabs, collapsed])

  // Debug: log actuals data structure
  useEffect(() => {
    if (actualsData && !actualsData.error) {
      console.log('🔍 Budget General - Actuals data:', {
        week: actualsData.week,
        months: actualsData.months?.slice(0, 5),
        metrics_count: actualsData.metrics?.length,
        sample_metrics: actualsData.metrics?.slice(0, 10),
        sample_totals: Object.fromEntries(Object.entries(actualsData.totals || {}).slice(0, 5)),
        sample_table_keys: actualsData.table ? Object.keys(actualsData.table).slice(0, 3) : []
      })
    } else if (actualsData?.error) {
      console.warn('⚠️ Budget General - Actuals error:', actualsData.error)
    }
  }, [actualsData])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-3">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Loading Budget</h2>
            <p className="text-sm text-gray-600">Preparing overview…</p>
          </div>
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (budgetData?.error) {
    return <p className="text-gray-600">{budgetData.error}</p>
  }

  const fmt = new Intl.NumberFormat('sv-SE')

  // Toggle selection of tabs (Total or specific months)
  const toggleTab = (key: string) => {
    setSelectedTabs((prev) => {
      const has = prev.includes(key)
      if (has) return prev.filter((k) => k !== key)
      return [...prev, key]
    })
  }

  const renderTable = (selectedMonths: string[] | null) => {
    const metrics: string[] = budgetData?.metrics || []
    const sel = selectedMonths ?? selectedTabs
    const showTotal = sel.includes('Total')
    const showYTD = sel.includes('YTD')
    let monthKeys = sel.filter((k) => k !== 'Total' && k !== 'YTD')
    
    // Helper to normalize month names for matching
    const normalizeMonth = (m: string) => m.trim().toLowerCase()
    const actualsMonths = (actualsData?.months || []).map(normalizeMonth)
    const actualsMetrics = actualsData?.metrics || []
    const metricExists = (m: string) => actualsMetrics.includes(m)
    
    // Helper to find matching month (case-insensitive)
    const findActualsMonth = (budgetMonth: string): string | null => {
      if (!actualsData?.months) return null
      const normalized = normalizeMonth(budgetMonth)
      return actualsData.months.find((am: string) => normalizeMonth(am) === normalized) || null
    }
    
    return (
    <div className="mt-6 overflow-auto rounded-md border">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">Metric</th>
            <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">Customer</th>
            {showTotal && (
              <>
                <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">Total Budget</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">Total Actuals</th>
              </>
            )}
            {showYTD && (
              <>
                <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">YTD Budget</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">YTD Actuals</th>
              </>
            )}
            {monthKeys.map((m: string) => (
              <Fragment key={`head-${m}`}>
                <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">{m} Budget</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700 whitespace-nowrap">{m} Actuals</th>
              </Fragment>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric: string, idx: number) => {
            const hasActuals = metricExists(metric)
            return (
            <tr key={metric} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-3 py-2 whitespace-nowrap text-gray-900 font-medium">{budgetData?.display_name_by_metric?.[metric] || metric}</td>
              <td className="px-3 py-2 whitespace-nowrap text-gray-900">{budgetData?.customer_by_metric?.[metric] || ''}</td>
              {/* Total across all months */}
              {showTotal && (
                <>
                  <td className="px-3 py-2 whitespace-nowrap text-gray-900">{fmt.format(Number(budgetData?.totals?.[metric] ?? 0))}</td>
                  <td className={`px-3 py-2 whitespace-nowrap ${hasActuals ? 'text-gray-900' : 'text-gray-400'}`}>
                    {hasActuals ? fmt.format(Number(actualsData?.totals?.[metric] ?? 0)) : '-'}
                  </td>
                </>
              )}
              {showYTD && (
                <>
                  <td className="px-3 py-2 whitespace-nowrap text-gray-900">{fmt.format(Number(budgetData?.ytd_totals?.[metric] ?? 0))}</td>
                  <td className={`px-3 py-2 whitespace-nowrap ${hasActuals ? 'text-gray-900' : 'text-gray-400'}`}>
                    {hasActuals ? fmt.format(Number(actualsData?.ytd_totals?.[metric] ?? 0)) : '-'}
                  </td>
                </>
              )}
              {monthKeys.map((m: string) => {
                const vb = budgetData?.table?.[metric]?.[m] ?? 0
                // Try exact match first, then case-insensitive month match
                let va = actualsData?.table?.[metric]?.[m] ?? 0
                if (va === 0 && hasActuals && actualsData?.table?.[metric]) {
                  const matchingMonth = findActualsMonth(m)
                  if (matchingMonth) {
                    va = actualsData?.table?.[metric]?.[matchingMonth] ?? 0
                  }
                }
                return (
                  <Fragment key={`row-${metric}-${m}`}>
                    <td className="px-3 py-2 whitespace-nowrap text-gray-900">{fmt.format(Number(vb) || 0)}</td>
                    <td className={`px-3 py-2 whitespace-nowrap ${hasActuals ? 'text-gray-900' : 'text-gray-400'}`}>
                      {hasActuals ? fmt.format(Number(va) || 0) : '-'}
                    </td>
                  </Fragment>
                )
              })}
            </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )}

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Monthly overview</CardTitle>
            <Button variant="outline" size="sm" onClick={() => setCollapsed(!collapsed)}>
              {collapsed ? 'Expand' : 'Collapse'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {!collapsed && (
          <Fragment>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Week</div>
              <div className="text-sm font-medium">{budgetData?.week}</div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Columns</div>
              <div className="text-sm font-medium">{budgetData?.metrics?.length}</div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Rows</div>
              <div className="text-sm font-medium">{months.length} months</div>
            </div>
          </div>
          
          <div className="mt-6 flex flex-wrap gap-2">
            {['Total', 'YTD', ...months].map((key) => {
              const active = selectedTabs.includes(key)
              return (
                <Button
                  key={key}
                  variant={active ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => toggleTab(key)}
                >
                  {key}
                </Button>
              )
            })}
          </div>
          </Fragment>
          )}

          {!collapsed && renderTable(selectedTabs)}
        </CardContent>
      </Card>
    </div>
  )
}


