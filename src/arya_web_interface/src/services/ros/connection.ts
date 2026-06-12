import type {
  PublisherCommand,
  SubscriberData,
  ConnectionState,
} from '@/types/ros'

type MessageHandler = (data: SubscriberData) => void
type StatusHandler = (state: ConnectionState) => void

const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY_MS = 3000

class ROSConnection {
  private ws: WebSocket | null = null
  private url: string = ''
  private messageHandlers: Set<MessageHandler> = new Set()
  private statusHandlers: Set<StatusHandler> = new Set()
  private reconnectAttempts = 0
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  private shouldReconnect = true

  private state: ConnectionState = {
    status: 'disconnected',
    lastError: null,
    reconnectAttempts: 0,
  }

  private notifyStatusChange() {
    this.statusHandlers.forEach(handler => handler({ ...this.state }))
  }

  private setState(partial: Partial<ConnectionState>) {
    this.state = { ...this.state, ...partial }
    this.notifyStatusChange()
  }

  connect(url: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.url = url
    this.shouldReconnect = true
    this.reconnectAttempts = 0
    this.doConnect()
  }

  private doConnect(): void {
    if (!this.shouldReconnect) return

    this.setState({ status: 'connecting', lastError: null })

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.reconnectAttempts = 0
        this.setState({
          status: 'connected',
          lastError: null,
          reconnectAttempts: 0,
        })
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as SubscriberData
          this.messageHandlers.forEach(handler => handler(data))
        } catch {
          // Ignore malformed messages
        }
      }

      this.ws.onerror = () => {
        this.setState({
          status: 'error',
          lastError: 'WebSocket connection error',
        })
      }

      this.ws.onclose = () => {
        if (this.shouldReconnect && this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          this.reconnectAttempts++
          this.setState({
            status: 'connecting',
            reconnectAttempts: this.reconnectAttempts,
          })
          this.reconnectTimeout = setTimeout(() => this.doConnect(), RECONNECT_DELAY_MS)
        } else if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          this.setState({
            status: 'error',
            lastError: 'Max reconnection attempts reached',
          })
        } else {
          this.setState({ status: 'disconnected' })
        }
      }
    } catch (err) {
      this.setState({
        status: 'error',
        lastError: err instanceof Error ? err.message : 'Connection failed',
      })
    }
  }

  disconnect(): void {
    this.shouldReconnect = false
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.setState({ status: 'disconnected' })
  }

  send(command: PublisherCommand): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      return false
    }
    try {
      this.ws.send(JSON.stringify(command))
      return true
    } catch {
      return false
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler)
    handler({ ...this.state }) // Send current state immediately
    return () => this.statusHandlers.delete(handler)
  }

  getState(): ConnectionState {
    return { ...this.state }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// Singleton instance
export const rosConnection = new ROSConnection()