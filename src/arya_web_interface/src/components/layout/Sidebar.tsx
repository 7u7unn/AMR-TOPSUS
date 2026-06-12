interface SidebarProps {
  activeView: string
  collapsed: boolean
  onNavigate: (view: string) => void
}

const navItems = [
  { id: 'drive', icon: '⬡', label: 'Drive Control', badge: null },
  { id: 'io', icon: '◈', label: 'I/O Module', badgeId: 'ioBadge', count: 8 },
  { id: 'topics', icon: 'T', label: 'ROS Topics', badgeId: 'topicBadge', count: 0 },
  { id: 'navigation', icon: '◰', label: 'Navigation', badge: null },
  { id: 'teleop', icon: '⌘', label: 'Teleop', badge: null },
  { id: 'mission', icon: '▶', label: 'Mission', badge: null },
]

export function Sidebar({ activeView, collapsed, onNavigate }: SidebarProps) {
  return (
    <nav className={`hmi-sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="nav-section-lbl">Views</div>

      {navItems.map(item => (
        <div
          key={item.id}
          className={`nav-item ${activeView === item.id ? 'active' : ''}`}
          onClick={() => onNavigate(item.id)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-lbl">{item.label}</span>
          {item.badgeId === 'ioBadge' && (
            <span className="nav-badge">8/8</span>
          )}
          {item.badgeId === 'topicBadge' && (
            <span className="nav-badge">0/2</span>
          )}
        </div>
      ))}

      <div className="nav-section-lbl" style={{ marginTop: 'auto' }}>System</div>
      <div className="nav-item settings-item" onClick={() => onNavigate('settings')}>
        <span className="nav-icon">⚙</span>
        <span className="nav-lbl">Settings</span>
      </div>
    </nav>
  )
}