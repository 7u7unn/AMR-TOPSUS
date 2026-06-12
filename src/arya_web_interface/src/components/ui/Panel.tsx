import { useState, ReactNode, CSSProperties } from 'react'

type PanelColor = 'cyan' | 'orange' | 'green' | 'yellow' | 'red'

interface PanelProps {
  title: string
  color?: PanelColor
  children: ReactNode
  collapsible?: boolean
  headerRight?: ReactNode
  defaultCollapsed?: boolean
  className?: string
  id?: string
  style?: CSSProperties
}

export function Panel({
  title,
  color = 'cyan',
  children,
  collapsible = true,
  headerRight,
  defaultCollapsed = false,
  className = '',
  id,
  style,
}: PanelProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed)

  const getColorDot = () => {
    const colors: Record<PanelColor, string> = {
      cyan: '#0A6ED1',
      orange: '#D95F02',
      green: '#2E7D32',
      yellow: '#B7791F',
      red: '#C62828',
    }
    return colors[color]
  }

  return (
    <div className={`panel ${color} ${collapsed ? 'collapsed' : ''} ${className}`} id={id} style={style}>
      <div className="panel-header">
        <div className="panel-header-dot" style={{ background: getColorDot() }}></div>
        <span className="panel-title">{title}</span>
        {headerRight}
        <div className="panel-header-right">
          {collapsible && (
            <button
              className="panel-collapse-btn"
              onClick={() => setCollapsed(!collapsed)}
              aria-label={collapsed ? 'Expand panel' : 'Collapse panel'}
            >
              ▾
            </button>
          )}
        </div>
      </div>
      <div className="panel-body-wrap">
        <div className="panel-body">{children}</div>
      </div>
    </div>
  )
}