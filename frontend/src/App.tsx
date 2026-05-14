import { useCallback, useRef, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { RiskGauge } from './components/RiskGauge'
import { mockFlags, riskHistogram, type FlaggedRow } from './data/mockFlags'

function formatMoney(n: number) {
  return n.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })
}

function bandBadge(band: FlaggedRow['band']) {
  const map = {
    high: 'bg-red-500/15 text-red-300 ring-1 ring-red-500/40',
    medium: 'bg-amber-500/15 text-amber-200 ring-1 ring-amber-500/35',
    low: 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/35',
  }
  return map[band]
}

export default function App() {
  const [selected, setSelected] = useState<FlaggedRow | null>(mockFlags[0] ?? null)
  const [uploadHover, setUploadHover] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [predicting, setPredicting] = useState(false)
  const [predictResult, setPredictResult] = useState<any | null>(null)
  const [predictError, setPredictError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const API_BASE = (import.meta.env.VITE_API_BASE as string) ?? 'http://localhost:8000'

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setUploadHover(false)
    // Wired to FastAPI batch upload in a later phase
    const files = e.dataTransfer.files
    if (files.length) {
      void handleFiles(files)
    }
  }, [])

  async function handleFiles(files: FileList | null) {
    setUploadResult(null)
    setUploadError(null)
    if (!files || files.length === 0) return
    const file = files[0]
    const allowed = ['.csv', '.xlsx', '.xls']
    if (!allowed.some((s) => file.name.toLowerCase().endsWith(s))) {
      setUploadError('Please upload a CSV or Excel file.')
      return
    }
    try {
      setUploading(true)
      const fd = new FormData()
      fd.append('file', file, file.name)
      const res = await fetch(`${API_BASE}/api/v1/`, { method: 'GET' })
      // quick health check - ignore result, proceed to upload
      const r = await fetch(`${API_BASE}/api/v1/datasets/`, { method: 'POST', body: fd })
      if (!r.ok) {
        const t = await r.text()
        throw new Error(t || r.statusText)
      }
      const body = await r.json()
      setUploadResult(body)
    } catch (err: any) {
      setUploadError(err?.message ?? String(err))
    } finally {
      setUploading(false)
    }
  }

  async function runPredict(datasetId: string) {
    setPredictResult(null)
    setPredictError(null)
    setPredicting(true)
    try {
      const r = await fetch(`${API_BASE}/api/v1/predict/${datasetId}`, { method: 'POST' })
      if (!r.ok) {
        const t = await r.text()
        throw new Error(t || r.statusText)
      }
      const body = await r.json()
      setPredictResult(body)
    } catch (err: any) {
      setPredictError(err?.message ?? String(err))
    } finally {
      setPredicting(false)
    }
  }

  const flaggedRevenue = mockFlags.filter((r) => r.band !== 'low').reduce((s, r) => s + r.amount, 0)
  const openCases = mockFlags.filter((r) => r.band === 'high').length

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-400/90">
              Fine-Guard AI
            </p>
            <h1 className="text-lg font-semibold text-slate-50">Fraud monitoring</h1>
            <p className="text-sm text-slate-400">
              School build — UI shell; SQLite + FastAPI wiring comes next.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" aria-hidden />
            Demo data · no backend yet
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        <section className="grid gap-4 sm:grid-cols-3">
          <article className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Flagged exposure</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-50">{formatMoney(flaggedRevenue)}</p>
            <p className="mt-1 text-xs text-slate-500">Medium + high bands (sample)</p>
          </article>
          <article className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Open high-risk</p>
            <p className="mt-2 text-2xl font-semibold tabular-nums text-red-300">{openCases}</p>
            <p className="mt-1 text-xs text-slate-500">Needs investigator review</p>
          </article>
          <article className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Ingestion</p>
            <p className="mt-2 text-2xl font-semibold text-slate-50">CSV / XLSX</p>
            <p className="mt-1 text-xs text-slate-500">Batch upload (below) → SQLite via API</p>
          </article>
        </section>

        <div className="grid gap-6 lg:grid-cols-5">
          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 lg:col-span-2">
            <h2 className="text-sm font-semibold text-slate-200">Risk score distribution</h2>
            <p className="mb-3 text-xs text-slate-500">Population histogram (illustrative)</p>
            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskHistogram} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="range" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: '#475569' }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} name="Transactions" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 lg:col-span-3">
            <h2 className="text-sm font-semibold text-slate-200">Flagged transactions</h2>
            <p className="mb-3 text-xs text-slate-500">Dense table — click a row for investigation panel</p>
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full min-w-[520px] text-left text-sm">
                <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-3 py-2 font-medium">ID</th>
                    <th className="px-3 py-2 font-medium">Time (UTC)</th>
                    <th className="px-3 py-2 font-medium">Amount</th>
                    <th className="px-3 py-2 font-medium">Merchant</th>
                    <th className="px-3 py-2 font-medium">Score</th>
                    <th className="px-3 py-2 font-medium">Band</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 bg-slate-950/50">
                  {mockFlags.map((row) => (
                    <tr
                      key={row.id}
                      className={
                        selected?.id === row.id
                          ? 'cursor-pointer bg-sky-950/40 hover:bg-sky-950/50'
                          : 'cursor-pointer hover:bg-slate-900/80'
                      }
                      onClick={() => setSelected(row)}
                    >
                      <td className="whitespace-nowrap px-3 py-2 font-mono text-xs text-sky-300">{row.id}</td>
                      <td className="whitespace-nowrap px-3 py-2 text-slate-400">{row.occurredAt.slice(0, 19).replace('T', ' ')}</td>
                      <td className="whitespace-nowrap px-3 py-2 tabular-nums text-slate-200">{formatMoney(row.amount)}</td>
                      <td className="max-w-[180px] truncate px-3 py-2 text-slate-300">{row.merchant}</td>
                      <td className="whitespace-nowrap px-3 py-2 tabular-nums text-slate-200">{row.riskScore.toFixed(2)}</td>
                      <td className="px-3 py-2">
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${bandBadge(row.band)}`}>
                          {row.band}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <section
          className={`rounded-xl border border-dashed px-6 py-10 text-center transition-colors ${
            uploadHover ? 'border-sky-500/60 bg-sky-950/20' : 'border-slate-600 bg-slate-900/30'
          }`}
          onDragOver={(e) => {
            e.preventDefault()
            setUploadHover(true)
          }}
          onDragLeave={() => setUploadHover(false)}
          onDrop={onDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => void handleFiles(e.target.files)}
          />
          <p className="text-sm font-medium text-slate-200">Batch upload</p>
          <p className="mt-1 text-xs text-slate-500">Drag and drop CSV or Excel here</p>
          <div className="mt-4 flex items-center justify-center gap-2">
            <button
              className="rounded bg-sky-600 px-3 py-1 text-sm font-medium text-white hover:bg-sky-500"
              onClick={() => fileInputRef.current?.click()}
            >
              Select file
            </button>
            <span className="text-xs text-slate-400">or drop a file onto this area</span>
          </div>
          <div className="mt-3">
            {uploading && <p className="text-xs text-slate-400">Uploading…</p>}
            {uploadResult && (
              <div className="mx-auto mt-2 max-w-md rounded border border-slate-800 bg-slate-950/60 p-3 text-left text-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <div><strong className="text-slate-200">Uploaded:</strong> <span className="text-slate-400">{uploadResult.filename}</span></div>
                    <div><strong className="text-slate-200">Rows:</strong> <span className="text-slate-400">{uploadResult.row_count}</span></div>
                    <div><strong className="text-slate-200">ID:</strong> <span className="font-mono text-xs text-sky-300">{uploadResult.dataset_id}</span></div>
                  </div>
                  <div>
                    <button
                      className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium text-white hover:bg-emerald-500"
                      onClick={() => void runPredict(uploadResult.dataset_id)}
                      disabled={predicting}
                    >
                      {predicting ? 'Predicting…' : 'Run prediction'}
                    </button>
                  </div>
                </div>
                {uploadResult.warnings?.length > 0 && (
                  <div className="mt-2 text-xs text-amber-300">Warnings: {uploadResult.warnings.join('; ')}</div>
                )}

                {predictError && <div className="mt-2 text-xs text-red-400">Predict error: {predictError}</div>}

                {predictResult && (
                  <div className="mt-3 text-sm">
                    <div className="text-xs text-slate-400">Preview scores (first {predictResult.preview?.length ?? 0} rows)</div>
                    <ul className="mt-2 max-h-40 overflow-y-auto text-xs">
                      {predictResult.preview?.map((p: any) => (
                        <li key={p.transaction_id} className="flex justify-between border-b border-slate-800 py-1">
                          <span className="font-mono text-sky-300 truncate max-w-[200px]">{p.transaction_id}</span>
                          <span className="ml-2 tabular-nums text-slate-200">{p.score.toFixed(4)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {uploadError && <div className="mt-2 text-xs text-red-400">Error: {uploadError}</div>}
          </div>
        </section>

        {selected && (
          <section className="grid gap-6 rounded-xl border border-slate-800 bg-slate-900/40 p-6 lg:grid-cols-2">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Investigation</h2>
              <p className="mt-1 font-mono text-xs text-sky-300">{selected.id}</p>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between gap-4 border-b border-slate-800 py-2">
                  <dt className="text-slate-500">Amount</dt>
                  <dd className="tabular-nums text-slate-100">{formatMoney(selected.amount)}</dd>
                </div>
                <div className="flex justify-between gap-4 border-b border-slate-800 py-2">
                  <dt className="text-slate-500">Channel</dt>
                  <dd className="text-slate-200">{selected.channel}</dd>
                </div>
                <div className="flex justify-between gap-4 border-b border-slate-800 py-2">
                  <dt className="text-slate-500">Merchant</dt>
                  <dd className="text-right text-slate-200">{selected.merchant}</dd>
                </div>
              </dl>
            </div>
            <div className="flex flex-col items-center justify-center gap-4 border-t border-slate-800 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
              <RiskGauge score={selected.riskScore} />
              <div className="w-full max-w-md">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Explainability (preview)</p>
                <ul className="space-y-2 text-sm">
                  {selected.xaiHints.map((h) => (
                    <li
                      key={h.label}
                      className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2"
                    >
                      <span className="font-medium text-slate-200">{h.label}</span>
                      <span className="mt-0.5 block text-xs text-slate-500">{h.detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
