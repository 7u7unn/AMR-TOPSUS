import { useState, useEffect, useRef } from 'react'
import { Panel } from '@/components/ui'

interface TopicInfo {
  name: string
  type: string
}

interface EchoSlot {
  topicName: string
  topicType: string
  messages: string[]
  active: boolean
}

export function TopicsView() {
  const [topics, setTopics] = useState<TopicInfo[]>([])
  const [filter, setFilter] = useState('')
  const [echoSlot1, setEchoSlot1] = useState<EchoSlot>({ topicName: '', topicType: '', messages: [], active: false })
  const [echoSlot2, setEchoSlot2] = useState<EchoSlot>({ topicName: '', topicType: '', messages: [], active: false })
  const [isRefreshing, setIsRefreshing] = useState(false)
  const echoBody1Ref = useRef<HTMLPreElement>(null)
  const echoBody2Ref = useRef<HTMLPreElement>(null)

  // Fetch topics list
  const fetchTopics = async () => {
    setIsRefreshing(true)
    try {
      const response = await fetch('/api/topics')
      const data = await response.json()
      if (Array.isArray(data)) {
        setTopics(data)
      } else if (data.topics) {
        setTopics(data.topics)
      }
    } catch (error) {
      console.error('Failed to fetch topics:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchTopics()
    const interval = setInterval(fetchTopics, 5000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll echo bodies
  useEffect(() => {
    if (echoBody1Ref.current) {
      echoBody1Ref.current.scrollTop = echoBody1Ref.current.scrollHeight
    }
  }, [echoSlot1.messages])

  useEffect(() => {
    if (echoBody2Ref.current) {
      echoBody2Ref.current.scrollTop = echoBody2Ref.current.scrollHeight
    }
  }, [echoSlot2.messages])

  const filteredTopics = topics.filter(t =>
    t.name.toLowerCase().includes(filter.toLowerCase()) ||
    t.type.toLowerCase().includes(filter.toLowerCase())
  )

  const handleStartEcho = (slot: 1 | 2) => {
    const topic = slot === 1 ? echoSlot1.topicName : echoSlot2.topicName
    const topicInfo = topics.find(t => t.name === topic)
    if (!topicInfo) return

    if (slot === 1) {
      setEchoSlot1(prev => ({ ...prev, active: true, topicType: topicInfo.type, messages: [] }))
    } else {
      setEchoSlot2(prev => ({ ...prev, active: true, topicType: topicInfo.type, messages: [] }))
    }

    // In a real implementation, this would subscribe to the WebSocket topic
    // For now, we simulate with mock data
    const interval = setInterval(() => {
      const mockData = `header:
  stamp:
    sec: ${Math.floor(Date.now() / 1000)}
    nanosec: ${Date.now() % 1000 * 1000000}
  frame_id: "base_link"
---
`
      if (slot === 1) {
        setEchoSlot1(prev => ({
          ...prev,
          messages: [...prev.messages.slice(-99), mockData]
        }))
      } else {
        setEchoSlot2(prev => ({
          ...prev,
          messages: [...prev.messages.slice(-99), mockData]
        }))
      }
    }, 1000)

    return () => clearInterval(interval)
  }

  const handleStopEcho = (slot: 1 | 2) => {
    if (slot === 1) {
      setEchoSlot1(prev => ({ ...prev, active: false }))
    } else {
      setEchoSlot2(prev => ({ ...prev, active: false }))
    }
  }

  const activeEchoCount = (echoSlot1.active ? 1 : 0) + (echoSlot2.active ? 1 : 0)

  return (
    <div className="topic-grid">
      {/* Topic Control Panel */}
      <Panel title="ROS Topic Echo" color="cyan" headerRight={<span className="panel-chip">{topics.length} topics</span>}>
        <div>
          <div className="topic-controls">
            <div className="topic-field">
              <label className="topic-label">Filter</label>
              <input
                className="topic-search"
                type="search"
                placeholder="/topic name"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>

            <div className="topic-field">
              <label className="topic-label">Echo Slot 1</label>
              <select
                className="topic-select"
                value={echoSlot1.topicName}
                onChange={(e) => setEchoSlot1(prev => ({ ...prev, topicName: e.target.value }))}
                disabled={echoSlot1.active}
              >
                <option value="">Select topic...</option>
                {filteredTopics.map(t => (
                  <option key={t.name} value={t.name}>
                    {t.name} [{t.type}]
                  </option>
                ))}
              </select>
            </div>

            <div className="topic-field">
              <label className="topic-label">Echo Slot 2</label>
              <select
                className="topic-select"
                value={echoSlot2.topicName}
                onChange={(e) => setEchoSlot2(prev => ({ ...prev, topicName: e.target.value }))}
                disabled={echoSlot2.active}
              >
                <option value="">Select topic...</option>
                {filteredTopics.map(t => (
                  <option key={t.name} value={t.name}>
                    {t.name} [{t.type}]
                  </option>
                ))}
              </select>
            </div>

            <div className="topic-actions">
              <button
                className="topic-btn"
                onClick={() => handleStartEcho(1)}
                disabled={!echoSlot1.topicName}
              >
                Start Echo 1
              </button>
              <button
                className="topic-btn stop"
                onClick={() => handleStopEcho(1)}
                disabled={!echoSlot1.active}
              >
                Stop 1
              </button>
            </div>

            <div className="topic-actions">
              <button
                className="topic-btn"
                onClick={() => handleStartEcho(2)}
                disabled={!echoSlot2.topicName}
              >
                Start Echo 2
              </button>
              <button
                className="topic-btn stop"
                onClick={() => handleStopEcho(2)}
                disabled={!echoSlot2.active}
              >
                Stop 2
              </button>
            </div>

            <div className="topic-hint">
              Select a topic from the dropdown and click "Start Echo" to view real-time messages.
              {topics.length === 0 && ' ROS topic list belum dimuat.'}
            </div>
          </div>

          <div className="topic-meta">
            <div className="topic-stat">
              <span className="topic-label">Active Echo</span>
              <b>{activeEchoCount}/2</b>
            </div>
            <div className="topic-stat">
              <span className="topic-label">Update Rate</span>
              <b>{activeEchoCount > 0 ? '~1 Hz' : 'idle'}</b>
            </div>
          </div>

          <div style={{ padding: '0 12px 12px' }}>
            <button className="topic-btn" onClick={fetchTopics} disabled={isRefreshing}>
              {isRefreshing ? 'Refreshing...' : 'Refresh List'}
            </button>
          </div>
        </div>
      </Panel>

      {/* Echo Slots */}
      <div className="echo-grid">
        <div className={`echo-slot ${echoSlot1.active ? '' : 'idle'}`} id="echoSlot1">
          <div className="echo-slot-header">
            <span className="echo-title">Slot 1</span>
            <span className="echo-type">{echoSlot1.topicName ? echoSlot1.topicType || 'active' : 'idle'}</span>
          </div>
          <pre
            ref={echoBody1Ref}
            className={`echo-body ${echoSlot1.messages.length === 0 ? 'echo-empty' : ''}`}
          >
            {echoSlot1.messages.length === 0
              ? 'No topic selected'
              : echoSlot1.messages.join('')
            }
          </pre>
        </div>

        <div className={`echo-slot ${echoSlot2.active ? '' : 'idle'}`} id="echoSlot2">
          <div className="echo-slot-header">
            <span className="echo-title">Slot 2</span>
            <span className="echo-type">{echoSlot2.topicName ? echoSlot2.topicType || 'active' : 'idle'}</span>
          </div>
          <pre
            ref={echoBody2Ref}
            className={`echo-body ${echoSlot2.messages.length === 0 ? 'echo-empty' : ''}`}
          >
            {echoSlot2.messages.length === 0
              ? 'No topic selected'
              : echoSlot2.messages.join('')
            }
          </pre>
        </div>
      </div>
    </div>
  )
}