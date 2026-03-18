import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../api'

const NGROK = 'https://blockish-candyce-noncongruous.ngrok-free.dev'

function PDFLink({ url }) {
  const finalUrl = url.replace('http://localhost:8000', NGROK)
  return (
    <a
      href={finalUrl}
      target="_blank"
      rel="noreferrer"
      className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-xl text-sm font-medium text-center"
    >
      PDF
    </a>
  )
}

function ImageLink({ url }) {
  const finalUrl = url.replace('http://localhost:8000', NGROK)
  return (
    <a
      href={finalUrl}
      target="_blank"
      rel="noreferrer"
      className="border border-slate-200 text-slate-600 hover:bg-slate-50 px-4 py-2 rounded-xl text-sm font-medium text-center"
    >
      Image
    </a>
  )
}

function FilterBtn({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={active
        ? 'px-4 py-2 rounded-xl text-sm font-semibold bg-cyan-500 text-white'
        : 'px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
      }
    >
      {label}
    </button>
  )
}

function ScanCard({ s }) {
  const isCancer = s.prediction === 'cancer'
  const badgeClass = isCancer
    ? 'text-xs font-bold px-2 py-1 rounded-full bg-red-100 text-red-600'
    : 'text-xs font-bold px-2 py-1 rounded-full bg-green-100 text-green-700'
  const probClass = isCancer ? 'font-bold text-red-500' : 'font-bold text-green-600'
  const pdfUrl = NGROK + '/api/reports/download/' + s.scan_id

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex items-center gap-5 hover:shadow-md transition-shadow">
      <img
        src={s.gradcam_url.replace('http://localhost:8000', NGROK)}
        className="w-20 h-20 rounded-xl object-cover border border-slate-100 flex-shrink-0"
        alt="scan"
        onError={e => { e.currentTarget.style.display = 'none' }}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className={badgeClass}>
            {isCancer ? 'Cancer Detected' : 'Clear'}
          </span>
          <span className="text-xs text-slate-400">{s.date}</span>
        </div>
        <div className="flex gap-6">
          <div>
            <p className="text-xs text-slate-400">Confidence</p>
            <p className="font-bold text-slate-800">
              {(s.confidence * 100).toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Cancer Prob.</p>
            <p className={probClass}>
              {(s.cancer_prob * 100).toFixed(1)}%
            </p>
          </div>
          <div className="hidden md:block">
            <p className="text-xs text-slate-400">Scan ID</p>
            <p className="font-mono text-xs text-slate-500">
              {s.scan_id.slice(0, 16)}...
            </p>
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-2 flex-shrink-0">
        <PDFLink url={pdfUrl} />
        <ImageLink url={s.image_url} />
      </div>
    </div>
  )
}

export default function Reports() {
  const [scans, setScans] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/scans/recent')
      .then(r => { setScans(r.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const cancerCount = scans.filter(s => s.prediction === 'cancer').length
  const nonCancerCount = scans.filter(s => s.prediction === 'non_cancer').length

  let filtered = scans
  if (filter === 'cancer') filtered = scans.filter(s => s.prediction === 'cancer')
  if (filter === 'non_cancer') filtered = scans.filter(s => s.prediction === 'non_cancer')

  return (
    <Layout>
      <div className="p-8">

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Scan Reports</h1>
          <p className="text-slate-500 mt-1">All AI scan results for your hospital</p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Total Scans</p>
            <p className="text-3xl font-bold text-slate-800 mt-1">{scans.length}</p>
          </div>
          <div className="bg-white rounded-2xl border border-red-100 shadow-sm p-5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Cancer Detected</p>
            <p className="text-3xl font-bold text-red-600 mt-1">{cancerCount}</p>
          </div>
          <div className="bg-white rounded-2xl border border-green-100 shadow-sm p-5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Clear Results</p>
            <p className="text-3xl font-bold text-green-600 mt-1">{nonCancerCount}</p>
          </div>
        </div>

        <div className="flex gap-2 mb-6">
          <FilterBtn label={'All (' + scans.length + ')'} active={filter === 'all'} onClick={() => setFilter('all')} />
          <FilterBtn label={'Cancer (' + cancerCount + ')'} active={filter === 'cancer'} onClick={() => setFilter('cancer')} />
          <FilterBtn label={'Clear (' + nonCancerCount + ')'} active={filter === 'non_cancer'} onClick={() => setFilter('non_cancer')} />
        </div>

        {loading && (
          <div className="text-center py-16 text-slate-400">
            <p>Loading scans...</p>
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-100 text-center py-16 text-slate-400">
            <div className="text-4xl mb-3">🔬</div>
            <p className="font-medium">No scans found</p>
            <p className="text-sm mt-1">Run your first scan to see results here</p>
          </div>
        )}

        {!loading && filtered.length > 0 && (
          <div className="space-y-3">
            {filtered.map(s => (
              <ScanCard key={s.scan_id} s={s} />
            ))}
          </div>
        )}

      </div>
    </Layout>
  )
}
