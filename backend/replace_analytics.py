import re

with open('d:/Myprojects/finance_APP/finora/frontend/src/app/(dashboard)/investments/page.tsx', 'r') as f:
    content = f.read()

# Find the start of ANALYTICS SECTION and the start of INVESTMENT TABLE
start_marker = "{/* ANALYTICS SECTION */}"
end_marker = "{/* INVESTMENT TABLE */}"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    before = content[:start_idx]
    after = content[end_idx:]
    
    new_analytics = '''{/* ANALYTICS SECTION */}
      {isAnalyticsLoading ? (
        <div className="flex justify-center items-center h-40">
          <p className="text-on-surface-variant animate-pulse">Loading Analytics Dashboard...</p>
        </div>
      ) : (
      <div className="grid grid-cols-12 gap-6">
        {/* Portfolio Growth */}
        <div className="col-span-12 lg:col-span-8 editorial-card p-6 rounded-xl relative overflow-hidden flex flex-col">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-1">Portfolio Growth</p>
              <h3 className="text-lg font-bold text-on-surface">Wealth Appreciation</h3>
            </div>
          </div>
          <div className="flex-1 w-full relative min-h-[220px]">
            {analytics?.growth_history && analytics.growth_history.length > 0 ? (
              <svg className="w-full h-full absolute inset-0" preserveAspectRatio="none" viewBox="0 0 800 200">
                <defs>
                  <linearGradient id="gradient" x1="0%" x2="0%" y1="0%" y2="100%">
                    <stop offset="0%" style={{ stopColor: 'rgba(139, 94, 60, 0.2)' }} />
                    <stop offset="100%" style={{ stopColor: 'rgba(139, 94, 60, 0)' }} />
                  </linearGradient>
                </defs>
                <path d="M0,180 C50,170 100,165 150,140 S250,150 300,120 S400,110 450,80 S550,90 600,60 S700,50 800,20 L800,200 L0,200 Z" fill="url(#gradient)"></path>
                <path d="M0,180 C50,170 100,165 150,140 S250,150 300,120 S400,110 450,80 S550,90 600,60 S700,50 800,20" fill="none" stroke="#8B5E3C" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"></path>
              </svg>
            ) : (
              <div className="flex items-center justify-center h-full text-sm text-on-surface-variant">
                No growth history available yet.
              </div>
            )}
            <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[10px] text-on-surface-variant px-2 pt-4 font-bold uppercase tracking-wider">
              {analytics?.growth_history?.slice(0, 7).map((snap: any, i: number) => (
                <span key={i}>{new Date(snap.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}</span>
              ))}
            </div>
          </div>
        </div>
        
        {/* Asset Allocation */}
        <div className="col-span-12 lg:col-span-4 editorial-card p-6 rounded-xl">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-4">Asset Allocation</p>
          <div className="flex items-center justify-center py-4">
            <div className="relative h-40 w-40">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" fill="transparent" r="15.9" stroke="#E7E2DB" strokeWidth="4"></circle>
                {analytics?.allocation?.distribution?.map((item: any, idx: number) => {
                  let previousPct = analytics.allocation.distribution.slice(0, idx).reduce((sum: number, curr: any) => sum + curr.pct, 0);
                  let dashArray = ${item.pct} ;
                  let dashOffset = 100 - previousPct + 25; // +25 for visual offset adjustment
                  return (
                    <circle key={item.type} cx="18" cy="18" fill="transparent" r="15.9" stroke={item.color} strokeDasharray={dashArray} strokeDashoffset={dashOffset} strokeWidth="4"></circle>
                  )
                })}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-[10px] text-on-surface-variant uppercase tracking-wider font-bold mb-0.5">Total</p>
                <p className="font-bold text-primary text-sm">Diversified</p>
              </div>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {analytics?.allocation?.distribution?.map((item: any) => (
              <div key={item.type} className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: item.color}}></div> <span className="font-medium text-on-surface">{item.label}</span></div>
                <span className="font-bold text-on-surface">{item.pct}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Performance vs Benchmark */}
        <div className="col-span-12 lg:col-span-8 editorial-card p-6 rounded-xl">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-8">Performance Comparison (1Y Return %)</p>
          <div className="flex items-end gap-6 h-40 px-4">
            <div className="flex-1 flex flex-col items-center gap-3 h-full justify-end">
              <div className="w-full bg-primary/10 rounded-t-lg relative group border-b-2 border-primary overflow-hidden" style={{height: ${Math.min(100, Math.max(10, analytics?.summary?.total_gain_pct || 0))}%}}>
                <div className="absolute bottom-0 left-0 right-0 bg-primary rounded-t-lg transition-all duration-700 opacity-90" style={{ height: '100%' }}></div>
              </div>
              <span className="text-[10px] uppercase font-bold text-on-surface tracking-wider">Portfolio ({analytics?.summary?.total_gain_pct?.toFixed(2)}%)</span>
            </div>
            
            {analytics?.benchmarks?.map((bench: any) => (
              <div key={bench.name} className="flex-1 flex flex-col items-center gap-3 h-full justify-end">
                <div className="w-full bg-surface-variant rounded-t-lg relative border-b-2 border-outline-variant overflow-hidden" style={{height: ${Math.min(100, Math.max(10, bench.return_pct))}%}}>
                  <div className="absolute bottom-0 left-0 right-0 bg-secondary rounded-t-lg opacity-50 h-full"></div>
                </div>
                <span className="text-[10px] uppercase font-bold text-on-surface-variant tracking-wider">{bench.name} ({bench.return_pct}%)</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Risk Distribution */}
        <div className="col-span-12 lg:col-span-4 editorial-card p-6 rounded-xl flex flex-col">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-4">Risk Profile</p>
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="w-32 h-32 relative">
              <svg className="w-full h-full -rotate-180" viewBox="0 0 36 36">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#E7E2DB" strokeDasharray="50, 100" strokeWidth="3"></path>
                {analytics?.risk_profile && (
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#8B5E3C" strokeDasharray={${(analytics.risk_profile.overall_score / 5) * 50}, 100} strokeWidth="4"></path>
                )}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center mt-2">
                <span className="material-symbols-outlined text-primary text-[32px]">balance</span>
              </div>
            </div>
            <div className="text-center mt-2">
              <p className="text-lg font-bold text-on-surface">{analytics?.risk_profile?.profile || 'Unknown'}</p>
              <p className="text-[11px] text-on-surface-variant mt-1.5 leading-relaxed font-medium">{analytics?.risk_profile?.explanation}</p>
            </div>
          </div>
        </div>
      </div>
      )}

      '''
    
    with open('d:/Myprojects/finance_APP/finora/frontend/src/app/(dashboard)/investments/page.tsx', 'w') as f:
        f.write(before + new_analytics + after)
        
    print("Successfully replaced analytics section.")
else:
    print("Could not find markers.")
