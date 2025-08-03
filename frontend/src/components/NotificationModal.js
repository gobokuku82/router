import React from 'react';
import './NotificationModal.css';

function NotificationModal({ isOpen, onClose, notifications = [] }) {
  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="notification-modal">
        <div className="modal-header">
          <h3>알림</h3>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-content">
          {notifications.length === 0 ? (
            <div className="no-notifications">
              <div className="no-notifications-icon">🔕</div>
              <p>알림이 존재하지 않습니다</p>
            </div>
          ) : (
            <div className="notifications-list">
              {notifications.map((notification, index) => (
                <div key={index} className="notification-item">
                  <div className="notification-icon">
                    {notification.type === 'warning' ? '⚠️' : 
                     notification.type === 'info' ? 'ℹ️' : 
                     notification.type === 'success' ? '✅' : '🔔'}
                  </div>
                  <div className="notification-content">
                    <div className="notification-title">{notification.title}</div>
                    <div className="notification-message">{notification.message}</div>
                    <div className="notification-time">{notification.time}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default NotificationModal; 