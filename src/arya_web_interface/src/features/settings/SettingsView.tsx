import { useState } from 'react'
import { Modal } from '@/components/ui'
import { useConnectionStore } from '@/stores'

export function SettingsView() {
  const { status, lastError } = useConnectionStore()
  const [wsHost, setWsHost] = useState(window.location.hostname)
  const [wsPort, setWsPort] = useState('8000')
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    localStorage.setItem('hmi-ws-host', wsHost)
    localStorage.setItem('hmi-ws-port', wsPort)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReload = () => {
    window.location.reload()
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '16px', letterSpacing: '.1em', textTransform: 'uppercase' }}>
        System Settings
      </h2>

      <div style={{ maxWidth: '600px' }}>
        {/* Connection Status */}
        <div style={{
          padding: '16px',
          background: status === 'connected' ? 'rgba(46, 125, 50, .10)' : status === 'error' ? 'rgba(198, 40, 40, .10)' : 'rgba(183, 121, 31, .10)',
          border: `1px solid ${status === 'connected' ? '#2E7D32' : status === 'error' ? '#C62828' : '#B7791F'}`,
          borderRadius: '6px',
          marginBottom: '24px'
        }}>
          <div style={{ fontWeight: 700, marginBottom: '8px' }}>Connection Status</div>
          <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '0.85rem' }}>
            <div>Status: <span style={{ color: status === 'connected' ? '#2E7D32' : status === 'error' ? '#C62828' : '#B7791F', fontWeight: 700 }}>
              {status.toUpperCase()}
            </span></div>
            {lastError && <div style={{ color: '#C62828', marginTop: '4px' }}>Error: {lastError}</div>}
          </div>
        </div>

        {/* WebSocket Settings */}
        <div style={{
          padding: '20px',
          background: '#ffffff',
          border: '1px solid #c7d1db',
          borderRadius: '6px',
          marginBottom: '16px'
        }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '16px', letterSpacing: '.1em', textTransform: 'uppercase' }}>
            WebSocket Configuration
          </h3>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label">WebSocket Host</label>
            <input
              className="form-input"
              type="text"
              value={wsHost}
              onChange={(e) => setWsHost(e.target.value)}
              placeholder="Robot IP address"
            />
            <div className="form-info" style={{ marginTop: '4px' }}>
              IP address of the robot running the FastAPI web server.
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label">WebSocket Port</label>
            <input
              className="form-input"
              type="text"
              value={wsPort}
              onChange={(e) => setWsPort(e.target.value)}
              placeholder="8000"
            />
          </div>

          <div className="form-info" style={{ marginBottom: '16px' }}>
            Changes to host/port require page reload to take effect.
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="modal-btn confirm" onClick={handleSave}>
              Save Settings
            </button>
            <button className="modal-btn" onClick={handleReload}>
              Reload Page
            </button>
          </div>

          {saved && (
            <div style={{ marginTop: '12px', color: '#2E7D32', fontFamily: 'IBM Plex Mono', fontSize: '0.8rem' }}>
              ✓ Settings saved successfully
            </div>
          )}
        </div>

        {/* System Info */}
        <div style={{
          padding: '20px',
          background: '#ffffff',
          border: '1px solid #c7d1db',
          borderRadius: '6px',
          marginBottom: '16px'
        }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '16px', letterSpacing: '.1em', textTransform: 'uppercase' }}>
            System Information
          </h3>

          <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '0.8rem', display: 'grid', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#5E6B78' }}>Firmware Version</span>
              <span style={{ fontWeight: 700 }}>YMPI-FW-2.0.1</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#5E6B78' }}>HMI Version</span>
              <span style={{ fontWeight: 700 }}>2.0.0</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#5E6B78' }}>Map Folder</span>
              <span style={{ fontWeight: 700 }}>amr_bringup_headless/maps</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#5E6B78' }}>Log Folder</span>
              <span style={{ fontWeight: 700 }}>~/.arya_amr/logs</span>
            </div>
          </div>
        </div>

        {/* About */}
        <div style={{
          padding: '20px',
          background: '#ffffff',
          border: '1px solid #c7d1db',
          borderRadius: '6px'
        }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px', letterSpacing: '.1em', textTransform: 'uppercase' }}>
            About
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#5E6B78', lineHeight: 1.6 }}>
            AMR YMPI 2.0 Web HMI — Industrial Human Machine Interface for autonomous mobile robot control.
            Built with React, TypeScript, and Zustand.
          </p>
        </div>
      </div>
    </div>
  )
}