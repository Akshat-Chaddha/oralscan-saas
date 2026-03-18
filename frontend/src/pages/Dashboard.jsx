import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import api from '../api'

function StatCard({ label, value, icon, color, sub }) {
  const colors = {
    cyan:   'bg-cyan-50   border-cyan-100   text-cyan-600',
    red:    'bg-red-50    border-red-100    text-red-600',
    green:  'bg-green-50  border-green-100  text-green-600',
    purple: 'bg-purple-50 border-purple-100 text-purple-600',
  }
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 rounded-xl border flex items-center justify-center text-xl ${colors[color]}`}>
          {icon}
        </div>
      </div>
      <p className="text-3xl font-bold text-slate-800 mb-1">{value}</p>
      <p className="text-slate-500 text-sm font-medium">{label}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [stats,  setStats]  = useState(null)
  const [recent, setRecent] = useState([])
  const navigate            = useNavigate()

  useEffect(() => {
    api.get('/scans/stats').then(r  => setStats(r.data))
    api.get('/scans/recent').then(r => setRecent(r.data))
  }, [])

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-slate-500 mt-1">Welcome back, {localStorage.getItem('name')}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Scans"      value={stats?.total_scans    ?? '—'} icon="🔬" color="cyan"   />
          <StatCard label="Cancer Detected"  value={stats?.cancer         ?? '—'} icon="⚠️" color="red"    />
          <StatCard label="Clear Results"    value={stats?.non_cancer     ?? '—'} icon="✅" color="green"  />
          <StatCard label="Total Patients"   value={stats?.total_patients ?? '—'} icon="👥" color="purple" />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div onClick={() => navigate('/scan')}
            className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-2xl p-6 cursor-pointer hover:shadow-lg hover:scale-[1.01] transition-all duration-200 text-white">
            <div className="text-3xl mb-3">🔬</div>
            <h2 className="text-xl font-bold">Run New Scan</h2>
            <p className="text-cyan-100 text-sm mt-1">Upload oral image for instant AI analysis</p>
          </div>
          <div onClick={() => navigate('/patients')}
            className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm cursor-pointer hover:shadow-md hover:scale-[1.01] transition-all duration-200">
            <div className="text-3xl mb-3">👥</div>
            <h2 className="text-xl font-bold text-slate-800">Manage Patients</h2>
            <p className="text-slate-400 text-sm mt-1">Add and view patient records</p>
          </div>
        </div>

        {/* Recent Scans */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-bold text-slate-800">Recent Scans</h2>
            <button onClick={() => navigate('/reports')}
              className="text-cyan-600 text-sm font-medium hover:underline">View all →</button>
          </div>
          {recent.length === 0
            ? <p className="text-center text-slate-400 py-12">No scans yet — run your first scan!</p>
            : <div className="divide-y divide-slate-50">
                {recent.map(s => (
                  <div key={s.scan_id} className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50 transition-colors">
                    <img src={s.gradcam_url} className="w-12 h-12 rounded-lg object-cover border border-slate-100" alt="" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                          s.prediction === 'cancer'
                            ? 'bg-red-100 text-red-600'
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {s.prediction === 'cancer' ? '⚠ Cancer' : '✓ Clear'}
                        </span>
                        <span className="text-xs text-slate-400">{s.date}</span>
                      </div>
                      <p className="text-sm text-slate-600 mt-0.5">
                        Confidence: <span className="font-semibold">{(s.confidence * 100).toFixed(1)}%</span>
                        &nbsp;· Cancer prob: <span className="font-semibold text-red-500">{(s.cancer_prob * 100).toFixed(1)}%</span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
          }
        </div>
      </div>
    </Layout>
  )
}