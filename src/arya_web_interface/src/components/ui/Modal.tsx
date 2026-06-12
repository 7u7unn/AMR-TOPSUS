import { ReactNode } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  icon?: string
  variant?: 'default' | 'warning' | 'success' | 'error'
  children: ReactNode
  footer?: ReactNode
}

export function Modal({ isOpen, onClose, title, icon, variant = 'default', children, footer }: ModalProps) {
  if (!isOpen) return null

  const getVariantClass = () => {
    switch (variant) {
      case 'warning': return 'warning'
      case 'success': return 'success'
      case 'error': return 'error'
      default: return ''
    }
  }

  return (
    <>
      <div className="modal-backdrop open" onClick={onClose}></div>
      <div className="modal open" role="dialog" aria-modal="true">
        <div className={`modal-panel ${getVariantClass()}`}>
          <div className="modal-header">
            <span>{icon || '⚙'}</span>
            <span className="modal-title">{title}</span>
            <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
          </div>
          <div className="modal-body">{children}</div>
          {footer && <div className="modal-footer">{footer}</div>}
        </div>
      </div>
    </>
  )
}

interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmText?: string
  cancelText?: string
}

export function ConfirmModal({ isOpen, onClose, onConfirm, title, message, confirmText = 'Confirm', cancelText = 'Cancel' }: ConfirmModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} icon="⚠" variant="warning">
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{ fontSize: '1.8rem', flexShrink: 0 }}>⚠</div>
        <div style={{ fontSize: '.86rem', color: '#1F2A33', lineHeight: 1.5 }}>
          <strong style={{ color: '#B7791F', display: 'block', marginBottom: '4px', fontSize: '.9rem', letterSpacing: '.06em' }}>{title}</strong>
          <span>{message}</span>
        </div>
      </div>
      <div className="modal-footer" style={{ padding: 0, background: 'transparent', border: 'none' }}>
        <button className="modal-btn" onClick={onClose}>{cancelText}</button>
        <button className="modal-btn danger" onClick={onConfirm}>{confirmText}</button>
      </div>
    </Modal>
  )
}