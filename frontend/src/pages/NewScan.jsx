import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import api from '../api'

const NGROK = 'https://blockish-candyce-noncongruous.ngrok-free.dev'

function UploadZone({ preview, onFileChange, onRemove }) {
  if (preview) {
    return (
      <div>
        <div
          onClick={() => document.getElementById('fileInput').click()}
          className="border-2 border-dashed border-cyan-300 bg-cyan-50 rounded-xl p-8 text-center cursor-pointer"
        >
          <img src={preview} className="max-h-56 mx-auto rounded-lg shadow-sm" alt="preview" />
        </div>
        <button
          onClick={onRemove}
          className="mt-2 text-sm text-slate-400 hover:text-red-500 transition-colors"
        >
          Remove image
        </button>
        <input id="fileInput" type="file" accept="image/*" hidden onChange={onFileChange} />
      </div>
    )
  }
  return (
    <div>
      <div
        onClick={() => document.getElementById('fileInput').click()}
        className="border-2 border-dashed border-slate-200 hover:border-cyan-300 hover:bg-slate-50 rounded-xl p-8 text-center cursor-pointer transition-all duration-200"
      >
        <div className="text-4xl mb-3 opacity-40">📷</div>
        <p className="text-slate-500 font-medium">Click to upload image</p>
        <p className="text-slate-400 text-sm mt-1">JPG, PNG supported</p>
      </div>
      <input id="fileInput" type="file" accept="image/*" hidden onChange={onFileChange} />
    </div>
  )
}

function MetricBox({ label, value, highlight }) {
  const base = 'rounded-xl p-4 border'
  const style = highlight ? base + ' bg-red-50 border-red-100' : base + ' bg-slate-50 border-slate-100'
  const valStyle = highlight ? 'text-3xl font-bold mt-1 text-red-600' : 'text-3xl font-bold mt-1 text-slate-800'
  return (
    <div className={style}>
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={valStyle}>{value}</p>
    </div>
  )
}

function BiopsyWarning() {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5 flex items-start gap-3">
      <span className="text-red-500 text-xl">⚡</span>
      <div>
        <p className="text-red-700 font-bold text-sm">Biopsy Recommended</p>
        <p className="text-red-600 text-xs mt-0.5">
          Cancer probability exceeds 70% clinical threshold
        </p>
      </div>
    </div>
  )
}

function PDFButton({ scanId }) {
  const url = NGROK + '/api/reports/download/' + scanId
  return (
    <div className="pt-4 border-t border-slate-100">
      <a
        href={url}
        target="_blank"
        rel="noreferrer"
        className="flex items-center justify-center gap-2 w-full bg-slate-800 hover:bg-slate-900 text-white py-3 rounded-xl font-semibold transition-all"
      >
        Download PDF Report
      </a>
      <p className="text-xs text-slate-400 text-center mt-2">
        Professional report with patient info, AI results and heatmap
      </p>
    </div>
  )
}

function ScanResult({ result }) {
  const isCancer = result.prediction === 'cancer'
  const headerClass = isCancer ? 'px-6 py-5 bg-red-500' : 'px-6 py-5 bg-green-500'
  const wrapClass = isCancer
    ? 'rounded-2xl border-2 overflow-hidden border-red-300'
    : 'rounded-2xl border-2 overflow-hidden border-green-300'
  const title = isCancer ? 'Cancer Detected' : 'No Cancer Detected'
  const gradcamUrl = result.gradcam_url
    ? result.gradcam_url.replace('http://localhost:8000', NGROK)
    : ''

  return (
    <div className={wrapClass}>
      <div className={headerClass}>
        <h2 className="text-xl font-bold text-white">{title}</h2>
        <p className="text-white text-sm mt-0.5 opacity-80">{result.message}</p>
      </div>
      <div className="bg-white p-6">
        <div className="grid grid-cols-2 gap-4 mb-5">
          <MetricBox label="Confidence" value={result.confidence + '%'} highlight={false} />
          <MetricBox label="Cancer Probability" value={result.cancer_probability + '%'} highlight={isCancer} />
        </div>
        {result.requires_biopsy && <BiopsyWarning />}
        <div className="mb-5">
          <p className="text-sm font-semibold text-slate-700 mb-2">
            AI Explanation — Grad-CAM Heatmap
          </p>
          <img
            src={gradcamUrl}
            className="rounded-xl w-full border border-slate-100 shadow-sm"
            alt="Grad-CAM heatmap"
          />
          <p className="text-xs text-slate-400 mt-2">
            Red/yellow areas show regions the AI focused on for this prediction
          </p>
        </div>
        <PDFButton scanId={result.scan_id} />
      </div>
    </div>
  )
}

export default function NewScan() {
  const [patients, setPatients] = useState([])
  const [patientId, setPatientId] = useState('')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/patients/').then(r => setPatients(r.data))
  }, [])

  const handleFileChange = e => {
    const f = e.target.files[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
  }

  const handleRemove = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
  }

  const handleUpload = async () => {
    if (!file || !patientId) {
      setError('Please select a patient and upload an image')
      return
    }
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await api.post('/scans/predict?patient_id=' + patientId, form)
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Prediction failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const btnDisabled = loading || !file || !patientId
  const btnClass = btnDisabled
    ? 'w-full bg-cyan-500 opacity-40 cursor-not-allowed text-white py-4 rounded-xl font-bold text-base'
    : 'w-full bg-cyan-500 hover:bg-cyan-600 text-white py-4 rounded-xl font-bold text-base transition-all duration-200'

  return (
    <Layout>
      <div className="p-8 max-w-3xl">

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">New Oral Scan</h1>
          <p className="text-slate-500 mt-1">
            Upload an oral cavity image for AI-powered cancer detection
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 mb-4">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Select Patient
          </label>
          <div className="flex gap-3">
            <select
              value={patientId}
              onChange={e => setPatientId(e.target.value)}
              className="flex-1 border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-400 text-slate-700 bg-white"
            >
              <option value="">Select a patient...</option>
              {patients.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name} · Age {p.age} · {p.gender}
                </option>
              ))}
            </select>
            <button
              onClick={() => navigate('/patients')}
              className="border border-slate-200 text-slate-600 px-4 py-3 rounded-xl hover:bg-slate-50 font-medium text-sm whitespace-nowrap"
            >
              + New Patient
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 mb-4">
          <label className="block text-sm font-semibold text-slate-700 mb-3">
            Oral Image
          </label>
          <UploadZone
            preview={preview}
            onFileChange={handleFileChange}
            onRemove={handleRemove}
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-4 mb-4 text-sm">
            {error}
          </div>
        )}

        <button onClick={handleUpload} disabled={btnDisabled} className={btnClass + ' mb-6'}>
          {loading ? 'Analyzing with AI...' : 'Run AI Analysis'}
        </button>

        {result && <ScanResult result={result} />}

      </div>
    </Layout>
  )
}
