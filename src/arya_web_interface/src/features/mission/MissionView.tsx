import { useState } from 'react'
import { Panel } from '@/components/ui'
import { useMissionStore, Station } from '@/stores'
import { publishGoalPose } from '@/services/ros'

export function MissionView() {
  const {
    stations,
    missionQueue,
    currentMission,
    status,
    addStation,
    removeStation,
    addToQueue,
    removeFromQueue,
    setStatus
  } = useMissionStore()

  const [missionMode, setMissionMode] = useState<'single' | 'queue'>('single')
  const [newStationName, setNewStationName] = useState('')
  const [newStationX, setNewStationX] = useState('')
  const [newStationY, setNewStationY] = useState('')
  const [newStationTheta, setNewStationTheta] = useState('')
  const [newStationWait, setNewStationWait] = useState('0')
  const [editingStations, setEditingStations] = useState(false)

  const handleAddStation = () => {
    if (!newStationName || !newStationX || !newStationY) return

    const station: Station = {
      id: `station_${Date.now()}`,
      name: newStationName,
      x: parseFloat(newStationX) || 0,
      y: parseFloat(newStationY) || 0,
      theta: (parseFloat(newStationTheta) || 0) * Math.PI / 180,
      wait: parseInt(newStationWait) || 0,
    }

    addStation(station)
    setNewStationName('')
    setNewStationX('')
    setNewStationY('')
    setNewStationTheta('')
    setNewStationWait('0')
  }

  const handleGoToStation = (station: Station) => {
    publishGoalPose(station.x, station.y, station.theta)
    setStatus('running')
  }

  const handleStartQueue = () => {
    if (missionQueue.length === 0) return
    const first = missionQueue[0]
    if (first) {
      handleGoToStation(first.waypoints[0])
    }
  }

  const handleClearQueue = () => {
    missionQueue.forEach(m => removeFromQueue(m.id))
  }

  const handleStartSingle = (station: Station) => {
    publishGoalPose(station.x, station.y, station.theta)
    setStatus('running')
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '16px', letterSpacing: '.1em', textTransform: 'uppercase' }}>
        Mission Management
      </h2>

      <div className="nav-grid">
        {/* Station Registry */}
        <Panel id="p-mission-stations" title="Station Registry" color="cyan" style={{ gridColumn: '1 / -1' }}>
          <div className="nav-controls-body">
            <div className="nav-section-header">
              <span className="nav-section-title">Stations</span>
              <button
                className={`btn-edit-toggle ${editingStations ? 'active' : ''}`}
                onClick={() => setEditingStations(!editingStations)}
              >
                {editingStations ? 'Done' : 'Edit'}
              </button>
            </div>

            {editingStations && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginBottom: '16px', padding: '12px', background: '#f7f9fb', borderRadius: '6px' }}>
                <div className="goal-field" style={{ minWidth: '120px' }}>
                  <label>Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newStationName}
                    onChange={(e) => setNewStationName(e.target.value)}
                    placeholder="Station A"
                  />
                </div>
                <div className="goal-field" style={{ minWidth: '80px' }}>
                  <label>X (m)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-input"
                    value={newStationX}
                    onChange={(e) => setNewStationX(e.target.value)}
                  />
                </div>
                <div className="goal-field" style={{ minWidth: '80px' }}>
                  <label>Y (m)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-input"
                    value={newStationY}
                    onChange={(e) => setNewStationY(e.target.value)}
                  />
                </div>
                <div className="goal-field" style={{ minWidth: '80px' }}>
                  <label>θ (°)</label>
                  <input
                    type="number"
                    step="1"
                    className="form-input"
                    value={newStationTheta}
                    onChange={(e) => setNewStationTheta(e.target.value)}
                  />
                </div>
                <div className="goal-field" style={{ minWidth: '60px' }}>
                  <label>Wait (s)</label>
                  <input
                    type="number"
                    min="0"
                    className="form-input"
                    value={newStationWait}
                    onChange={(e) => setNewStationWait(e.target.value)}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  <button className="topic-btn" onClick={handleAddStation} style={{ height: '36px' }}>
                    Add Station
                  </button>
                </div>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
              {stations.length === 0 && (
                <div className="empty-note" style={{ gridColumn: '1 / -1' }}>
                  No stations configured. Click Edit to add stations.
                </div>
              )}
              {stations.map(station => (
                <div
                  key={station.id}
                  className="station-row"
                  style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
                >
                  <div>
                    <strong style={{ fontSize: '1rem' }}>{station.name}</strong>
                    <span style={{ display: 'block', fontSize: '0.7rem' }}>
                      X: {station.x.toFixed(2)} Y: {station.y.toFixed(2)} θ: {(station.theta * 180 / Math.PI).toFixed(0)}°
                    </span>
                    <span style={{ display: 'block', fontSize: '0.65rem', color: '#8794A3' }}>
                      Wait: {station.wait}s
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button
                      className="topic-btn"
                      onClick={() => handleStartSingle(station)}
                      style={{ flex: 1 }}
                    >
                      Go
                    </button>
                    <button
                      className="topic-btn"
                      onClick={() => addToQueue({
                        id: `mission_${Date.now()}`,
                        name: `To ${station.name}`,
                        waypoints: [station],
                        status: 'pending'
                      })}
                      style={{ flex: 1 }}
                    >
                      + Queue
                    </button>
                    {editingStations && (
                      <button
                        className="mini-action-btn danger"
                        onClick={() => removeStation(station.id)}
                      >
                        Del
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        {/* Mission Queue */}
        <Panel id="p-mission-queue" title="Mission Queue" color="orange" style={{ gridColumn: '1 / -1' }}>
          <div className="nav-controls-body">
            <div className="mission-mode-row">
              <button
                className={`mission-mode-btn ${missionMode === 'single' ? 'active' : ''}`}
                onClick={() => setMissionMode('single')}
              >
                Single Mission
              </button>
              <button
                className={`mission-mode-btn ${missionMode === 'queue' ? 'active' : ''}`}
                onClick={() => setMissionMode('queue')}
              >
                Queued Missions
              </button>
            </div>

            {missionMode === 'queue' && (
              <>
                <div className="mission-queue-list" style={{ marginTop: '16px' }}>
                  {missionQueue.length === 0 && (
                    <div className="empty-note">
                      No missions in queue. Add stations to the queue from the registry above.
                    </div>
                  )}
                  {missionQueue.map((mission, index) => (
                    <div key={mission.id} className="queue-row">
                      <div>
                        <strong>{index + 1}. {mission.name}</strong>
                        <span>{mission.waypoints.length} waypoint(s)</span>
                      </div>
                      <div className="row-actions">
                        <button
                          className="mini-action-btn"
                          onClick={() => removeFromQueue(mission.id)}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mission-toolbar" style={{ marginTop: '16px' }}>
                  <button
                    className="topic-btn"
                    onClick={handleStartQueue}
                    disabled={missionQueue.length === 0}
                  >
                    Start Queue
                  </button>
                  <button
                    className="topic-btn stop"
                    onClick={() => setStatus('idle')}
                  >
                    Cancel Queue
                  </button>
                  <button
                    className="topic-btn"
                    onClick={handleClearQueue}
                    disabled={missionQueue.length === 0}
                  >
                    Clear Queue
                  </button>
                </div>
              </>
            )}

            {missionMode === 'single' && (
              <div className="form-info" style={{ marginTop: '16px' }}>
                Single mission mode: Click "Go" on any station to start navigation immediately.
              </div>
            )}
          </div>
        </Panel>

        {/* Mission Status */}
        <Panel id="p-mission-status" title="Current Mission Status" color="green" style={{ gridColumn: '1 / -1' }}>
          <div className="nav-controls-body">
            <div className={`nav-status-bar ${status === 'running' ? 'running' : status === 'success' ? 'success' : status === 'error' ? 'error' : 'idle'}`}>
              <span className="nav-status-label">Status:</span>
              <span className="nav-status-value">{status.toUpperCase()}</span>
            </div>

            {currentMission && (
              <div style={{ marginTop: '16px' }}>
                <div className="form-label">Current Mission</div>
                <div style={{ padding: '12px', background: '#f7f9fb', borderRadius: '6px', marginTop: '8px' }}>
                  <strong>{currentMission.name}</strong>
                  <div style={{ fontSize: '0.8rem', color: '#5E6B78', marginTop: '4px' }}>
                    {currentMission.waypoints.length} waypoint(s)
                  </div>
                </div>
              </div>
            )}

            {!currentMission && (
              <div className="empty-note" style={{ marginTop: '16px' }}>
                No active mission. Select a station to begin.
              </div>
            )}
          </div>
        </Panel>
      </div>
    </div>
  )
}