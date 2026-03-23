import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts'
import type { PerformanceTrend } from '../../types'

interface Props {
  performances: PerformanceTrend[]
}

export default function ProgressChart({ performances }: Props) {
  const data = performances.map(p => ({
    label: p.label,
    mean_abs_error: p.summary_stats.mean_abs_error,
    pct_inaudible: p.summary_stats.pct_inaudible,
  }))

  return (
    <div>
      <div className="chart-container">
        <h3 className="chart-title">Mean Absolute Error Over Time</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" angle={-30} textAnchor="end" />
            <YAxis label={{ value: 'MAE (ms)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Line type="monotone" dataKey="mean_abs_error" stroke="#e94560" dot={true} name="Mean Abs Error" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="chart-container">
        <h3 className="chart-title">% Inaudible Strikes Over Time</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" angle={-30} textAnchor="end" />
            <YAxis label={{ value: '% Inaudible', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Bar dataKey="pct_inaudible" fill="#3cb44b" name="% Inaudible" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
