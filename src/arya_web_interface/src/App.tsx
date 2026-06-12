import { useState } from 'react'
import { Header, Sidebar, StatusBar } from '@/components/layout'
import { ToastContainer, Modal, showToast } from '@/components/ui'
import { DriveView } from '@/features/drive'
import { IOView } from '@/features/io'
import { NavigationView } from '@/features/navigation'
import { TeleopView } from '@/features/teleop'
import { MissionView } from '@/features/mission'
import { TopicsView } from '@/features/topics'
import { SettingsView } from '@/features/settings'
import { useROS } from '@/hooks'
import { publishMode } from '@/services/ros'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activeView, setActiveView] = useState('drive')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [emergencyModalOpen, setEmergencyModalOpen] = useState(false)
  const [driveStatus] = useState('IDLE')
  const [ioStatus] = useState('OFFLINE')
  const [statusMessage] = useState('System ready')

  // Initialize ROS connection and subscriptions
  useROS()

  const handleEmergencyStop = () => {
    showToast('EMERGENCY STOP', 'Robot stopped. Switch to Manual mode to resume.', 'error')
    setEmergencyModalOpen(true)
  }

  const handleResumeFromEmergency = () => {
    publishMode('manual')
    setEmergencyModalOpen(false)
    showToast('Mode Changed', 'Switched to Manual mode.', 'info')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Header
        onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <div className="hmi-body">
        <Sidebar
          activeView={activeView}
          collapsed={sidebarCollapsed}
          onNavigate={setActiveView}
        />

        <div className="hmi-workspace">
          <div className="hmi-content">
            {/* Drive View */}
            <div className={`view ${activeView === 'drive' ? 'active' : ''}`} id="view-drive">
              <DriveView />
            </div>

            {/* I/O View */}
            <div className={`view ${activeView === 'io' ? 'active' : ''}`} id="view-io">
              <IOView />
            </div>

            {/* ROS Topics View */}
            <div className={`view ${activeView === 'topics' ? 'active' : ''}`} id="view-topics">
              <TopicsView />
            </div>

            {/* Navigation View */}
            <div className={`view ${activeView === 'navigation' ? 'active' : ''}`} id="view-navigation">
              <NavigationView />
            </div>

            {/* Teleop View */}
            <div className={`view ${activeView === 'teleop' ? 'active' : ''}`} id="view-teleop">
              <TeleopView onEmergencyStop={handleEmergencyStop} />
            </div>

            {/* Mission View */}
            <div className={`view ${activeView === 'mission' ? 'active' : ''}`} id="view-mission">
              <MissionView />
            </div>

            {/* Settings View */}
            <div className={`view ${activeView === 'settings' ? 'active' : ''}`} id="view-settings">
              <SettingsView />
            </div>
          </div>
        </div>
      </div>

      <StatusBar
        driveStatus={driveStatus}
        ioStatus={ioStatus}
        message={statusMessage}
      />

      <ToastContainer />

      {/* Settings Modal */}
      <Modal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        title="System Settings"
        icon="⚙"
      >
        <div className="form-group">
          <label className="form-label">WebSocket Host</label>
          <input className="form-input" type="text" placeholder="Auto-detect from hostname" />
        </div>
        <div className="form-group">
          <label className="form-label">WebSocket Port</label>
          <input className="form-input" type="text" defaultValue="8000" />
        </div>
        <div className="form-group">
          <label className="form-label">Map Folder Path</label>
          <input className="form-input" type="text" value="amr_bringup_headless/maps" readOnly />
        </div>
        <div className="form-info">
          Changes to host/port require page reload. Robot firmware version: YMPI-FW-2.0.1
        </div>
        <div className="modal-footer" style={{ padding: 0, background: 'transparent', border: 'none' }}>
          <button className="modal-btn" onClick={() => setSettingsOpen(false)}>Cancel</button>
          <button className="modal-btn confirm" onClick={() => setSettingsOpen(false)}>Apply &amp; Reload</button>
        </div>
      </Modal>

      {/* Emergency Stop Modal */}
      <Modal
        isOpen={emergencyModalOpen}
        onClose={() => setEmergencyModalOpen(false)}
        title="EMERGENCY STOP ACTIVATED"
        icon="🚨"
        variant="error"
      >
        <div style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>
          <p style={{ marginBottom: '12px' }}>
            The robot has been stopped due to emergency stop activation.
          </p>
          <p>
            All motion commands are blocked until you switch modes.
          </p>
        </div>
        <div className="modal-footer" style={{ padding: 0, background: 'transparent', border: 'none' }}>
          <button className="modal-btn" onClick={() => setEmergencyModalOpen(false)}>OK</button>
          <button className="modal-btn confirm" onClick={handleResumeFromEmergency}>Switch to Manual</button>
        </div>
      </Modal>
    </div>
  )
}

export default App