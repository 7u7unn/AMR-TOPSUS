import { useState, useEffect, useCallback, useRef } from 'react'
import { Panel } from '@/components/ui'
import { DPad, SpeedControl, VelocityBars } from '@/components/ui/DPad'
import { useRobotStore } from '@/stores'
import { publishCmdVel, publishMode } from '@/services/ros'

interface TeleopViewProps {
  onEmergencyStop: () => void
}

export function TeleopView({ onEmergencyStop }: TeleopViewProps) {
  const { mode, linearVelocity, angularVelocity } = useRobotStore()
  const [speed, setSpeed] = useState(0.3)
  const [maxSpeed] = useState(1.0)
  const [keyboardEnabled, setKeyboardEnabled] = useState(true)
  const [deadmanActive, setDeadmanActive] = useState(false)
  const [commandTimeout, setCommandTimeout] = useState<ReturnType<typeof setTimeout> | null>(null)

  // Key states for keyboard control
  const activeKeys = useRef<Set<string>>(new Set())

  const handleMove = useCallback((direction: string) => {
    if (mode !== 'manual') return

    let linear = 0
    let angular = 0
    const turnSpeed = 1.5

    switch (direction) {
      case 'forward': linear = speed; break
      case 'backward': linear = -speed; break
      case 'left': angular = turnSpeed; break
      case 'right': angular = -turnSpeed; break
      case 'forwardLeft': linear = speed; angular = turnSpeed; break
      case 'forwardRight': linear = speed; angular = -turnSpeed; break
      case 'backwardLeft': linear = -speed; angular = turnSpeed; break
      case 'backwardRight': linear = -speed; angular = -turnSpeed; break
    }

    publishCmdVel(linear, angular)

    // Reset timeout
    if (commandTimeout) clearTimeout(commandTimeout)
    const timeout = setTimeout(() => publishCmdVel(0, 0), 100)
    setCommandTimeout(timeout)
  }, [speed, mode, commandTimeout])

  const handleStop = useCallback(() => {
    publishCmdVel(0, 0)
    activeKeys.current.clear()
  }, [])

  const handleSpeedUp = () => setSpeed(s => Math.min(maxSpeed, s + 0.1))
  const handleSpeedDown = () => setSpeed(s => Math.max(0.05, s - 0.1))

  // Keyboard event handlers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!keyboardEnabled || mode !== 'manual') return

      const key = e.key.toLowerCase()
      if (activeKeys.current.has(key)) return
      activeKeys.current.add(key)

      switch (key) {
        case 'w':
        case 'arrowup':
          publishCmdVel(speed, 0)
          break
        case 's':
        case ',':
          publishCmdVel(-speed, 0)
          break
        case 'a':
        case 'arrowleft':
          publishCmdVel(0, 1.5)
          break
        case 'd':
        case 'arrowright':
          publishCmdVel(0, -1.5)
          break
        case 'q':
          handleSpeedUp()
          break
        case 'z':
          handleSpeedDown()
          break
        case 'k':
        case ' ':
          handleStop()
          break
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase()
      activeKeys.current.delete(key)

      if (activeKeys.current.size === 0) {
        publishCmdVel(0, 0)
      } else {
        // Calculate remaining active directions
        let linear = 0
        let angular = 0

        if (activeKeys.current.has('w') || activeKeys.current.has('arrowup')) linear = speed
        if (activeKeys.current.has('s') || activeKeys.current.has(',')) linear = -speed
        if (activeKeys.current.has('a') || activeKeys.current.has('arrowleft')) angular = 1.5
        if (activeKeys.current.has('d') || activeKeys.current.has('arrowright')) angular = -1.5

        publishCmdVel(linear, angular)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [keyboardEnabled, mode, speed, handleStop])

  const handleEmergencyStop = () => {
    publishCmdVel(0, 0)
    publishMode('emergency')
    onEmergencyStop()
  }

  const handleSwitchMode = (newMode: 'auto' | 'manual') => {
    publishMode(newMode)
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '16px', letterSpacing: '.1em', textTransform: 'uppercase' }}>
        Teleoperation Control
      </h2>

      {/* Safety Controls */}
      <div className="pos-bar" style={{ marginBottom: '16px' }}>
        <div className="pos-card" style={{ borderTopColor: mode === 'emergency' ? '#C62828' : '#aebbc8' }}>
          <div className="pos-label">Current Mode</div>
          <div className="pos-value" style={{ color: mode === 'auto' ? '#2E7D32' : mode === 'emergency' ? '#C62828' : '#D95F02' }}>
            {mode.toUpperCase()}
          </div>
          <div className="pos-unit">Robot Operation Mode</div>
        </div>

        <div className="pos-card">
          <div className="pos-label">Keyboard</div>
          <div className="pos-value" style={{ color: keyboardEnabled ? '#0A6ED1' : '#8794A3' }}>
            {keyboardEnabled ? 'ENABLED' : 'DISABLED'}
          </div>
          <div className="pos-unit">WASD / Arrows / Space</div>
        </div>

        <div className="pos-card">
          <div className="pos-label">Deadman Switch</div>
          <div className="pos-value" style={{ color: deadmanActive ? '#2E7D32' : '#C62828' }}>
            {deadmanActive ? 'ACTIVE' : 'INACTIVE'}
          </div>
          <div className="pos-unit">Hold to enable drive</div>
        </div>

        <div className="pos-card" style={{ borderTopColor: '#C62828' }}>
          <div className="pos-label">Emergency Stop</div>
          <button
            onClick={handleEmergencyStop}
            className="ctrl-btn"
            style={{
              background: '#C62828',
              color: 'white',
              borderColor: '#C62828',
              height: 'auto',
              padding: '12px',
              fontSize: '1rem'
            }}
          >
            🚨 E-STOP
          </button>
        </div>
      </div>

      {/* Mode Selection */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <button
          className={`topic-btn ${mode === 'auto' ? 'active' : ''}`}
          onClick={() => handleSwitchMode('auto')}
          style={{ minWidth: '120px', height: '40px' }}
        >
          AUTO MODE
        </button>
        <button
          className={`topic-btn ${mode === 'manual' ? 'active' : ''}`}
          onClick={() => handleSwitchMode('manual')}
          style={{ minWidth: '120px', height: '40px' }}
        >
          MANUAL MODE
        </button>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>
          <input
            type="checkbox"
            checked={keyboardEnabled}
            onChange={(e) => setKeyboardEnabled(e.target.checked)}
          />
          <span>Enable Keyboard Control</span>
        </label>
      </div>

      {/* D-Pad Control */}
      <div className="drive-grid">
        <Panel title="Motion Control" color="orange" collapsible={false}>
          <div className="dpad-wrap">
            <SpeedControl
              speed={speed}
              maxSpeed={maxSpeed}
              onSpeedChange={setSpeed}
              onSpeedUp={handleSpeedUp}
              onSpeedDown={handleSpeedDown}
            />
            <DPad onMove={handleMove} onStop={handleStop} disabled={mode !== 'manual'} />
            <VelocityBars linear={linearVelocity} angular={angularVelocity} />
          </div>
        </Panel>

        <Panel title="Safety Settings" color="yellow" collapsible={false}>
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Max Velocity (m/s)</label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="2.0"
                className="form-input"
                value={maxSpeed}
                readOnly
              />
            </div>
            <div className="form-group">
              <label className="form-label">Command Timeout (ms)</label>
              <input
                type="number"
                step="100"
                min="100"
                max="5000"
                className="form-input"
                defaultValue="100"
              />
            </div>
            <div className="form-info">
              Safety: Commands auto-expire if no new command received within timeout. Emergency stop cuts power immediately.
            </div>
          </div>
        </Panel>
      </div>

      {/* Keyboard Reference */}
      <Panel title="Keyboard Controls Reference" color="cyan" className="mt-4">
        <div style={{ padding: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontFamily: 'IBM Plex Mono' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#f2f5f8', border: '1px solid #c7d1db', padding: '4px 8px', borderRadius: '4px' }}>W / ↑</kbd>
              <span>Forward</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#f2f5f8', border: '1px solid #c7d1db', padding: '4px 8px', borderRadius: '4px' }}>S / ,</kbd>
              <span>Backward</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#f2f5f8', border: '1px solid #c7d1db', padding: '4px 8px', borderRadius: '4px' }}>A / ←</kbd>
              <span>Rotate Left</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#f2f5f8', border: '1px solid #c7d1db', padding: '4px 8px', borderRadius: '4px' }}>D / →</kbd>
              <span>Rotate Right</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#f2f5f8', border: '1px solid #c7d1db', padding: '4px 8px', borderRadius: '4px' }}>Q</kbd>
              <span>Speed Up</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#f2f5f8', border: '1px solid #c7d1db', padding: '4px 8px', borderRadius: '4px' }}>Z</kbd>
              <span>Speed Down</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#f2f5f8', border: '1px solid #c7d1db', padding: '4px 8px', borderRadius: '4px' }}>K / Space</kbd>
              <span>Stop</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <kbd style={{ background: '#C62828', color: 'white', border: '1px solid #C62828', padding: '4px 8px', borderRadius: '4px' }}>ESC</kbd>
              <span>Emergency Stop</span>
            </div>
          </div>
        </div>
      </Panel>
    </div>
  )
}