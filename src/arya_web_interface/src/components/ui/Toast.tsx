import { useEffect, useState } from 'react'

type ToastType = 'info' | 'success' | 'warning' | 'error' | 'busy'

interface Toast {
  id: string
  title: string
  message: string
  type: ToastType
  timestamp: number
}

let toastListeners: ((toasts: Toast[]) => void)[] = []
let toasts: Toast[] = []

export function showToast(title: string, message: string, type: ToastType = 'info') {
  const toast: Toast = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    title,
    message,
    type,
    timestamp: Date.now(),
  }
  toasts = [...toasts, toast].slice(-5) // Keep max 5 toasts
  toastListeners.forEach(listener => listener([...toasts]))

  // Auto remove after 5 seconds
  setTimeout(() => {
    toasts = toasts.filter(t => t.id !== toast.id)
    toastListeners.forEach(listener => listener([...toasts]))
  }, 5000)
}

export function ToastContainer() {
  const [activeToasts, setActiveToasts] = useState<Toast[]>([])

  useEffect(() => {
    const listener = (newToasts: Toast[]) => setActiveToasts([...newToasts])
    toastListeners.push(listener)
    return () => {
      toastListeners = toastListeners.filter(l => l !== listener)
    }
  }, [])

  const getToastClass = (type: ToastType) => {
    switch (type) {
      case 'success': return 'success'
      case 'error': return 'error'
      case 'warning': return 'warning'
      case 'busy': return 'busy'
      default: return ''
    }
  }

  return (
    <div className="toast-container">
      {activeToasts.map(toast => (
        <div key={toast.id} className={`toast ${getToastClass(toast.type)} show`}>
          <div className="toast-header">
            <span className="toast-title">{toast.title}</span>
            <span className="toast-time">{new Date(toast.timestamp).toLocaleTimeString('en-US', { hour12: false })}</span>
          </div>
          <div className="toast-body">{toast.message}</div>
        </div>
      ))}
    </div>
  )
}