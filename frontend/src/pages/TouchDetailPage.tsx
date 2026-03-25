import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { touches as touchesApi, performances as perfApi } from '../api'
import type { Touch, Performance } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import { useDropzone } from 'react-dropzone'
import { DndContext, closestCenter } from '@dnd-kit/core'
import type { DragEndEvent } from '@dnd-kit/core'
import {
  SortableContext, verticalListSortingStrategy,
  useSortable, arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Trash2, CheckCircle, XCircle, BarChart2, Upload } from 'lucide-react'
import { format } from 'date-fns'

function SortablePerformanceRow({
  perf,
  onDelete,
}: {
  perf: Performance
  onDelete: (id: number) => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: perf.id })
  const style = { transform: CSS.Transform.toString(transform), transition: transition ?? undefined }

  return (
    <div ref={setNodeRef} style={style} className="performance-row">
      <span className="drag-handle" {...attributes} {...listeners}>
        <GripVertical size={16} />
      </span>
      <span className="performance-label">{perf.label}</span>
      <span className="performance-date">{format(new Date(perf.created_at), 'dd MMM yyyy')}</span>
      <button className="btn btn-danger btn-sm" onClick={() => onDelete(perf.id)}>
        <Trash2 size={14} />
      </button>
    </div>
  )
}

function MethodDropzone({ touchId, onUploaded }: { touchId: number; onUploaded: (t: Touch) => void }) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    setUploading(true)
    setError('')
    try {
      const updated = await touchesApi.uploadMethod(touchId, acceptedFiles[0])
      onUploaded(updated)
    } catch {
      setError('Upload failed')
    } finally {
      setUploading(false)
    }
  }, [touchId, onUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/plain': ['.txt'] },
    multiple: false,
  })

  return (
    <div>
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}>
        <input {...getInputProps()} />
        <Upload size={24} />
        {uploading ? (
          <p>Uploading...</p>
        ) : isDragActive ? (
          <p>Drop the method file here...</p>
        ) : (
          <p>Drag & drop a .txt method file, or click to select</p>
        )}
      </div>
      {error && <div className="error-message">{error}</div>}
    </div>
  )
}

function PerformanceDropzone({
  touchId,
  nextOrderIndex,
  onUploaded,
}: {
  touchId: number
  nextOrderIndex: number
  onUploaded: (p: Performance) => void
}) {
  const [label, setLabel] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setFile(acceptedFiles[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'text/plain': ['.csv'] },
    multiple: false,
  })

  const handleUpload = async () => {
    if (!file || !label.trim()) return
    setUploading(true)
    setError('')
    try {
      const perf = await perfApi.create(touchId, label.trim(), file, nextOrderIndex)
      onUploaded(perf)
      setLabel('')
      setFile(null)
    } catch {
      setError('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="perf-upload-form">
      <div className="form-group">
        <label>Label</label>
        <input
          type="text"
          value={label}
          onChange={e => setLabel(e.target.value)}
          placeholder="e.g. Practice 1"
        />
      </div>
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}>
        <input {...getInputProps()} />
        <Upload size={20} />
        {file ? (
          <p>{file.name}</p>
        ) : isDragActive ? (
          <p>Drop CSV file here...</p>
        ) : (
          <p>Drag & drop a CSV timing file, or click to select</p>
        )}
      </div>
      {error && <div className="error-message">{error}</div>}
      <button
        className="btn btn-primary"
        onClick={handleUpload}
        disabled={uploading || !file || !label.trim()}
      >
        {uploading ? 'Uploading...' : 'Add Performance'}
      </button>
    </div>
  )
}

