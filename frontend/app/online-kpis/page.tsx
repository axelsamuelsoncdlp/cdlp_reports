'use client'

import { useState, useEffect } from 'react'
import { getPeriods, getOnlineKPIs, type OnlineKPIsResponse } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function OnlineKPIs() {
  const [selectedWeek, setSelectedWeek] = useState('2025-42')
  const [periods, setPeriods] = useState(null)
  const [kpisData, setKpisData] = useState<OnlineKPIsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load periods on mount
  useEffect(() => {
    const loadPeriods = async () => {
      try {
        const data = await getPeriods(selectedWeek)
        setPeriods(data)
      } catch (err) {
        console.error('Failed to load periods:', err)
      }
    }
    loadPeriods()
  }, [selectedWeek])

  // Load KPIs data
  useEffect(() => {
    if (!periods) return

    const loadKPIs = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const data = await getOnlineKPIs(selectedWeek, 8)
        setKpisData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch Online KPIs')
      } finally {
        setLoading(false)
      }
    }

    loadKPIs()
  }, [periods, selectedWeek])

  const chartData = kpisData?.kpis.map(kpi => {
    const weekNum = kpi.week.split('-')[1]
    return {
      week: `W${weekNum}`,
      current: kpi.aov_new_customer,
      lastYear: kpi.last_year?.aov_new_customer || 0
    }
  }) || []

  const kpiLabels = [
    { key: 'aov_new_customer', label: 'AOV New Customer', format: (val: number) => `SEK ${val.toFixed(0)}` },
    { key: 'aov_returning_customer', label: 'AOV Returning Customer', format: (val: number) => `SEK ${val.toFixed(0)}` },
    { key: 'cos', label: 'COS', format: (val: number) => `SEK ${(val / 1000).toFixed(0)}k` },
    { key: 'conversion_rate', label: 'Conversion Rate', format: (val: number) => `${val.toFixed(1)}%` },
    { key: 'new_customers', label: 'New Customers', format: (val: number) => val.toLocaleString() },
    { key: 'returning_customers', label: 'Returning Customers', format: (val: number) => val.toLocaleString() },
    { key: 'sessions', label: 'Sessions', format: (val: number) => val.toLocaleString() },
    { key: 'new_customer_cac', label: 'New Customer CAC', format: (val: number) => `SEK ${val.toFixed(0)}` }
  ]

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-gray-600">Loading Online KPIs...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-red-600">{error}</div>
        </div>
      </div>
    )
  }

  if (!kpisData) {
    return (
      <div className="space-y-8">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-gray-600">No KPIs data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Online KPIs</h2>
        
        <div className="grid grid-cols-3 gap-6">
          {kpiLabels.map((kpi, index) => {
            const chartData = kpisData.kpis.map(k => {
              const weekNum = k.week.split('-')[1]
              const currentValue = k[kpi.key as keyof typeof k] as number
              const lastYearValue = k.last_year?.[kpi.key as keyof typeof k.last_year] as number || 0
              
              return {
                week: `W${weekNum}`,
                current: currentValue,
                lastYear: lastYearValue
              }
            })

            return (
              <div key={index} className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-4">{kpi.label}</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="current" stroke="#8884d8" name="Current Year" />
                    <Line type="monotone" dataKey="lastYear" stroke="#82ca9d" name="Last Year" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

