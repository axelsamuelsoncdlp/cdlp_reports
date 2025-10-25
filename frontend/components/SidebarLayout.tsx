'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { useState } from 'react'
import { IconChartBar, IconFileChart, IconTrendingUp, IconSettings, IconChevronDown, IconChevronRight, IconMenu2, IconX } from '@tabler/icons-react'

export default function SidebarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isGeneralOpen, setIsGeneralOpen] = useState(true)
  const [isMarketingOpen, setIsMarketingOpen] = useState(true)

  const isActive = (path: string) => pathname === path

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className={`${isCollapsed ? 'w-16' : 'w-64'} transition-all duration-300 flex-shrink-0 border-r bg-gray-50`}>
        <div className="flex flex-col h-full">
          {/* Toggle Button */}
          <div className="flex items-center justify-between p-4 border-b">
            {!isCollapsed && <h2 className="text-lg font-semibold text-gray-900">Menu</h2>}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 rounded-md hover:bg-gray-200 transition-colors"
              aria-label="Toggle sidebar"
            >
              {isCollapsed ? <IconMenu2 className="h-5 w-5" /> : <IconX className="h-5 w-5" />}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-4">
            <nav className="flex flex-col space-y-1">
              {/* General Dropdown */}
              <div>
                <button
                  onClick={() => setIsGeneralOpen(!isGeneralOpen)}
                  className={`w-full flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive('/summary') || isActive('/top-markets') || isActive('/online-kpis') || 
                    isActive('/contribution') || isActive('/gender-sales') || isActive('/men-category-sales') || 
                    isActive('/women-category-sales') || isActive('/category-sales') || isActive('/products-new') || 
                    isActive('/products-gender')
                      ? 'bg-gray-200 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <IconChartBar className="h-4 w-4 flex-shrink-0" />
                  {!isCollapsed && (
                    <>
                      <span className="flex-1 text-left">General</span>
                      {isGeneralOpen ? <IconChevronDown className="h-4 w-4" /> : <IconChevronRight className="h-4 w-4" />}
                    </>
                  )}
                </button>
                
                {!isCollapsed && isGeneralOpen && (
                  <div className="ml-4 mt-1 space-y-1">
                    <Link
                      href="/summary"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/summary')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Summary
                    </Link>
                    <Link
                      href="/top-markets"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/top-markets')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconFileChart className="h-4 w-4" />
                      Top Markets
                    </Link>
                    <Link
                      href="/online-kpis"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/online-kpis')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconTrendingUp className="h-4 w-4" />
                      Online KPIs
                    </Link>
                    <Link
                      href="/contribution"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/contribution')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconTrendingUp className="h-4 w-4" />
                      Contribution
                    </Link>
                    <Link
                      href="/gender-sales"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/gender-sales')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Gender Sales
                    </Link>
                    <Link
                      href="/men-category-sales"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/men-category-sales')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Men Category Sales
                    </Link>
                    <Link
                      href="/women-category-sales"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/women-category-sales')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Women Category Sales
                    </Link>
                    <Link
                      href="/category-sales"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/category-sales')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Category Sales
                    </Link>
                    <Link
                      href="/products-new"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/products-new')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Products New
                    </Link>
                    <Link
                      href="/products-gender"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/products-gender')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Products Gender
                    </Link>
                  </div>
                )}
              </div>

              {/* Marketing Dropdown */}
              <div>
                <button
                  onClick={() => setIsMarketingOpen(!isMarketingOpen)}
                  className={`w-full flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive('/sessions-per-country')
                      ? 'bg-gray-200 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <IconTrendingUp className="h-4 w-4 flex-shrink-0" />
                  {!isCollapsed && (
                    <>
                      <span className="flex-1 text-left">Marketing</span>
                      {isMarketingOpen ? <IconChevronDown className="h-4 w-4" /> : <IconChevronRight className="h-4 w-4" />}
                    </>
                  )}
                </button>
                
                {!isCollapsed && isMarketingOpen && (
                  <div className="ml-4 mt-1 space-y-1">
                    <Link
                      href="/sessions-per-country"
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/sessions-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Sessions per Country
                    </Link>
                  </div>
                )}
              </div>

              {/* Settings */}
              <Link
                href="/settings"
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive('/settings')
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <IconSettings className="h-4 w-4" />
                {!isCollapsed && <span>Settings</span>}
              </Link>
            </nav>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <header className="bg-white shadow-sm border-b">
          <div className="px-6 py-4">
            <h1 className="text-2xl font-bold text-gray-900">Weekly Report Generator</h1>
            <p className="text-gray-600 mt-1">Generate professional reports with data validation</p>
          </div>
        </header>
        <main className="flex-1 bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

