import { useState, useCallback } from 'react'
import { Panel } from '@/components/ui'
import { DPad, SpeedControl, VelocityBars } from '@/components/ui/DPad'
import { publishCmdVel, publishResetOdom } from '@/services/ros'
import { useRobotStore } from '@/stores'

interface LaserData {
  distances: number[]
  safe: boolean
}

export function DriveView() {
  const { x, y, theta, linearVelocity, angularVelocity, mode } = useRobotStore()
  const [speed, setSpeed] = useState(0.5)
  const [maxSpeed] = useState(2.0)
  const [angleUnit, setAngleUnit] = useState<'rad' | 'deg'>('rad')
  const [laserData] = useState<LaserData>({ distances: [0, 0, 0, 0, 0], safe: true })
  const [magneticBits] = useState<boolean[]>(Array(16).fill(false))
  const [deviation] = useState(0)

  const handleMove = useCallback((direction: string) => {
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
  }, [speed])

  const handleStop = useCallback(() => {
    publishCmdVel(0, 0)
  }, [])

  const handleSpeedUp = () => setSpeed(s => Math.min(maxSpeed, s + 0.1))
  const handleSpeedDown = () => setSpeed(s => Math.max(0.1, s - 0.1))

  const displayTheta = angleUnit === 'deg' ? (theta * 180 / Math.PI).toFixed(2) : theta.toFixed(2)

  return (
    <div>
      {/* Position Bar */}
      <div className="pos-bar">
        <div className="pos-card green">
          <div className="pos-label">X Position</div>
          <div className="pos-value">{x.toFixed(2)}</div>
          <div className="pos-unit">meters</div>
        </div>
        <div className="pos-card cyan">
          <div className="pos-label">Y Position</div>
          <div className="pos-value">{y.toFixed(2)}</div>
          <div className="pos-unit">meters</div>
        </div>
        <div className="pos-card heading yellow">
          <div>
            <div className="pos-label">Heading θ</div>
            <div className="pos-value">{displayTheta}</div>
            <div className="pos-unit">{angleUnit === 'deg' ? 'degrees' : 'radians'}</div>
          </div>
          <div className="angle-toggle">
            <button
              className={`angle-btn ${angleUnit === 'rad' ? 'active' : ''}`}
              onClick={() => setAngleUnit('rad')}
            >Rad</button>
            <button
              className={`angle-btn ${angleUnit === 'deg' ? 'active' : ''}`}
              onClick={() => setAngleUnit('deg')}
            >Deg</button>
          </div>
        </div>
        <div className="pos-controls">
          <div className="pos-ctrl-label">Quick Actions</div>
          <div className="ctrl-btn-row">
            <button className="ctrl-btn" onClick={() => publishResetOdom()}>Reset Odom</button>
          </div>
          <div className="ctrl-btn-row">
            <button className="ctrl-btn">Reset Encoder</button>
          </div>
          <div className="ctrl-btn-row">
            <button className="ctrl-btn">Stop Lidar</button>
          </div>
        </div>
      </div>

      {/* Front Laser Sensor */}
      <Panel title="Front Obstacle Laser (CCF-LAS4)" color="red" className="mb-3">
        <div style={{ padding: '14px 16px' }}>
          <div className="laser-channels">
            {laserData.distances.map((dist, i) => (
              <div key={i} className="laser-channel">
                <div className="laser-channel-label">CH {i + 1}{i === 2 ? ' (CENTER)' : ''}</div>
                <div className="laser-channel-value">{dist > 0 ? dist.toFixed(0) : '--'}</div>
                <div className="laser-channel-unit">
                  {['Front-Left 60°', 'Front-Left 30°', 'Front 0°', 'Front-Right 30°', 'Front-Right 60°'][i]}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Panel>

      {/* Magnetic Line Sensor */}
      <Panel title="Magnetic Navigation Sensor (CCF-NS16)" color="cyan" className="mb-3">
        <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* 16-bit magnetic LED strip */}
          <div>
            <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '.65rem', fontWeight: 700, letterSpacing: '.08em', color: '#5E6B78', textTransform: 'uppercase', marginBottom: '8px', textAlign: 'center' }}>
              Sensor Photodiode / Magnetic LED Strip (16-Bit Map)
            </div>
            <div className="magnetic-bits">
              {magneticBits.map((on, i) => (
                <div key={i} className={`magnetic-bit ${on ? 'on' : ''}`}></div>
              ))}
            </div>
          </div>

          {/* Deviation slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'IBM Plex Mono', fontSize: '.6rem', color: '#8794A3', marginBottom: '6px' }}>
              <span>LEFT LIMIT (-100mm)</span>
              <span style={{ fontWeight: 'bold', color: '#5E6B78', letterSpacing: '.05em' }}>CENTER ALIGNMENT</span>
              <span>RIGHT LIMIT (+100mm)</span>
            </div>
            <div className="deviation-bar">
              <div className="deviation-center"></div>
              <div className="deviation-indicator" style={{ left: `${50 + (deviation / 100) * 50}%` }}></div>
            </div>
          </div>
        </div>
      </Panel>

      {/* Drive Grid */}
      <div className="drive-grid">
        {/* Motion Control Panel */}
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

        {/* Right column */}
        <div className="drive-right">
          {/* Trajectory Map */}
          <Panel title="Trajectory Map" color="cyan" collapsible={false}>
            <div className="canvas-wrapper">
              <canvas id="odomCanvas" width={700} height={340}></canvas>
              <div className="canvas-footer">
                <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '.6rem', color: '#5E6B78', letterSpacing: '.06em' }}>
                  ODOMETRY TRAJECTORY
                </div>
                <span className="canvas-scale-chip">GRID 1 m</span>
                <div className="canvas-zoom-btns">
                  <button className="cz-btn">−</button>
                  <button className="cz-btn">⌂</button>
                  <button className="cz-btn">+</button>
                </div>
              </div>
            </div>
          </Panel>

          {/* Telemetry */}
          <Panel title="Telemetry" color="cyan" collapsible={false}>
            <div className="tele-grid">
              <div className="tele-cell">
                <div className="tele-label">Voltage</div>
                <div className="tele-value">0.0 <span style={{ fontSize: '.7rem', opacity: 0.7 }}>V</span></div>
              </div>
              <div className="tele-cell">
                <div className="tele-label">Driver Temp</div>
                <div className="tele-value">0.0 <span style={{ fontSize: '.7rem', opacity: 0.7 }}>°C</span></div>
              </div>
              <div className="tele-cell">
                <div className="tele-label">Current L / R</div>
                <div className="tele-value">0.0 / 0.0 <span style={{ fontSize: '.7rem', opacity: 0.7 }}>A</span></div>
              </div>
              <div className="tele-cell">
                <div className="tele-label">RPM L / R</div>
                <div className="tele-value">0 / 0</div>
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}