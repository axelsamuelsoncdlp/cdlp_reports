'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { IconChartBar, IconFileChart, IconTrendingUp, IconSettings } from '@tabler/icons-react'

export default function SidebarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r bg-gray-50">
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto py-4">
            <nav className="flex flex-col space-y-1">
              <Link
                href="/"
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  pathname === '/'
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <IconChartBar className="h-4 w-4" />
                Dashboard
              </Link>
              <Link
                href="/summary"
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  pathname === '/summary'
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
                  pathname === '/top-markets'
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
                  pathname === '/online-kpis'
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
                  pathname === '/contribution'
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <IconTrendingUp className="h-4 w-4" />
                Contribution
              </Link>
              <Link
                href="/settings"
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  pathname === '/settings'
                    ? 'bg-gray-200 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <IconSettings className="h-4 w-4" />
                Settings
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

