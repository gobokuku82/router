import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import SettingsModal from './SettingsModal';
import NotificationModal from './NotificationModal';
import UserModal from './UserModal';
import './Sidebar.css';

const Sidebar = ({ sidebarVisible, setSidebarVisible, currentUser, onLogout }) => {
  const location = useLocation();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);

  // 예시 알림 데이터 (실제로는 API에서 가져올 데이터)
  const notifications = [
    // 현재는 빈 배열로 "알림이 없습니다" 상태를 보여줍니다
    // 테스트를 위해 아래 주석을 해제하면 알림을 볼 수 있습니다
    
    {
      type: 'info',
      title: '새로운 방문 일정',
      message: '내일 오후 2시 ABC병원 방문 예정입니다.',
      time: '5분 전'
    },/*
    {
      type: 'warning',
      title: '보고서 제출 마감',
      message: '영업방문 보고서 제출 마감이 2시간 남았습니다.',
      time: '1시간 전'
    }
    */
  ];

  const menuItems = [
    { path: '/', icon: '🏠', label: '홈' },
    { path: '/search', icon: '🔍', label: '검색' },
    { path: '/chat', icon: '💬', label: '채팅' },
    { path: '/docs', icon: '📄', label: '문서 생성' },
    { path: '/client', icon: '👥', label: '고객 관리' },
    { path: '/employee', icon: '👤', label: '실적 확인' },
    { path: '/schedule', icon: '📅', label: '일정 관리' },
  ];

  const handleSettingsClick = () => {
    setIsSettingsOpen(true);
  };

  const handleCloseSettings = () => {
    setIsSettingsOpen(false);
  };

  const handleNotificationClick = () => {
    setIsNotificationModalOpen(true);
  };

  const handleUserClick = () => {
    setIsUserModalOpen(true);
  };

  const handleLogout = () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      onLogout();
    }
  };

  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  // 사용자 아바타에 표시할 이니셜 (이름의 첫 글자)
  const userInitial = currentUser?.name ? currentUser.name.charAt(0) : '김';

  return (
    <>
      {/* Header */}
      <header className="main-header">
        <div className="header-left">
          <button 
            className="sidebar-toggle-btn"
            onClick={toggleSidebar}
            title={sidebarVisible ? "사이드바 숨기기" : "사이드바 보이기"}
          >
            ☰
          </button>
          <div className="logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">Narutalk</span>
          </div>
        </div>
        
        <div className="header-right">
          <div className="header-actions">
            <button className="notification-btn" title="알림" onClick={handleNotificationClick}>
              🔔
            </button>
            <div className="user-profile" onClick={handleUserClick}>
              <div className="user-avatar" data-initial={userInitial}></div>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <div className={`sidebar ${sidebarVisible ? 'visible' : 'hidden'}`}>
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>
        
        <div className="sidebar-footer">
          <div className="nav-item settings-item" onClick={handleSettingsClick}>
            <span className="nav-icon">⚙️</span>
            <span className="nav-label">설정</span>
          </div>
          <div className="server-info">
            {currentUser?.name || '사용자'} ({currentUser?.id || 'N/A'})
          </div>
        </div>
      </div>

      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={handleCloseSettings}
        onLogout={onLogout}
        currentUser={currentUser}
      />
      
      <NotificationModal 
        isOpen={isNotificationModalOpen}
        onClose={() => setIsNotificationModalOpen(false)}
        notifications={notifications}
      />
      
      <UserModal
        isOpen={isUserModalOpen}
        onClose={() => setIsUserModalOpen(false)}
        userData={currentUser}
      />
    </>
  );
};

export default Sidebar; 