import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts'
import type { TempoPoint } from '../../types'

interface Props {
  data: TempoPoint[]
  title?: string
}

export default function TempoChart({ data, title }: Props) {
  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="row_index" label={{ value: 'Row', position: 'insideBottom', offset: -5 }} />
          <YAxis label={{ value: 'Interval (ms)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Line type="monotone" dataKey="interval_ms" stroke="#4363d8" dot={false} name="Interval (ms)" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
