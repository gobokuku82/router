import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';

const LoginPage = ({ onLogin }) => {
  const navigate = useNavigate();
  const [loginData, setLoginData] = useState({
    employeeId: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // 미리 정의된 사용자 정보 (실제 환경에서는 백엔드 API 연동)
  const validUsers = [
    { id: 'E001', password: '1234', name: '김복남', department: '영업부' },
    { id: 'E002', password: '1234', name: '이영희', department: '마케팅부' },
    { id: 'admin', password: 'admin123', name: '관리자', department: '관리부' }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({
      ...prev,
      [name]: value
    }));
    // 입력 시 에러 메시지 초기화
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!loginData.employeeId || !loginData.password) {
      setError('사원번호와 비밀번호를 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setError('');

    // 로그인 시뮬레이션 (1초 대기)
    setTimeout(() => {
      const user = validUsers.find(
        u => u.id === loginData.employeeId && u.password === loginData.password
      );

      if (user) {
        // 로그인 성공
        const userData = {
          id: user.id,
          name: user.name,
          department: user.department,
          company: '좋은제약',
          position: '영업팀 대리',
          email: `${user.id.toLowerCase()}@goodpharm.co.kr`,
          phone: '010-1234-5678'
        };

        // 로컬 스토리지에 사용자 정보 저장
        localStorage.setItem('narutalk_user', JSON.stringify(userData));
        localStorage.setItem('narutalk_isLoggedIn', 'true');

        // 부모 컴포넌트에 로그인 상태 전달
        if (onLogin) {
          onLogin(userData);
        }

        // 대시보드로 이동
        navigate('/');
      } else {
        setError('사원번호 또는 비밀번호가 잘못되었습니다.');
      }

      setIsLoading(false);
    }, 1000);
  };

  const handleDemoLogin = () => {
    setLoginData({
      employeeId: 'E001',
      password: '1234'
    });
  };

  return (
    <div className="login-page">
      <div className="login-background">
        <div className="background-pattern"></div>
      </div>
      
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="company-logo">
              <span className="logo-icon">💊</span>
              <h1 className="company-name">좋은제약</h1>
            </div>
            <h2 className="app-name">Narutalk</h2>
            <p className="app-description">제약영업사원을 위한 AI 업무 파트너</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="employeeId">사원번호</label>
              <input
                type="text"
                id="employeeId"
                name="employeeId"
                value={loginData.employeeId}
                onChange={handleInputChange}
                placeholder="사원번호를 입력하세요"
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">비밀번호</label>
              <input
                type="password"
                id="password"
                name="password"
                value={loginData.password}
                onChange={handleInputChange}
                placeholder="비밀번호를 입력하세요"
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <button 
              type="submit" 
              className={`login-button ${isLoading ? 'loading' : ''}`}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="loading-spinner"></span>
                  로그인 중...
                </>
              ) : (
                '로그인'
              )}
            </button>

          </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 