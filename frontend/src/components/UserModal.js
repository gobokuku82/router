import React from 'react';
import './UserModal.css';

function UserModal({ isOpen, onClose, userData = {} }) {
  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // 기본 사용자 데이터
  const defaultUserData = {
    name: '김복남',
    company: '좋은제약',
    position: '영업팀 대리',
    department: '영업부',
    email: 'kim.boknam@goodpharm.co.kr',
    phone: '010-1234-5678',
    avatar: '김'
  };

  const user = { ...defaultUserData, ...userData };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="user-modal">
        <div className="modal-header">
          <h3>사용자 정보</h3>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-content">
          <div className="user-profile-section">
            <div className="user-avatar-large">
              {user.avatar}
            </div>
            <div className="user-basic-info">
              <h2 className="user-name">{user.name}</h2>
              <p className="user-position">{user.position}</p>
            </div>
          </div>
          
          <div className="user-details">
            <div className="detail-item">
              <div className="detail-label">회사명</div>
              <div className="detail-value">{user.company}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">부서</div>
              <div className="detail-value">{user.department}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">이메일</div>
              <div className="detail-value">{user.email}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">연락처</div>
              <div className="detail-value">{user.phone}</div>
            </div>
          </div>

          <div className="modal-actions">
            <button className="action-button secondary" onClick={onClose}>
              확인
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserModal; 