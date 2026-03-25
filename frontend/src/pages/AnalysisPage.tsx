import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { performances as perfApi, analysis as analysisApi } from '../api'
import type { Performance, SingleAnalysis, FullAnalysis, BellCharacteristic } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import StrikingChart from '../components/charts/StrikingChart'
import TempoChart from '../components/charts/TempoChart'
import ProgressChart from '../components/charts/ProgressChart'

type TopTab = 'single' | 'progress'
type SubTab = 'rounds' | 'changes' | 'characteristics'

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>()
  const touchId = Number(id)

  const [topTab, setTopTab] = useState<TopTab>('single')
  const [subTab, setSubTab] = useState<SubTab>('rounds')
  const [perfList, setPerfList] = useState<Performance[]>([])
  const [selectedPerfId, setSelectedPerfId] = useState<number | null>(null)
  const [singleAnalysis, setSingleAnalysis] = useState<SingleAnalysis | null>(null)
  const [fullAnalysis, setFullAnalysis] = useState<FullAnalysis | null>(null)
  const [characteristics, setCharacteristics] = useState<Record<string, BellCharacteristic> | null>(null)
  const [loading, setLoading] = useState(true)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadPerfs = async () => {
      try {
        const perfs = await perfApi.list(touchId)
        const sorted = perfs.sort((a, b) => a.order_index - b.order_index)
        setPerfList(sorted)
        if (sorted.length > 0) setSelectedPerfId(sorted[0].id)
      } catch {
        setError('Failed to load performances')
      } finally {
        setLoading(false)
      }
    }
    loadPerfs()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [touchId])

  useEffect(() => {
    if (!selectedPerfId) return
    const loadSingle = async () => {
      setAnalysisLoading(true)
      try {
        const data = await analysisApi.getSingle(touchId, selectedPerfId)
        setSingleAnalysis(data)
      } catch {
        setError('Failed to load analysis')
      } finally {
        setAnalysisLoading(false)
      }
    }
    loadSingle()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [touchId, selectedPerfId])

  useEffect(() => {
    if (topTab !== 'progress') return
    const loadFull = async () => {
      setAnalysisLoading(true)
      try {
        const data = await analysisApi.getFull(touchId)
        setFullAnalysis(data)
      } catch {
        setError('Failed to load full analysis')
      } finally {
        setAnalysisLoading(false)
      }
    }
    if (!fullAnalysis) loadFull()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topTab, touchId])

  useEffect(() => {
    if (subTab !== 'characteristics' || !selectedPerfId) return
    const loadChars = async () => {
      try {
        const data = await analysisApi.getCharacteristics(touchId, selectedPerfId)
        setCharacteristics(data)
      } catch {
        setError('Failed to load characteristics')
      }
    }
    loadChars()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subTab, touchId, selectedPerfId])

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} />

  const nBells = singleAnalysis && singleAnalysis.striking_errors.length > 0
    ? Math.max(...singleAnalysis.striking_errors.flatMap(row => row.map(s => s.bell)))
    : 1

  return (
    <div>
      <h1>Analysis</h1>

      <div className="tabs">
        <button
          className={`tab ${topTab === 'single' ? 'tab-active' : ''}`}
          onClick={() => setTopTab('single')}
        >
          Single Performance
        </button>
        <button
          className={`tab ${topTab === 'progress' ? 'tab-active' : ''}`}
          onClick={() => setTopTab('progress')}
        >
          Progress Over Time
        </button>
      </div>

      {topTab === 'single' && (
        <div>
          <div className="form-group" style={{ maxWidth: 300, marginBottom: '1rem' }}>
            <label>Performance</label>
            <select
              value={selectedPerfId ?? ''}
              onChange={e => setSelectedPerfId(Number(e.target.value))}
            >
              {perfList.map(p => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
          </div>

          <div className="tabs tabs-secondary">
            {(['rounds', 'changes', 'characteristics'] as SubTab[]).map(tab => (
              <button
                key={tab}
                className={`tab ${subTab === tab ? 'tab-active' : ''}`}
                onClick={() => setSubTab(tab)}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {analysisLoading ? (
            <LoadingSpinner />
          ) : singleAnalysis ? (
            <>
              {subTab === 'rounds' && (
                <div>
                  {singleAnalysis.rounds_rows < 2 ? (
                    <div className="info-message">No rounds section detected.</div>
                  ) : (
                    <>
                      <StrikingChart
                        data={singleAnalysis.striking_errors.slice(0, singleAnalysis.rounds_rows)}
                        nBells={nBells}
                        title="Rounds Striking Errors"
                      />
                      <div className="stats-row">
                        <div className="stat-card">
                          <span className="stat-label">Mean Error</span>
                          <span className="stat-value">{singleAnalysis.summary_stats.mean_error.toFixed(1)} ms</span>
                        </div>
                        <div className="stat-card">
                          <span className="stat-label">Std Error</span>
                          <span className="stat-value">{singleAnalysis.summary_stats.std_error.toFixed(1)} ms</span>
                        </div>
                        <div className="stat-card">
                          <span className="stat-label">% Inaudible</span>
                          <span className="stat-value">{singleAnalysis.summary_stats.pct_inaudible.toFixed(1)}%</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}

              {subTab === 'changes' && (
                <div>
                  <StrikingChart
                    data={singleAnalysis.striking_errors}
                    mistakeRows={singleAnalysis.method_mistakes}
                    nBells={nBells}
                    title="Striking Errors (All Changes)"
                  />
                  <TempoChart data={singleAnalysis.tempo_data} title="Tempo" />
                  <h3>Per-Bell Statistics</h3>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Bell</th>
                        <th>Mean Error</th>
                        <th>Std</th>
                        <th>Mean Abs</th>
                        <th>% Inaudible</th>
                        <th>Backstroke</th>
                        <th>Handstroke</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(singleAnalysis.per_bell_stats)
                        .sort(([a], [b]) => Number(a) - Number(b))
                        .map(([bell, stats]) => (
                          <tr key={bell}>
                            <td>{bell}</td>
                            <td>{stats.mean_error.toFixed(1)}</td>
                            <td>{stats.std_error.toFixed(1)}</td>
                            <td>{stats.mean_abs_error.toFixed(1)}</td>
                            <td>{stats.pct_inaudible.toFixed(1)}%</td>
                            <td>{stats.backstroke_mean.toFixed(1)}</td>
                            <td>{stats.handstroke_mean.toFixed(1)}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}

              {subTab === 'characteristics' && (
                <div>
                  {!characteristics ? (
                    <LoadingSpinner />
                  ) : (
                    <div className="card-grid">
                      {Object.entries(characteristics)
                        .sort(([a], [b]) => Number(a) - Number(b))
                        .map(([bell, chars]) => (
                          <div key={bell} className="card">
                            <h3>Bell {bell}</h3>
                            <div className="char-row">
                              <span>Slow Tempo Reaction</span>
                              <span>{chars.slow_tempo_reaction.toFixed(3)}</span>
                            </div>
                            <div className="char-row">
                              <span>Backstroke Tendency</span>
                              <span>{chars.backstroke_tendency.toFixed(1)} ms</span>
                            </div>
                            <div className="char-row">
                              <span>Handstroke Tendency</span>
                              <span>{chars.handstroke_tendency.toFixed(1)} ms</span>
                            </div>
                            <div className="char-row">
                              <span>Low Confidence</span>
                              <span className={chars.low_confidence ? 'text-error' : 'text-success'}>
                                {chars.low_confidence ? 'Yes' : 'No'}
                              </span>
                            </div>
                            <div className="char-row">
                              <span>Influenced by Previous</span>
                              <span>{chars.influenced_by_previous.toFixed(3)}</span>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>
      )}

      {topTab === 'progress' && (
        <div>
          {analysisLoading ? (
            <LoadingSpinner />
          ) : fullAnalysis ? (
            fullAnalysis.performances.length < 2 ? (
              <div className="info-message">
                At least 2 performances are needed to show progress over time.
              </div>
            ) : (
              <ProgressChart performances={fullAnalysis.performances} />
            )
          ) : null}
        </div>
      )}
    </div>
  )
}
