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

  const getPageTitle = () => {
    const titles: Record<string, { title: string; subtitle: string }> = {
      '/summary': { title: 'Summary', subtitle: 'Overview of weekly metrics' },
      '/top-markets': { title: 'Top Markets', subtitle: 'Sales performance by country' },
      '/online-kpis': { title: 'Online KPIs', subtitle: 'Key performance indicators for online sales' },
      '/contribution': { title: 'Contribution', subtitle: 'New vs returning customer contribution' },
      '/gender-sales': { title: 'Gender Sales', subtitle: 'Sales breakdown by gender' },
      '/men-category-sales': { title: 'Men Category Sales', subtitle: 'Sales by men product categories' },
      '/women-category-sales': { title: 'Women Category Sales', subtitle: 'Sales by women product categories' },
      '/category-sales': { title: 'Category Sales', subtitle: 'Sales by category with YoY growth' },
      '/products-new': { title: 'Products New', subtitle: 'Top products for new and returning customers' },
      '/products-gender': { title: 'Products Gender', subtitle: 'Top products by gender' },
      '/sessions-per-country': { title: 'Sessions per Country', subtitle: '(‘000)' },
      '/conversion-per-country': { title: 'Conversion per Country', subtitle: 'Conversion rates by country' },
      '/new-customers-per-country': { title: 'New Customers per Country', subtitle: 'New customer acquisition by country' },
      '/returning-customers-per-country': { title: 'Returning Customers per Country', subtitle: 'Returning customers by country' },
      '/aov-new-customers-per-country': { title: 'AOV New Customers per Country', subtitle: '(SEK)' },
      '/aov-returning-customers-per-country': { title: 'AOV Returning Customers per Country', subtitle: '(SEK)' },
      '/marketing-spend-per-country': { title: 'Marketing Spend per Country', subtitle: '(SEK \'000)' },
      '/ncac-per-country': { title: 'nCAC per Country', subtitle: '(SEK)' },
      '/contribution-new-per-country': { title: 'Contribution New Customer per Country', subtitle: '(SEK)' },
      '/contribution-new-total-per-country': { title: 'Contribution New Total per Country', subtitle: '(SEK \'000)' },
      '/contribution-returning-per-country': { title: 'Contribution Returning Customer per Country', subtitle: '(SEK)' },
      '/contribution-returning-total-per-country': { title: 'Contribution Returning Total per Country', subtitle: '(SEK \'000)' },
      '/total-contribution-per-country': { title: 'Total Contribution per Country', subtitle: '(SEK \'000)' },
      '/settings': { title: 'Settings', subtitle: 'Configure data sources and file uploads' },
    }
    
    return titles[pathname] || { title: 'Weekly Report', subtitle: 'Generate professional reports with data validation' }
  }

  const { title, subtitle } = getPageTitle()

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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                      prefetch={true}
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
                    isActive('/sessions-per-country') || isActive('/conversion-per-country') || isActive('/new-customers-per-country') || isActive('/returning-customers-per-country') || isActive('/aov-new-customers-per-country') || isActive('/aov-returning-customers-per-country') || isActive('/marketing-spend-per-country') || isActive('/ncac-per-country') || isActive('/contribution-new-per-country')
                      ? 'bg-gray-200 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <IconTrendingUp className="h-4 w-4 flex-shrink-0" />
                  {!isCollapsed && (
                    <>
                      <span className="flex-1 text-left">Markets</span>
                      {isMarketingOpen ? <IconChevronDown className="h-4 w-4" /> : <IconChevronRight className="h-4 w-4" />}
                    </>
                  )}
                </button>
                
                {!isCollapsed && isMarketingOpen && (
                  <div className="ml-4 mt-1 space-y-1">
                    <Link
                      href="/sessions-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/sessions-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Sessions per Country
                    </Link>
                    <Link
                      href="/conversion-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/conversion-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Conversion per Country
                    </Link>
                    <Link
                      href="/new-customers-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/new-customers-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      New Customers
                    </Link>
                    <Link
                      href="/returning-customers-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/returning-customers-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Returning Customers
                    </Link>
                    <Link
                      href="/aov-new-customers-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/aov-new-customers-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      AOV New Customers
                    </Link>
                    <Link
                      href="/aov-returning-customers-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/aov-returning-customers-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      AOV Returning Customers
                    </Link>
                    <Link
                      href="/marketing-spend-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/marketing-spend-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Marketing Spend
                    </Link>
                    <Link
                      href="/ncac-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/ncac-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      nCAC
                    </Link>
                    <Link
                      href="/contribution-new-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/contribution-new-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Contribution New Customer
                    </Link>
                    <Link
                      href="/contribution-new-total-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/contribution-new-total-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Contribution New Total
                    </Link>
                    <Link
                      href="/contribution-returning-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/contribution-returning-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Contribution Returning Customer
                    </Link>
                    <Link
                      href="/contribution-returning-total-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/contribution-returning-total-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Contribution Returning Total
                    </Link>
                    <Link
                      href="/total-contribution-per-country"
                      prefetch={true}
                      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                        isActive('/total-contribution-per-country')
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <IconChartBar className="h-4 w-4" />
                      Total Contribution
                    </Link>
                  </div>
                )}
              </div>

              {/* Settings */}
              <Link
                href="/settings"
                prefetch={true}
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
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            <p className="text-gray-600 mt-1">{subtitle}</p>
          </div>
        </header>
        <main className="flex-1 bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

