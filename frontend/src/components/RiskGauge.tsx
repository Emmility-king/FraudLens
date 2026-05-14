interface RiskGaugeProps {
  score: number
  label?: string
}

function bandFromScore(score: number): { text: string; className: string } {
  if (score >= 0.75) return { text: 'High', className: 'text-red-400' }
  if (score >= 0.45) return { text: 'Elevated', className: 'text-amber-300' }
  return { text: 'Low', className: 'text-emerald-400' }
}

export function RiskGauge({ score, label = 'Risk score' }: RiskGaugeProps) {
  const pct = Math.round(score * 100)
  const band = bandFromScore(score)
  const angle = 180 * score

  return (
    <div className="flex flex-col items-center gap-2">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{label}</p>
      <div className="relative h-28 w-48">
        <svg viewBox="0 0 120 72" className="h-full w-full" aria-hidden>
          <path
            d="M 12 60 A 48 48 0 0 1 108 60"
            fill="none"
            stroke="#1e293b"
            strokeWidth="10"
            strokeLinecap="round"
          />
          <path
            d="M 12 60 A 48 48 0 0 1 108 60"
            fill="none"
            stroke="url(#gaugeGrad)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${(angle / 180) * 150.8} 150.8`}
          />
          <defs>
            <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22c55e" />
              <stop offset="50%" stopColor="#fbbf24" />
              <stop offset="100%" stopColor="#f87171" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span className="text-2xl font-semibold tabular-nums text-slate-100">{pct}</span>
          <span className={`text-xs font-medium ${band.className}`}>{band.text}</span>
        </div>
      </div>
    </div>
  )
}
