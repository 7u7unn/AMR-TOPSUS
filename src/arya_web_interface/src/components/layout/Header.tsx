import { useState, useEffect } from 'react'
import { useConnectionStore, useRobotStore } from '@/stores'

interface HeaderProps {
  onToggleSidebar: () => void
  onOpenSettings: () => void
}

export function Header({ onToggleSidebar, onOpenSettings }: HeaderProps) {
  const { status } = useConnectionStore()
  const { mode } = useRobotStore()
  const [time, setTime] = useState('--:--:--')

  useEffect(() => {
    const updateTime = () => setTime(new Date().toLocaleTimeString('en-US', { hour12: false }))
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  const getStatusClass = () => {
    switch (status) {
      case 'connected': return 'connected'
      case 'error': return 'error'
      default: return ''
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'connected': return 'CONNECTED'
      case 'connecting': return 'CONNECTING...'
      case 'error': return 'ERROR'
      default: return 'CONNECTING...'
    }
  }

  return (
    <header className="hmi-header">
      <button className="hdr-menu" onClick={onToggleSidebar} aria-label="Toggle sidebar">☰</button>

      <div className="hdr-brand">
        <div className="brand-gem">AMR</div>
        <div className="brand-text">
          <strong>YMPI 2.0</strong>
          <small>Industrial HMI Interface</small>
        </div>
      </div>

      <div className="hdr-sep"></div>

      <div className="hdr-sysinfo">
        <span className="si-l">System</span>
        <span className="si-v">ONLINE</span>
      </div>

      <div className="hdr-sep"></div>

      <div className="hdr-sysinfo">
        <span className="si-l">Time</span>
        <span className="si-v">{time}</span>
      </div>

      <div className="hdr-right">
        <div className={`status-badge ${getStatusClass()}`}>{getStatusText()}</div>
        <button className={`mode-btn ${mode === 'auto' ? 'active' : ''}`}>
          {mode.toUpperCase()} MODE
        </button>
        <button className="hdr-icon-btn" onClick={onOpenSettings} title="Settings" aria-label="Open settings">⚙</button>
      </div>
    </header>
  )
}