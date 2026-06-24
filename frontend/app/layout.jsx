import './globals.css'
import Sidebar from '@/components/layout/Sidebar'

export const metadata = {
  title: 'AI Knowledge Coach',
  description: 'Language learning with knowledge network management',
}

export default function RootLayout({ children }) {
  return (
    <html lang="zh">
      <body>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
