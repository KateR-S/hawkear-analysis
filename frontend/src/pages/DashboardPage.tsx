import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { touches as touchesApi } from '../api'
import type { Touch } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import { Plus, Trash2, Check, X } from 'lucide-react'
import { format } from 'date-fns'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [touchList, setTouchList] = useState<Touch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [creating, setCreating] = useState(false)

  const loadTouches = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const data = await touchesApi.list()
      setTouchList(data)
    } catch {
      setError('Failed to load touches')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadTouches() }, [loadTouches])

  const handleCreate = async () => {
    if (!newName.trim()) return
    setCreating(true)
    try {
      const touch = await touchesApi.create(newName.trim(), newDescription.trim())
      setTouchList(prev => [touch, ...prev])
      setShowModal(false)
      setNewName('')
      setNewDescription('')
    } catch {
      setError('Failed to create touch')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this touch?')) return
    try {
      await touchesApi.delete(id)
      setTouchList(prev => prev.filter(t => t.id !== id))
    } catch {
      setError('Failed to delete touch')
    }
  }

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} onRetry={loadTouches} />

  return (
    <div>
      <div className="page-header">
        <h1>My Touches</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={16} /> New Touch
        </button>
      </div>

      {touchList.length === 0 ? (
        <div className="empty-state">
          <p>No touches yet. Create your first touch to get started.</p>
        </div>
      ) : (
        <div className="card-grid">
          {touchList.map(touch => (
            <div
              key={touch.id}
              className="card card-clickable"
              onClick={() => navigate(`/touches/${touch.id}`)}
            >
              <div className="card-header">
                <h3>{touch.name}</h3>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={e => handleDelete(touch.id, e)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
              {touch.description && <p className="card-description">{touch.description}</p>}
              <div className="card-meta">
                <span className="badge">
                  {touch.method_file_path ? (
                    <><Check size={12} className="text-success" /> Method uploaded</>
                  ) : (
                    <><X size={12} className="text-error" /> No method</>
                  )}
                </span>
                {touch.n_bells && <span className="badge">{touch.n_bells} bells</span>}
                <span className="card-date">{format(new Date(touch.created_at), 'dd MMM yyyy')}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>New Touch</h2>
            <div className="form-group">
              <label>Name</label>
              <input
                type="text"
                value={newName}
                onChange={e => setNewName(e.target.value)}
                autoFocus
                placeholder="e.g. Cambridge Surprise Minor"
              />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <textarea
                value={newDescription}
                onChange={e => setNewDescription(e.target.value)}
                rows={3}
                placeholder="Notes about this touch..."
              />
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleCreate} disabled={creating || !newName.trim()}>
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
