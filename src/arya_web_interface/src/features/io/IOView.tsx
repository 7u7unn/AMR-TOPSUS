import { Panel } from '@/components/ui'
import { useIOStore } from '@/stores'
import { publishIOSetSingle } from '@/services/ros'

const DI_NAMES = ['Emergency Stop', 'Left Limit', 'Right Limit', 'Front Sensor', 'Rear Sensor', 'Charge Detect', 'Manual Mode', 'Reserved']
const DO_NAMES = ['Buzzer', 'Relay 1', 'Relay 2', 'Relay 3', 'Light 1', 'Light 2', 'Motor Enable', 'Reserved']

export function IOView() {
  const { digitalInputs, digitalOutputs, setOutput } = useIOStore()

  const diByte = digitalInputs.reduce((acc, val, i) => acc | (val ? (1 << i) : 0), 0)
  const doByte = digitalOutputs.reduce((acc, val, i) => acc | (val ? (1 << i) : 0), 0)
  const diActive = digitalInputs.filter(Boolean).length
  const doActive = digitalOutputs.filter(Boolean).length

  const handleOutputToggle = (index: number) => {
    const newValue = !digitalOutputs[index]
    setOutput(index, newValue)
    publishIOSetSingle(index, newValue)
  }

  const handleAllOn = () => {
    for (let i = 0; i < 8; i++) {
      setOutput(i, true)
      publishIOSetSingle(i, true)
    }
  }

  const handleAllOff = () => {
    for (let i = 0; i < 8; i++) {
      setOutput(i, false)
      publishIOSetSingle(i, false)
    }
  }

  const handleToggleAll = () => {
    const allOn = digitalOutputs.every(Boolean)
    for (let i = 0; i < 8; i++) {
      setOutput(i, !allOn)
      publishIOSetSingle(i, !allOn)
    }
  }

  return (
    <div>
      {/* Connection Strip */}
      <div className="conn-strip">
        <div className="conn-strip-header">I/O COMM</div>
        <div className="conn-diamond ok"></div>
        <div className="conn-field">
          <div className="conn-field-label">Port</div>
          <div className="conn-field-value">/dev/ttyS3</div>
        </div>
        <div className="conn-field">
          <div className="conn-field-label">Baud</div>
          <div className="conn-field-value">9600</div>
        </div>
        <div className="conn-field">
          <div className="conn-field-label">Parity</div>
          <div className="conn-field-value">None</div>
        </div>
        <div className="conn-field">
          <div className="conn-field-label">Slave ID</div>
          <div className="conn-field-value">1</div>
        </div>
        <div className="conn-field">
          <div className="conn-field-label">Protocol</div>
          <div className="conn-field-value">Modbus RTU</div>
        </div>
        <div className="conn-field" style={{ marginLeft: 'auto' }}>
          <div className="conn-field-label">Poll Rate</div>
          <div className="conn-field-value">10 Hz</div>
        </div>
      </div>

      {/* I/O Grid */}
      <div className="io-grid">
        {/* Digital Inputs */}
        <Panel title="Digital Inputs — DI" color="green">
          <div>
            <div className="io-status-strip">
              <span>Raw byte:</span>
              <span className="io-byte-chip">0x{diByte.toString(16).toUpperCase().padStart(2, '0')}</span>
              <span className="io-count">Active: <b style={{ color: '#2E7D32' }}>{diActive}</b>/8</span>
            </div>
            <div className="io-channels">
              {digitalInputs.map((on, i) => (
                <div key={i} className={`io-channel ${on ? 'on-di' : ''}`}>
                  <div className={`led ${on ? 'on' : ''}`}></div>
                  <div className="io-channel-info">
                    <div className="io-channel-num">DI {i}</div>
                    <div className="io-channel-name">{DI_NAMES[i] || `Channel ${i}`}</div>
                    <div className={`io-channel-status ${on ? 'on' : ''}`}>
                      {on ? 'ACTIVE' : 'INACTIVE'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        {/* Digital Outputs */}
        <Panel title="Digital Outputs — DO" color="orange">
          <div>
            <div className="io-status-strip">
              <span>Raw byte:</span>
              <span className="io-byte-chip" style={{ color: '#D95F02' }}>0x{doByte.toString(16).toUpperCase().padStart(2, '0')}</span>
              <span className="io-count">Active: <b style={{ color: '#D95F02' }}>{doActive}</b>/8</span>
            </div>
            <div className="io-channels">
              {digitalOutputs.map((on, i) => (
                <div key={i} className={`io-channel ${on ? 'on-do' : ''}`}>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={on}
                      onChange={() => handleOutputToggle(i)}
                    />
                    <span className="tog-track"></span>
                  </label>
                  <div className="io-channel-info">
                    <div className="io-channel-num">DO {i}</div>
                    <div className="io-channel-name">{DO_NAMES[i] || `Channel ${i}`}</div>
                    <div className={`io-channel-status ${on ? 'on-do' : ''}`}>
                      {on ? 'ACTIVE' : 'INACTIVE'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="bulk-row">
              <button className="bulk-btn" onClick={handleAllOn}>All On</button>
              <button className="bulk-btn danger" onClick={handleAllOff}>All Off</button>
              <button className="bulk-btn" onClick={handleToggleAll}>Toggle All</button>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  )
}