export default function TouchDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const touchId = Number(id)

  const [touch, setTouch] = useState<Touch | null>(null)
  const [perfList, setPerfList] = useState<Performance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [showAddPerf, setShowAddPerf] = useState(false)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const [t, perfs] = await Promise.all([
        touchesApi.get(touchId),
        perfApi.list(touchId),
      ])
      setTouch(t)
      setPerfList(perfs.sort((a, b) => a.order_index - b.order_index))
    } catch {
      setError('Failed to load touch')
    } finally {
      setLoading(false)
    }
  }, [touchId])

  useEffect(() => { load() }, [load])

  const handleSaveEdit = async () => {
    if (!touch) return
    try {
      const updated = await touchesApi.update(touchId, { name: editName, description: editDesc })
      setTouch(updated)
      setEditing(false)
    } catch {
      setError('Failed to update touch')
    }
  }

  const handleDeletePerf = async (perfId: number) => {
    if (!confirm('Delete this performance?')) return
    try {
      await perfApi.delete(touchId, perfId)
      setPerfList(prev => prev.filter(p => p.id !== perfId))
    } catch {
      setError('Failed to delete performance')
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = perfList.findIndex(p => p.id === active.id)
    const newIndex = perfList.findIndex(p => p.id === over.id)
    const newList = arrayMove(perfList, oldIndex, newIndex)
    setPerfList(newList)
    try {
      await perfApi.reorder(touchId, newList.map((p, i) => ({ id: p.id, order_index: i })))
    } catch {
      setError('Failed to reorder performances')
    }
  }

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} onRetry={load} />
  if (!touch) return null

  const canAnalyse = touch.method_file_path && perfList.length > 0

  return (
    <div>
      <div className="page-header">
        {editing ? (
          <div className="edit-inline">
            <input
              type="text"
              value={editName}
              onChange={e => setEditName(e.target.value)}
              className="edit-title-input"
            />
            <button className="btn btn-primary btn-sm" onClick={handleSaveEdit}>Save</button>
            <button className="btn btn-secondary btn-sm" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        ) : (
          <div className="title-row">
            <h1>{touch.name}</h1>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => { setEditing(true); setEditName(touch.name); setEditDesc(touch.description ?? '') }}
            >
              Edit
            </button>
          </div>
        )}
        {canAnalyse && (
          <button className="btn btn-primary" onClick={() => navigate(`/touches/${touchId}/analysis`)}>
            <BarChart2 size={16} /> Analyse
          </button>
        )}
      </div>

      {editing && (
        <div className="form-group">
          <label>Description</label>
          <textarea
            value={editDesc}
            onChange={e => setEditDesc(e.target.value)}
            rows={3}
          />
        </div>
      )}
      {!editing && touch.description && (
        <p className="touch-description">{touch.description}</p>
      )}

      <section className="section">
        <h2>Method File</h2>
        {touch.method_file_path ? (
          <div className="status-badge status-success">
            <CheckCircle size={16} />
            Method uploaded
            {touch.n_bells && ` — ${touch.n_bells} bells`}
            {touch.rounds_rows && `, ${touch.rounds_rows} rounds rows`}
          </div>
        ) : (
          <>
            <div className="status-badge status-warning">
              <XCircle size={16} />
              No method file uploaded
            </div>
            <MethodDropzone touchId={touchId} onUploaded={t => setTouch(t)} />
          </>
        )}
      </section>

      <section className="section">
        <div className="section-header">
          <h2>Performances</h2>
          <button className="btn btn-secondary btn-sm" onClick={() => setShowAddPerf(v => !v)}>
            {showAddPerf ? 'Cancel' : '+ Add Performance'}
          </button>
        </div>

        {showAddPerf && (
          <PerformanceDropzone
            touchId={touchId}
            nextOrderIndex={perfList.length}
            onUploaded={p => {
              setPerfList(prev => [...prev, p])
              setShowAddPerf(false)
            }}
          />
        )}

        {perfList.length === 0 ? (
          <p className="empty-state-small">No performances yet.</p>
        ) : (
          <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={perfList.map(p => p.id)} strategy={verticalListSortingStrategy}>
              <div className="performance-list">
                {perfList.map(perf => (
                  <SortablePerformanceRow key={perf.id} perf={perf} onDelete={handleDeletePerf} />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        )}
      </section>
    </div>
  )
}
