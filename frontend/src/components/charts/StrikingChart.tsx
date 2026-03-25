import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine, ReferenceArea, ResponsiveContainer
} from 'recharts'
import type { StrikeError } from '../../types'
import { BELL_COLORS } from '../../constants'

interface Props {
  data: StrikeError[][]
  mistakeRows?: number[]
  nBells: number
  title?: string
}

export default function StrikingChart({ data, mistakeRows, nBells, title }: Props) {
  const chartData = data.map((row, rowIndex) => {
    const point: Record<string, number> = { rowIndex }
    row.forEach(strike => {
      point[`bell_${strike.bell}`] = strike.error_ms
    })
    return point
  })

  const bells = Array.from({ length: nBells }, (_, i) => i + 1)

  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="rowIndex" label={{ value: 'Row', position: 'insideBottom', offset: -5 }} />
          <YAxis domain={[-200, 200]} label={{ value: 'Error (ms)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <ReferenceArea y1={-50} y2={50} fill="#fffde7" fillOpacity={0.5} />
          {mistakeRows?.map(row => (
            <ReferenceLine key={row} x={row} stroke="#999" strokeDasharray="4 4" />
          ))}
          {bells.map((bell, i) => (
            <Line
              key={bell}
              type="monotone"
              dataKey={`bell_${bell}`}
              stroke={BELL_COLORS[i % BELL_COLORS.length]}
              dot={false}
              name={`Bell ${bell}`}
              connectNulls={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
