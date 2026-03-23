interface Props {
  message: string
  onRetry?: () => void
}

export default function ErrorMessage({ message, onRetry }: Props) {
  return (
    <div className="error-message">
      <span>{message}</span>
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}
