export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen" style={{ background: '#fff8f5' }}>
      {children}
    </div>
  )
}
