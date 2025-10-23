import { Inter } from 'next/font/google'
import './globals.css'
import SidebarLayout from '@/components/SidebarLayout'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Weekly Report Generator',
  description: 'Generate professional weekly reports with data validation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SidebarLayout>
          {children}
        </SidebarLayout>
      </body>
    </html>
  )
}
