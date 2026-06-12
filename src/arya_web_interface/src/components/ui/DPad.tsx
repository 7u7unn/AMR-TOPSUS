interface DPadProps {
  onMove: (direction: 'forward' | 'backward' | 'left' | 'right' | 'forwardLeft' | 'forwardRight' | 'backwardLeft' | 'backwardRight') => void
  onStop: () => void
  disabled?: boolean
}

export function DPad({ onMove, onStop, disabled }: DPadProps) {
  const handleMouseDown = (direction: string) => {
    if (disabled) return
    if (direction === 'stop') {
      onStop()
    } else {
      onMove(direction as 'forward' | 'backward' | 'left' | 'right' | 'forwardLeft' | 'forwardRight' | 'backwardLeft' | 'backwardRight')
    }
  }

  return (
    <div className="dpad-grid">
      <div className="dpad-row">
        <button className="btn" onMouseDown={() => handleMouseDown('forwardLeft')} disabled={disabled} title="Forward-Left (U)">↖</button>
        <button className="btn" onMouseDown={() => handleMouseDown('forward')} disabled={disabled} title="Forward (I)">▲</button>
        <button className="btn" onMouseDown={() => handleMouseDown('forwardRight')} disabled={disabled} title="Forward-Right (O)">↗</button>
      </div>
      <div className="dpad-row">
        <button className="btn" onMouseDown={() => handleMouseDown('left')} disabled={disabled} title="Rotate Left (J)">↺</button>
        <button className="btn btn-stop" onMouseDown={() => handleMouseDown('stop')} disabled={disabled} title="STOP (K)">■</button>
        <button className="btn" onMouseDown={() => handleMouseDown('right')} disabled={disabled} title="Rotate Right (L)">↻</button>
      </div>
      <div className="dpad-row">
        <button className="btn" onMouseDown={() => handleMouseDown('backwardLeft')} disabled={disabled} title="Backward-Left (M)">↙</button>
        <button className="btn" onMouseDown={() => handleMouseDown('backward')} disabled={disabled} title="Backward (,)">▼</button>
        <button className="btn" onMouseDown={() => handleMouseDown('backwardRight')} disabled={disabled} title="Backward-Right (.)">↘</button>
      </div>
    </div>
  )
}

interface SpeedControlProps {
  speed: number
  maxSpeed: number
  onSpeedChange: (speed: number) => void
  onSpeedUp: () => void
  onSpeedDown: () => void
}

export function SpeedControl({ speed, maxSpeed, onSpeedChange, onSpeedUp, onSpeedDown }: SpeedControlProps) {
  return (
    <>
      <div className="slider-row">
        <label>Max Speed</label>
        <input
          type="range"
          min={0.1}
          max={maxSpeed}
          step={0.05}
          value={speed}
          onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
        />
        <span className="srval">{speed.toFixed(2)}</span>
        <span style={{ color: '#8794A3', fontSize: '.58rem' }}>m/s</span>
      </div>
      <div className="speed-row">
        <button className="btn btn-speed" onClick={onSpeedDown} title="Speed Down (Z)">−</button>
        <div className="speed-badge">
          <small>Command Speed</small>
          <span className="sv">{speed.toFixed(2)}</span>
          <span className="su">m/s</span>
        </div>
        <button className="btn btn-speed" onClick={onSpeedUp} title="Speed Up (Q)">＋</button>
      </div>
    </>
  )
}

interface VelocityBarsProps {
  linear: number
  angular: number
  maxLinear?: number
  maxAngular?: number
}

export function VelocityBars({ linear, angular, maxLinear = 2, maxAngular = 2 }: VelocityBarsProps) {
  const linearPercent = Math.min(100, Math.abs(linear) / maxLinear * 100)
  const angularPercent = Math.min(100, Math.abs(angular) / maxAngular * 100)

  return (
    <div className="bars-row">
      <div className="bar-col">
        <div className="bar-track">
          <div className="bar-fill" style={{ width: `${linearPercent}%` }}></div>
        </div>
        <div className="bar-label">
          <span>Linear</span>
          <span>{linear.toFixed(2)}</span>
        </div>
      </div>
      <div className="bar-col">
        <div className="bar-track">
          <div className="bar-fill" style={{ width: `${angularPercent}%` }}></div>
        </div>
        <div className="bar-label">
          <span>Angular</span>
          <span>{angular.toFixed(2)}</span>
        </div>
      </div>
    </div>
  )
}