import { useState, useEffect } from 'react'

interface StatusBarProps {
  driveStatus: string
  ioStatus: string
  message: string
}

export function StatusBar({ driveStatus, ioStatus, message }: StatusBarProps) {
  const [time, setTime] = useState('--:--:--')

  useEffect(() => {
    const updateTime = () => setTime(new Date().toLocaleTimeString('en-US', { hour12: false }))
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  const getDriveDotClass = () => {
    if (driveStatus === 'RUNNING') return 'ok'
    return 'warn'
  }

  const getIoDotClass = () => {
    if (ioStatus === 'ONLINE') return 'ok'
    return 'err'
  }

  return (
    <div className="hmi-statusbar">
      <div className="sb-item">
        <span className="sb-dot ok"></span>SYS READY
      </div>
      <div className="sb-item">
        <span className={`sb-dot ${getDriveDotClass()}`}></span>
        DRIVE: <span style={{ marginLeft: '4px' }}>{driveStatus}</span>
      </div>
      <div className="sb-item">
        <span className={`sb-dot ${getIoDotClass()}`}></span>
        I/O: <span style={{ marginLeft: '4px' }}>{ioStatus}</span>
      </div>
      <div className="sb-msg">{message}</div>
      <div className="sb-clock">{time}</div>
    </div>
  )
}