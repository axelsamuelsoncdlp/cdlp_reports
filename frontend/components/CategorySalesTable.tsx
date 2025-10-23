'use client'

import { getCategorySales } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'

interface CategorySalesTableProps {
  baseWeek: string
}

export default function CategorySalesTable({ baseWeek }: CategorySalesTableProps) {
  const [categorySalesData, setCategorySalesData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      try {
        const data = await getCategorySales(baseWeek, 8)
        setCategorySalesData(data)
      } catch (err) {
        console.error('Failed to load category sales:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [baseWeek])

  const formatValue = (value: number): string => {
    if (value === 0) return '0'
    const thousandsValue = value / 1000
    const roundedThousands = Math.round(thousandsValue)
    return roundedThousands.toLocaleString('sv-SE')
  }

  const calculateYoY = (current: number, previous: number): number | null => {
    if (previous === 0) return null
    return ((current - previous) / previous) * 100
  }

  const formatYoY = (value: number | null): string => {
    if (value === null) return '-'
    const absValue = Math.abs(value)
    const formatted = Math.round(absValue).toString()
    if (value < 0) {
      return `(${formatted}%)`
    } else {
      return `${formatted}%`
    }
  }

  const getWeekNumber = (weekStr: string): string => {
    const parts = weekStr.split('-')
    return `W${parts[1]}`
  }

  if (loading || !categorySalesData) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <span className="text-gray-600">Loading category sales data...</span>
        </div>
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          {[...Array(15)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    )
  }

  const { category_sales, period_info } = categorySalesData
  
  // Get all unique categories
  const allCategories = new Set<string>()
  category_sales.forEach((week: any) => {
    Object.keys(week.categories).forEach(cat => allCategories.add(cat))
  })

  // Separate Men and Women categories
  const menCategories = Array.from(allCategories).filter(cat => cat.startsWith('MEN_')).map(cat => cat.replace('MEN_', ''))
  const womenCategories = Array.from(allCategories).filter(cat => cat.startsWith('WOMEN_')).map(cat => cat.replace('WOMEN_', ''))
  
  // Get week keys
  const weekKeys = category_sales.map((week: any) => week.week).sort()
  
  // Calculate last year weeks
  const lastYearWeeks = weekKeys.map(week => {
    const [year, weekNum] = week.split('-')
    return `${parseInt(year) - 1}-${weekNum}`
  })

  // Calculate totals for each week
  const calculateTotals = (categories: string[], gender: 'MEN' | 'WOMEN') => {
    const totals: Record<string, number> = {}
    weekKeys.forEach(week => {
      totals[week] = 0
      categories.forEach(cat => {
        const key = `${gender}_${cat}`
        category_sales.forEach((weekData: any) => {
          if (weekData.week === week) {
            totals[week] += weekData.categories[key] || 0
          }
        })
      })
    })
    return totals
  }

  const menTotals = calculateTotals(menCategories, 'MEN')
  const womenTotals = calculateTotals(womenCategories, 'WOMEN')
  const grandTotals: Record<string, number> = {}
  weekKeys.forEach(week => {
    grandTotals[week] = (menTotals[week] || 0) + (womenTotals[week] || 0)
  })

  // Calculate averages
  const calculateAverage = (totals: Record<string, number>): number => {
    const sum = Object.values(totals).reduce((a, b) => a + b, 0)
    return sum / Object.keys(totals).length
  }

  const menAvg = calculateAverage(menTotals)
  const womenAvg = calculateAverage(womenTotals)
  const grandAvg = calculateAverage(grandTotals)

  // Sort categories by average (highest to lowest)
  const sortCategoriesByAverage = (categories: string[], gender: 'MEN' | 'WOMEN') => {
    return categories.map(category => {
      const weekValues: Record<string, number> = {}
      weekKeys.forEach((week) => {
        const weekData = category_sales.find((w: any) => w.week === week)
        weekValues[week] = weekData?.categories[`${gender}_${category}`] || 0
      })
      const avg = Object.values(weekValues).reduce((a, b) => a + b, 0) / Object.keys(weekValues).length
      return { category, avg }
    }).sort((a, b) => b.avg - a.avg).map(item => item.category)
  }

  const sortedMenCategories = sortCategoriesByAverage(menCategories, 'MEN')
  const sortedWomenCategories = sortCategoriesByAverage(womenCategories, 'WOMEN')

  return (
    <div className="bg-gray-50 rounded-lg overflow-hidden overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gray-200 border-b">
            <th className="text-left py-2 px-2 font-medium text-gray-900" rowSpan={3}>Category</th>
            <th className="text-center py-2 px-2 font-medium text-gray-900 bg-gray-200" colSpan={9}>
              Latest Week: {period_info.latest_dates}
            </th>
            <th className="text-center py-2 px-2 font-medium text-gray-900 bg-yellow-100" colSpan={9}>
              Y/Y GROWTH%
            </th>
          </tr>
          <tr className="bg-gray-200 border-b">
            {weekKeys.map((week) => (
              <th key={week} className="text-right py-1 px-2 font-medium text-gray-900" rowSpan={2}>
                {getWeekNumber(week)}
              </th>
            ))}
            <th className="text-right py-1 px-2 font-medium text-gray-900 bg-blue-100" rowSpan={2}>Avg</th>
            {weekKeys.map((week) => (
              <th key={`yoy-${week}`} className="text-right py-1 px-2 font-medium text-gray-900 bg-yellow-50" rowSpan={2}>
                {getWeekNumber(week)}
              </th>
            ))}
            <th className="text-right py-1 px-2 font-medium text-gray-900 bg-yellow-50" rowSpan={2}>Avg</th>
          </tr>
        </thead>
        <tbody>
          {/* Men Categories */}
          {sortedMenCategories.map((category) => {
            const weekValues: Record<string, number> = {}
            const lastYearValues: Record<string, number> = {}
            
            weekKeys.forEach((week, index) => {
              const weekData = category_sales.find((w: any) => w.week === week)
              const lastYearWeek = lastYearWeeks[index]
              const lastYearData = category_sales.find((w: any) => w.week === lastYearWeek)
              
              weekValues[week] = weekData?.categories[`MEN_${category}`] || 0
              lastYearValues[lastYearWeek] = lastYearData?.categories[`MEN_${category}`] || 0
            })
            
            const avg = Object.values(weekValues).reduce((a, b) => a + b, 0) / Object.keys(weekValues).length
            
            return (
              <tr key={`MEN_${category}`} className="border-b border-gray-200">
                <td className="py-2 px-2 font-medium text-gray-900">{category}</td>
                {weekKeys.map((week) => (
                  <td key={week} className="py-2 px-2 text-right text-gray-700">
                    {formatValue(weekValues[week])}
                  </td>
                ))}
                <td className="py-2 px-2 text-right text-gray-700 bg-blue-50 font-medium">
                  {formatValue(avg)}
                </td>
                {weekKeys.map((week, weekIndex) => {
                  const lastYearWeek = lastYearWeeks[weekIndex]
                  const currentValue = weekValues[week]
                  const lastYearValue = lastYearValues[lastYearWeek]
                  const yoY = calculateYoY(currentValue, lastYearValue)
                  
                  return (
                    <td key={`yoy-${week}`} className="py-2 px-2 text-right text-gray-700 bg-yellow-50">
                      {formatYoY(yoY)}
                    </td>
                  )
                })}
                <td className="py-2 px-2 text-right text-gray-700 bg-yellow-50 font-medium">
                  {(() => {
                    let totalYoY = 0
                    let validWeeks = 0
                    weekKeys.forEach((week, weekIndex) => {
                      const lastYearWeek = lastYearWeeks[weekIndex]
                      const currentValue = weekValues[week]
                      const lastYearValue = lastYearValues[lastYearWeek]
                      const yoY = calculateYoY(currentValue, lastYearValue)
                      if (yoY !== null) {
                        totalYoY += yoY
                        validWeeks++
                      }
                    })
                    const avgYoY = validWeeks > 0 ? totalYoY / validWeeks : null
                    return formatYoY(avgYoY)
                  })()}
                </td>
              </tr>
            )
          })}
          
          {/* Men Total */}
          <tr className="bg-gray-200 border-b font-semibold">
            <td className="py-2 px-2 font-bold text-gray-900">Men Total</td>
            {weekKeys.map((week) => (
              <td key={week} className="py-2 px-2 text-right text-gray-700">
                {formatValue(menTotals[week])}
              </td>
            ))}
            <td className="py-2 px-2 text-right text-gray-700 bg-blue-50 font-medium">
              {formatValue(menAvg)}
            </td>
            {weekKeys.map((week, weekIndex) => {
              const lastYearWeek = lastYearWeeks[weekIndex]
              const currentValue = menTotals[week]
              const lastYearValue = menTotals[lastYearWeek] || 0
              const yoY = calculateYoY(currentValue, lastYearValue)
              
              return (
                <td key={`yoy-${week}`} className="py-2 px-2 text-right text-gray-700 bg-yellow-50">
                  {formatYoY(yoY)}
                </td>
              )
            })}
            <td className="py-2 px-2 text-right text-gray-700 bg-yellow-50 font-medium">
              {(() => {
                let totalYoY = 0
                let validWeeks = 0
                weekKeys.forEach((week, weekIndex) => {
                  const lastYearWeek = lastYearWeeks[weekIndex]
                  const currentValue = menTotals[week]
                  const lastYearValue = menTotals[lastYearWeek] || 0
                  const yoY = calculateYoY(currentValue, lastYearValue)
                  if (yoY !== null) {
                    totalYoY += yoY
                    validWeeks++
                  }
                })
                const avgYoY = validWeeks > 0 ? totalYoY / validWeeks : null
                return formatYoY(avgYoY)
              })()}
            </td>
          </tr>

          {/* Women Categories */}
          {sortedWomenCategories.map((category) => {
            const weekValues: Record<string, number> = {}
            const lastYearValues: Record<string, number> = {}
            
            weekKeys.forEach((week, index) => {
              const weekData = category_sales.find((w: any) => w.week === week)
              const lastYearWeek = lastYearWeeks[index]
              const lastYearData = category_sales.find((w: any) => w.week === lastYearWeek)
              
              weekValues[week] = weekData?.categories[`WOMEN_${category}`] || 0
              lastYearValues[lastYearWeek] = lastYearData?.categories[`WOMEN_${category}`] || 0
            })
            
            const avg = Object.values(weekValues).reduce((a, b) => a + b, 0) / Object.keys(weekValues).length
            
            return (
              <tr key={`WOMEN_${category}`} className="border-b border-gray-200">
                <td className="py-2 px-2 font-medium text-gray-900">{category}</td>
                {weekKeys.map((week) => (
                  <td key={week} className="py-2 px-2 text-right text-gray-700">
                    {formatValue(weekValues[week])}
                  </td>
                ))}
                <td className="py-2 px-2 text-right text-gray-700 bg-blue-50 font-medium">
                  {formatValue(avg)}
                </td>
                {weekKeys.map((week, weekIndex) => {
                  const lastYearWeek = lastYearWeeks[weekIndex]
                  const currentValue = weekValues[week]
                  const lastYearValue = lastYearValues[lastYearWeek]
                  const yoY = calculateYoY(currentValue, lastYearValue)
                  
                  return (
                    <td key={`yoy-${week}`} className="py-2 px-2 text-right text-gray-700 bg-yellow-50">
                      {formatYoY(yoY)}
                    </td>
                  )
                })}
                <td className="py-2 px-2 text-right text-gray-700 bg-yellow-50 font-medium">
                  {(() => {
                    let totalYoY = 0
                    let validWeeks = 0
                    weekKeys.forEach((week, weekIndex) => {
                      const lastYearWeek = lastYearWeeks[weekIndex]
                      const currentValue = weekValues[week]
                      const lastYearValue = lastYearValues[lastYearWeek]
                      const yoY = calculateYoY(currentValue, lastYearValue)
                      if (yoY !== null) {
                        totalYoY += yoY
                        validWeeks++
                      }
                    })
                    const avgYoY = validWeeks > 0 ? totalYoY / validWeeks : null
                    return formatYoY(avgYoY)
                  })()}
                </td>
              </tr>
            )
          })}
          
          {/* Women Total */}
          <tr className="bg-gray-200 border-b font-semibold">
            <td className="py-2 px-2 font-bold text-gray-900">Women Total</td>
            {weekKeys.map((week) => (
              <td key={week} className="py-2 px-2 text-right text-gray-700">
                {formatValue(womenTotals[week])}
              </td>
            ))}
            <td className="py-2 px-2 text-right text-gray-700 bg-blue-50 font-medium">
              {formatValue(womenAvg)}
            </td>
            {weekKeys.map((week, weekIndex) => {
              const lastYearWeek = lastYearWeeks[weekIndex]
              const currentValue = womenTotals[week]
              const lastYearValue = womenTotals[lastYearWeek] || 0
              const yoY = calculateYoY(currentValue, lastYearValue)
              
              return (
                <td key={`yoy-${week}`} className="py-2 px-2 text-right text-gray-700 bg-yellow-50">
                  {formatYoY(yoY)}
                </td>
              )
            })}
            <td className="py-2 px-2 text-right text-gray-700 bg-yellow-50 font-medium">
              {(() => {
                let totalYoY = 0
                let validWeeks = 0
                weekKeys.forEach((week, weekIndex) => {
                  const lastYearWeek = lastYearWeeks[weekIndex]
                  const currentValue = womenTotals[week]
                  const lastYearValue = womenTotals[lastYearWeek] || 0
                  const yoY = calculateYoY(currentValue, lastYearValue)
                  if (yoY !== null) {
                    totalYoY += yoY
                    validWeeks++
                  }
                })
                const avgYoY = validWeeks > 0 ? totalYoY / validWeeks : null
                return formatYoY(avgYoY)
              })()}
            </td>
          </tr>

          {/* Grand Total */}
          <tr className="bg-gray-300 border-b font-bold">
            <td className="py-2 px-2 font-bold text-gray-900">Grand Total</td>
            {weekKeys.map((week) => (
              <td key={week} className="py-2 px-2 text-right text-gray-700">
                {formatValue(grandTotals[week])}
              </td>
            ))}
            <td className="py-2 px-2 text-right text-gray-700 bg-blue-100 font-medium">
              {formatValue(grandAvg)}
            </td>
            {weekKeys.map((week, weekIndex) => {
              const lastYearWeek = lastYearWeeks[weekIndex]
              const currentValue = grandTotals[week]
              const lastYearValue = grandTotals[lastYearWeek] || 0
              const yoY = calculateYoY(currentValue, lastYearValue)
              
              return (
                <td key={`yoy-${week}`} className="py-2 px-2 text-right text-gray-700 bg-yellow-100">
                  {formatYoY(yoY)}
                </td>
              )
            })}
            <td className="py-2 px-2 text-right text-gray-700 bg-yellow-100 font-medium">
              {(() => {
                let totalYoY = 0
                let validWeeks = 0
                weekKeys.forEach((week, weekIndex) => {
                  const lastYearWeek = lastYearWeeks[weekIndex]
                  const currentValue = grandTotals[week]
                  const lastYearValue = grandTotals[lastYearWeek] || 0
                  const yoY = calculateYoY(currentValue, lastYearValue)
                  if (yoY !== null) {
                    totalYoY += yoY
                    validWeeks++
                  }
                })
                const avgYoY = validWeeks > 0 ? totalYoY / validWeeks : null
                return formatYoY(avgYoY)
              })()}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

