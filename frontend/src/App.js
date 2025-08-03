import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Components
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import SearchPage from './components/SearchPage';
import ChatScreen from './components/ChatScreen';
import DocsPage from './components/DocsPage';
import ClientPage from './components/ClientPage';
import EmployeePerformance from './components/EmployeePerformance';
import SchedulePage from './components/SchedulePage';
import LoginPage from './components/LoginPage';

function App() {
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // 컴포넌트 마운트 시 로그인 상태 확인
  useEffect(() => {
    const checkLoginStatus = () => {
      const loginStatus = localStorage.getItem('narutalk_isLoggedIn');
      const userData = localStorage.getItem('narutalk_user');
      
      if (loginStatus === 'true' && userData) {
        setIsLoggedIn(true);
        setCurrentUser(JSON.parse(userData));
      }
      
      setIsLoading(false);
    };

    checkLoginStatus();
  }, []);

  const handleLogin = (userData) => {
    setIsLoggedIn(true);
    setCurrentUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('narutalk_isLoggedIn');
    localStorage.removeItem('narutalk_user');
    setIsLoggedIn(false);
    setCurrentUser(null);
  };

  // 로딩 중일 때 표시할 컴포넌트
  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="loading-spinner-large"></div>
          <p>Narutalk 로딩 중...</p>
        </div>
      </div>
    );
  }

  // 로그인되지 않은 경우 로그인 페이지 표시
  if (!isLoggedIn) {
    return (
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    );
  }

  // 로그인된 경우 메인 애플리케이션 표시
  return (
    <Router>
      <div className="App">
        <Sidebar 
          sidebarVisible={sidebarVisible} 
          setSidebarVisible={setSidebarVisible}
          currentUser={currentUser}
          onLogout={handleLogout}
        />
        <div className={`main-content ${!sidebarVisible ? 'sidebar-hidden' : ''}`}>
          <Routes>
            <Route path="/" element={<Dashboard currentUser={currentUser} />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/chat" element={<ChatScreen />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/client" element={<ClientPage />} />
            <Route path="/employee" element={<EmployeePerformance currentUser={currentUser} />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
