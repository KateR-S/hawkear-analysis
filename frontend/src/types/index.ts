export interface User {
  id: number
  username: string
  email: string
}

export interface Touch {
  id: number
  user_id: number
  name: string
  description: string | null
  method_file_path: string | null
  n_bells: number | null
  rounds_rows: number | null
  created_at: string
}

export interface Performance {
  id: number
  touch_id: number
  label: string
  timing_file_path: string | null
  order_index: number
  created_at: string
}

export interface StrikeError {
  bell: number
  actual: number
  ideal: number
  error_ms: number
  is_inaudible: boolean
}

export interface SummaryStats {
  mean_error: number
  std_error: number
  mean_abs_error: number
  pct_inaudible: number
}

export interface BellStats {
  mean_error: number
  std_error: number
  mean_abs_error: number
  backstroke_mean: number
  handstroke_mean: number
  pct_inaudible: number
}

export interface TempoPoint {
  row_index: number
  center_time_ms: number
  interval_ms: number
}

export interface SingleAnalysis {
  striking_errors: StrikeError[][]
  rounds_rows: number
  method_mistakes: number[]
  summary_stats: SummaryStats
  per_bell_stats: Record<string, BellStats>
  tempo_data: TempoPoint[]
}

export interface PerformanceTrend {
  label: string
  summary_stats: SummaryStats
  per_bell_stats: Record<string, BellStats>
  tempo_data: TempoPoint[]
}

export interface FullAnalysis {
  performances: PerformanceTrend[]
  trend: Record<string, unknown>
}

export interface BellCharacteristic {
  slow_tempo_reaction: number
  backstroke_tendency: number
  handstroke_tendency: number
  low_confidence: boolean
  influenced_by_previous: number
}
