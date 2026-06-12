import { useState, useRef, useEffect, useCallback } from 'react'
import { Panel } from '@/components/ui'
import { useRobotStore, useLaunchStore, useMapStore, useMissionStore } from '@/stores'
import { publishGoalPose, publishInitialPose, publishLaunchStart, publishLaunchStop, publishSaveMap, publishLoadMap } from '@/services/ros'

interface Station {
  id: string
  name: string
  x: number
  y: number
  theta: number
  wait: number
}

interface GoalStatus {
  state: 'idle' | 'running' | 'success' | 'error'
  title: string
  message: string
}

export function NavigationView() {
  const { x, y, theta, amclX, amclY, amclTheta, amclAvailable } = useRobotStore()
  const { launchStates } = useLaunchStore()
  const { availableMaps, selectedMapName, keepoutZones } = useMapStore()
  const { stations, status } = useMissionStore()
  const [mode, setMode] = useState<'idle' | 'running' | 'success' | 'error'>('idle')
  const [goalStatus, setGoalStatus] = useState<GoalStatus>({ state: 'idle', title: 'Nav2 Goal', message: 'Belum ada goal dari web.' })
  const [displayFeaturesOpen, setDisplayFeaturesOpen] = useState(false)
  const [editStations, setEditStations] = useState(false)
  const [editRestrictions, setEditRestrictions] = useState(false)
  const [displayFeatures, setDisplayFeatures] = useState({
    showMap: true,
    showRobot: true,
    showFootprint: true,
    showLocalCostmap: true,
    showPath: true,
    showGlobalCostmap: false,
    showLidar: true,
  })

  // Form states
  const [initX, setInitX] = useState('')
  const [initY, setInitY] = useState('')
  const [initYaw, setInitYaw] = useState('')
  const [goalX, setGoalX] = useState('')
  const [goalY, setGoalY] = useState('')
  const [goalYaw, setGoalYaw] = useState('')
  const [stationName, setStationName] = useState('')
  const [stationX, setStationX] = useState('')
  const [stationY, setStationY] = useState('')
  const [stationYaw, setStationYaw] = useState('')
  const [stationWait, setStationWait] = useState('0')

  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Launch configs
  const launchConfigs = [
    { id: 'amir_hdl', name: 'Hardware', alias: 'amir_hdl' },
    { id: 'local_hdl', name: 'Localization', alias: 'local_hdl' },
    { id: 'nav_hdl', name: 'Nav2', alias: 'nav_hdl' },
    { id: 'mapping', name: 'Mapping', alias: 'mapping' },
    { id: 'record_path', name: 'Record Path', alias: 'record_path' },
  ]

  const getLaunchState = (id: string) => {
    return launchStates.find(l => l.name === id)?.running || false
  }

  const handleApplyInitialPose = () => {
    const xVal = parseFloat(initX) || 0
    const yVal = parseFloat(initY) || 0
    const yawVal = (parseFloat(initYaw) || 0) * Math.PI / 180
    publishInitialPose(xVal, yVal, yawVal)
  }

  const handleApplyGoal = () => {
    const xVal = parseFloat(goalX) || 0
    const yVal = parseFloat(goalY) || 0
    const yawVal = (parseFloat(goalYaw) || 0) * Math.PI / 180
    publishGoalPose(xVal, yVal, yawVal)
  }

  const handleToggleLaunch = (id: string) => {
    const isRunning = getLaunchState(id)
    if (isRunning) {
      publishLaunchStop(id)
    } else {
      publishLaunchStart(id)
    }
  }

  const handleToggleDisplayFeature = (key: keyof typeof displayFeatures) => {
    setDisplayFeatures(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const getGoalStatusClass = () => {
    switch (goalStatus.state) {
      case 'running': return 'running'
      case 'success': return 'success'
      case 'error': return 'error'
      default: return 'warn'
    }
  }

  return (
    <div className="nav-grid">
      {/* Navigation Map */}
      <Panel
        id="p-nav-map"
        title="Navigation Map"
        color="cyan"
        headerRight={
          <div className="nav-map-header-actions">
            <span className="selected-map-pill">{selectedMapName || 'No map selected'}</span>
            <button className="panel-action-btn">Choose Map</button>
          </div>
        }
      >
        <div className="nav-map-wrap">
          <canvas ref={canvasRef} width={800} height={400} style={{ background: '#f7f9fb' }}></canvas>
          <div className="canvas-footer">
            <div style={{ fontFamily: 'IBM Plex Mono', fontSize: '.6rem', color: '#5E6B78', letterSpacing: '.06em' }}>
              2D MAP NAVIGATION
            </div>
            <div className="canvas-zoom-btns">
              <button className="cz-btn wide active">AUTO CENTER</button>
              <button className="cz-btn">−</button>
              <button className="cz-btn">⌂</button>
              <button className="cz-btn">+</button>
            </div>
          </div>
        </div>
      </Panel>

      {/* Pose & Stations */}
      <Panel id="p-nav-pose-stations" title="Pose & Stations" color="cyan">
        <div className="nav-controls-body">
          <div className={`nav-status-bar ${status === 'running' ? 'running' : status === 'success' ? 'success' : status === 'error' ? 'error' : 'idle'}`}>
            <span className="nav-status-label">Robot Status:</span>
            <span className="nav-status-value">{status.toUpperCase()}</span>
          </div>

          <div className="pose-sections-row">
            {/* Initial Pose */}
            <div className="pose-section initial">
              <div className="pose-section-title">
                <span>Set Init Pose</span>
                <span className="pose-tag">Init</span>
              </div>
              <div className="goal-pose-inputs">
                <div className="goal-field">
                  <label>X (m)</label>
                  <input type="number" step="0.1" className="form-input" value={initX} onChange={e => setInitX(e.target.value)} />
                </div>
                <div className="goal-field">
                  <label>Y (m)</label>
                  <input type="number" step="0.1" className="form-input" value={initY} onChange={e => setInitY(e.target.value)} />
                </div>
                <div className="goal-field">
                  <label>θ (deg)</label>
                  <input type="number" step="1" className="form-input" value={initYaw} onChange={e => setInitYaw(e.target.value)} />
                </div>
              </div>
              <div className="pose-actions">
                <button className="topic-btn" onClick={handleApplyInitialPose}>Apply Initial</button>
                <button className="topic-btn pose-map-btn-initial">Set Init Pose</button>
              </div>
            </div>

            {/* Goal Pose */}
            <div className="pose-section goal">
              <div className="pose-section-title">
                <span>Set Goal Pose</span>
                <span className="pose-tag">Goal</span>
              </div>
              <div className="goal-pose-inputs">
                <div className="goal-field">
                  <label>X (m)</label>
                  <input type="number" step="0.1" className="form-input" value={goalX} onChange={e => setGoalX(e.target.value)} />
                </div>
                <div className="goal-field">
                  <label>Y (m)</label>
                  <input type="number" step="0.1" className="form-input" value={goalY} onChange={e => setGoalY(e.target.value)} />
                </div>
                <div className="goal-field">
                  <label>θ (deg)</label>
                  <input type="number" step="1" className="form-input" value={goalYaw} onChange={e => setGoalYaw(e.target.value)} />
                </div>
              </div>
              <div className="pose-actions">
                <button className="topic-btn" onClick={handleApplyGoal}>Apply Goal</button>
                <button className="topic-btn pose-map-btn-goal">Set Goal Pose</button>
              </div>
            </div>
          </div>

          {/* Station Registry */}
          <div className="nav-section">
            <div className="nav-section-header">
              <span className="nav-section-title">Station Registry</span>
              <button
                className={`btn-edit-toggle ${editStations ? 'active' : ''}`}
                onClick={() => setEditStations(!editStations)}
              >
                {editStations ? 'Done' : 'Edit'}
              </button>
            </div>

            {editStations && (
              <div className="edit-tools-stations" style={{ display: 'block' }}>
                <div className="station-input-grid">
                  <div className="goal-field">
                    <label>Name</label>
                    <input type="text" className="form-input" value={stationName} onChange={e => setStationName(e.target.value)} placeholder="Station A" />
                  </div>
                  <div className="goal-field">
                    <label>X (m)</label>
                    <input type="number" step="0.1" className="form-input" value={stationX} onChange={e => setStationX(e.target.value)} />
                  </div>
                  <div className="goal-field">
                    <label>Y (m)</label>
                    <input type="number" step="0.1" className="form-input" value={stationY} onChange={e => setStationY(e.target.value)} />
                  </div>
                  <div className="goal-field">
                    <label>Theta</label>
                    <input type="number" step="1" className="form-input" value={stationYaw} onChange={e => setStationYaw(e.target.value)} />
                  </div>
                  <div className="goal-field">
                    <label>Wait</label>
                    <input type="number" step="1" min="0" className="form-input" value={stationWait} onChange={e => setStationWait(e.target.value)} />
                  </div>
                </div>
                <div className="station-toolbar">
                  <button className="topic-btn">Pick On Map</button>
                  <button className="topic-btn">Add Station</button>
                  <button className="topic-btn">Save Stations</button>
                </div>
              </div>
            )}

            <div className="station-list">
              {stations.length === 0 && (
                <div className="empty-note">No stations configured. Click Edit to add stations.</div>
              )}
              {stations.map(station => (
                <div key={station.id} className="station-row">
                  <div>
                    <strong>{station.name}</strong>
                    <span>X: {station.x.toFixed(2)} Y: {station.y.toFixed(2)} θ: {station.theta.toFixed(0)}° Wait: {station.wait}s</span>
                  </div>
                  <div className="row-actions">
                    <button className="mini-action-btn">Go</button>
                    <button className="mini-action-btn danger">Del</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Panel>

      {/* Navigation Controls */}
      <Panel id="p-nav-controls" title="Navigation Controls" color="green">
        <div className="nav-controls-body">
          {/* Launch Control */}
          <div className="nav-section">
            <div className="nav-section-title">ROS Launch Control</div>
            <div className="launch-grid">
              {launchConfigs.map(config => (
                <div key={config.id} className="launch-tile">
                  <div className="launch-top">
                    <div className="launch-title">
                      <strong>{config.name}</strong>
                      <span>alias: {config.alias}</span>
                    </div>
                    <span className={`launch-state ${getLaunchState(config.id) ? 'running' : ''}`}>
                      {getLaunchState(config.id) ? 'RUNNING' : 'STOPPED'}
                    </span>
                  </div>
                  <button
                    className={`topic-btn launch-btn ${getLaunchState(config.id) ? 'running' : ''}`}
                    onClick={() => handleToggleLaunch(config.id)}
                  >
                    {getLaunchState(config.id) ? 'Stop' : 'Start'} {config.name}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Mapping Save Panel */}
          <div className="mapping-save-panel">
            <div className="mapping-save-row">
              <div className="mapping-save-title">
                <strong>Save Mapping Result</strong>
                <span>Target: ~/arya_ws/src/amr_bringup_headless/maps</span>
              </div>
              <button className="topic-btn">Save Map</button>
            </div>
          </div>

          {/* Display Features */}
          <div className={`nav-section display-features-section ${displayFeaturesOpen ? '' : 'collapsed'}`}>
            <button
              type="button"
              className="display-features-toggle-btn"
              onClick={() => setDisplayFeaturesOpen(!displayFeaturesOpen)}
            >
              Display Features <span>{displayFeaturesOpen ? '▾' : '▸'}</span>
            </button>
            {displayFeaturesOpen && (
              <div className="nav-checkbox-grid">
                <label className="nav-check-label">
                  <input type="checkbox" checked={displayFeatures.showMap} onChange={() => handleToggleDisplayFeature('showMap')} />
                  <span className="chk-box"></span>Map (Auto-sync)
                </label>
                <label className="nav-check-label">
                  <input type="checkbox" checked={displayFeatures.showRobot} onChange={() => handleToggleDisplayFeature('showRobot')} />
                  <span className="chk-box"></span>Robot Triangle
                </label>
                <label className="nav-check-label">
                  <input type="checkbox" checked={displayFeatures.showFootprint} onChange={() => handleToggleDisplayFeature('showFootprint')} />
                  <span className="chk-box"></span>Robot Polygon
                </label>
                <label className="nav-check-label">
                  <input type="checkbox" checked={displayFeatures.showLocalCostmap} onChange={() => handleToggleDisplayFeature('showLocalCostmap')} />
                  <span className="chk-box"></span>Local Costmap
                </label>
                <label className="nav-check-label">
                  <input type="checkbox" checked={displayFeatures.showPath} onChange={() => handleToggleDisplayFeature('showPath')} />
                  <span className="chk-box"></span>Path Plan
                </label>
                <label className="nav-check-label">
                  <input type="checkbox" checked={displayFeatures.showGlobalCostmap} onChange={() => handleToggleDisplayFeature('showGlobalCostmap')} />
                  <span className="chk-box"></span>Global Costmap
                </label>
                <label className="nav-check-label">
                  <input type="checkbox" checked={displayFeatures.showLidar} onChange={() => handleToggleDisplayFeature('showLidar')} />
                  <span className="chk-box"></span>Lidar Scans
                </label>
              </div>
            )}
          </div>

          {/* Log History */}
          <div className="nav-section">
            <div className="nav-section-title">Navigation Log History</div>
            <div className="nav-controls-log-stream">
              <div className="nav-log-empty">Belum ada log navigation.</div>
            </div>
          </div>
        </div>
      </Panel>

      {/* Restrictions & Missions */}
      <Panel id="p-nav-zones" title="Restrictions & Missions" color="orange">
        <div className="nav-controls-body">
          {/* Restriction Areas */}
          <div className="nav-section">
            <div className="nav-section-header">
              <span className="nav-section-title">Restriction Areas</span>
              <button
                className={`btn-edit-toggle ${editRestrictions ? 'active' : ''}`}
                onClick={() => setEditRestrictions(!editRestrictions)}
              >
                {editRestrictions ? 'Done' : 'Edit'}
              </button>
            </div>

            {editRestrictions && (
              <div className="edit-tools-restrictions" style={{ display: 'block' }}>
                <div className="annotation-toolbar">
                  <button className="topic-btn">Draw Restriction</button>
                  <button className="topic-btn">Save Restrictions</button>
                  <button className="topic-btn stop">Cancel Draw</button>
                </div>
              </div>
            )}

            <div className="annotation-list">
              {keepoutZones.length === 0 && (
                <div className="empty-note">No restriction areas defined.</div>
              )}
              {keepoutZones.map(zone => (
                <div key={zone.id} className="annotation-row">
                  <div>
                    <strong>{zone.name}</strong>
                    <span>{zone.points.length} points</span>
                  </div>
                  <button className="mini-action-btn danger">Del</button>
                </div>
              ))}
            </div>
          </div>

          {/* Mission Mode */}
          <div className="nav-section">
            <div className="nav-section-title">Mission Mode</div>
            <div className="mission-mode-row">
              <button className="mission-mode-btn active">Single</button>
              <button className="mission-mode-btn">Queued</button>
            </div>
            <div className="mission-queue-list"></div>
            <div className="mission-toolbar">
              <button className="topic-btn">Start Queue</button>
              <button className="topic-btn stop">Cancel Queue</button>
              <button className="topic-btn">Clear Queue</button>
            </div>
          </div>
        </div>
      </Panel>

      {/* Navigation Log */}
      <Panel id="p-nav-log" title="Navigation Log" color="cyan">
        <div className="nav-log-body">
          <div className="nav-log-status-grid">
            <div className="nav-log-card">
              <span className="nav-log-card-label">Launch</span>
              <div className="nav-log-hint">
                Launch berjalan sebagai background process terpisah. Log tersimpan di ~/.arya_amr/logs.
              </div>
            </div>
            <div className="nav-log-card">
              <span className="nav-log-card-label">Save Map</span>
              <div className="nav-log-hint">
                Siap menyimpan map SLAM Toolbox.
              </div>
            </div>
            <div className="nav-log-card">
              <span className="nav-log-card-label">Nav2 Goal</span>
              <div className={`nav-goal-status ${getGoalStatusClass()}`}>
                <div className="nav-goal-dot"></div>
                <div className="nav-goal-copy">
                  <strong>{goalStatus.title}</strong>
                  <span>{goalStatus.message}</span>
                </div>
                <span className="nav-goal-pill">{goalStatus.state.toUpperCase()}</span>
              </div>
            </div>
            <div className="nav-log-card">
              <span className="nav-log-card-label">Restriction</span>
              <div className="nav-log-hint">
                Pilih map lalu gambar rectangle di canvas.
              </div>
            </div>
            <div className="nav-log-card">
              <span className="nav-log-card-label">Mission</span>
              <div className="nav-log-hint">
                Single mission siap.
              </div>
            </div>
          </div>
          <div className="nav-log-stream-wrap">
            <span className="nav-log-stream-title">Activity Log</span>
            <div className="nav-log-stream">
              <div className="nav-log-empty">Belum ada log navigation.</div>
            </div>
          </div>
        </div>
      </Panel>
    </div>
  )
}