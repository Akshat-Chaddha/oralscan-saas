import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Patients() {
  const [patients, setPatients] = useState([])
  const [form, setForm]         = useState({ name:'', age:'', gender:'male', phone:'' })
  const [loading, setLoading]   = useState(false)
  const [showForm, setShowForm] = useState(false)
  const navigate                = useNavigate()

  const fetchPatients = () => api.get('/patients/').then(r => setPatients(r.data))

  useEffect(() => { fetchPatients() }, [])

  const addPatient = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/patients/', { ...form, age: parseInt(form.age) })
      setForm({ name:'', age:'', gender:'male', phone:'' })
      setShowForm(false)
      fetchPatients()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/')} className="text-blue-600 hover:underline">← Back</button>
          <span className="text-xl font-bold text-blue-800">👥 Patients</span>
        </div>
        <button onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium">
          + Add Patient
        </button>
      </nav>

      <div className="max-w-4xl mx-auto p-8">
        {/* Add Patient Form */}
        {showForm && (
          <div className="bg-white rounded-2xl shadow p-6 mb-6">
            <h2 className="text-lg font-bold mb-4">New Patient</h2>
            <form onSubmit={addPatient} className="grid grid-cols-2 gap-4">
              <input required placeholder="Full Name" value={form.name}
                onChange={e => setForm({...form, name: e.target.value})}
                className="border rounded-lg px-4 py-2 col-span-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <input type="number" placeholder="Age" value={form.age}
                onChange={e => setForm({...form, age: e.target.value})}
                className="border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <select value={form.gender} onChange={e => setForm({...form, gender: e.target.value})}
                className="border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
              <input placeholder="Phone Number" value={form.phone}
                onChange={e => setForm({...form, phone: e.target.value})}
                className="border rounded-lg px-4 py-2 col-span-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <button type="submit" disabled={loading}
                className="col-span-2 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50">
                {loading ? 'Saving...' : 'Save Patient'}
              </button>
            </form>
          </div>
        )}

        {/* Patient List */}
        <div className="bg-white rounded-2xl shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                {['Name','Age','Gender','Phone','Action'].map(h => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {patients.length === 0
                ? <tr><td colSpan={5} className="text-center py-12 text-gray-400">No patients yet — add your first patient</td></tr>
                : patients.map(p => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium">{p.name}</td>
                    <td className="px-6 py-4 text-gray-500">{p.age}</td>
                    <td className="px-6 py-4 text-gray-500 capitalize">{p.gender}</td>
                    <td className="px-6 py-4 text-gray-500">{p.phone}</td>
                    <td className="px-6 py-4">
                      <button onClick={() => navigate('/scan')}
                        className="bg-blue-50 text-blue-600 px-3 py-1 rounded-lg text-sm hover:bg-blue-100 font-medium">
                        New Scan
                      </button>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}