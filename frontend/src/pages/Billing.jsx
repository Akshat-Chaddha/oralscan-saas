import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../api'

const PLANS = [
  { key: 'starter',    name: 'Starter',    price: '₹4,999', scans: 100,   color: 'slate',  best: false },
  { key: 'pro',        name: 'Pro',        price: '₹12,999', scans: 500,  color: 'cyan',   best: true  },
  { key: 'enterprise', name: 'Enterprise', price: '₹29,999', scans: 99999,color: 'purple', best: false },
]

export default function Billing() {
  const [stats, setStats] = useState(null)

  useEffect(() => { api.get('/scans/stats').then(r => setStats(r.data)) }, [])

  const used  = stats?.total_scans ?? 0
  const limit = 100
  const pct   = Math.min((used / limit) * 100, 100)

  return (
    <Layout>
      <div className="p-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Billing & Plan</h1>
          <p className="text-slate-500 mt-1">Manage your subscription and scan usage</p>
        </div>

        {/* Current Usage */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 mb-8">
          <h2 className="font-bold text-slate-800 mb-4">Current Plan — Starter</h2>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-600">Scans used this month</span>
            <span className="text-sm font-bold text-slate-800">{used} / {limit}</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${pct > 80 ? 'bg-red-500' : 'bg-cyan-500'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          {pct > 80 && (
            <p className="text-red-500 text-sm mt-2 font-medium">
              ⚠ You're running low on scans — consider upgrading
            </p>
          )}
        </div>

        {/* Plans */}
        <h2 className="font-bold text-slate-800 mb-4">Available Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PLANS.map(plan => (
            <div key={plan.key}
              className={`bg-white rounded-2xl border-2 shadow-sm p-6 relative ${
                plan.best ? 'border-cyan-400' : 'border-slate-100'
              }`}>
              {plan.best && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-cyan-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                  MOST POPULAR
                </span>
              )}
              <h3 className="font-bold text-slate-800 text-lg">{plan.name}</h3>
              <p className="text-3xl font-bold text-slate-800 mt-2">{plan.price}
                <span className="text-sm font-normal text-slate-400">/mo</span>
              </p>
              <p className="text-slate-500 text-sm mt-1">
                {plan.scans === 99999 ? 'Unlimited scans' : `${plan.scans} scans/month`}
              </p>
              <ul className="mt-4 space-y-2 text-sm text-slate-600">
                <li>✅ AI Cancer Detection</li>
                <li>✅ Grad-CAM Explanations</li>
                <li>✅ PDF Reports</li>
                <li>✅ Patient Management</li>
                {plan.key !== 'starter' && <li>✅ Priority Support</li>}
                {plan.key === 'enterprise' && <li>✅ API Access</li>}
              </ul>
              <button
                onClick={() => alert('Contact sales@oralscan.ai to upgrade')}
                className={`mt-6 w-full py-3 rounded-xl font-semibold transition-all ${
                  plan.best
                    ? 'bg-cyan-500 hover:bg-cyan-600 text-white'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}>
                {plan.key === 'starter' ? 'Current Plan' : 'Upgrade'}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-slate-400 text-sm mt-6">
          To upgrade, contact us at sales@oralscan.ai or WhatsApp +91-XXXXXXXXXX
        </p>
      </div>
    </Layout>
  )
}