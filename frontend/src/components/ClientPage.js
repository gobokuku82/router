import React, { useState } from 'react';
import './ClientPage.css';

const ClientPage = () => {
  const [selectedAnalysis, setSelectedAnalysis] = useState('ABC회사 분석 결과 보고서');
  const [userMessage, setUserMessage] = useState('ABC회사에 등급을 데이터로 분석해 주세요, 관련 분석 보고서 중심해줘.');
  const [aiResponse, setAiResponse] = useState('네, ABC 회사의 등급과 관련 분석을 고객의 등급 기준마다 분석하여 결과 보고서를 작성해 보겠습니다.');
  const [inputMessage, setInputMessage] = useState('');
  
  const existingAnalyses = [
    'ABC회사_분석결과보고서_20...',
    'SSS회사_분석결과보고서_20...',
    '000회사_분석결과보고서_20...'
  ];

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      // 실제로는 AI API 호출
      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="client-page">
      {/* Left Sidebar */}
      <div className="client-sidebar">
        <h2>고객 분석</h2>
        
        <button className="new-analysis-btn">
          <span className="plus-icon">+</span>
          새로운 고객 분석
        </button>

        <div className="existing-analyses">
          <h3>기존 분석</h3>
          {existingAnalyses.length > 0 ? (
            existingAnalyses.map((analysis, index) => (
              <div key={index} className="analysis-item">
                <span className="analysis-icon">💬</span>
                <span className="analysis-name">{analysis}</span>
                <span className="analysis-arrow">›</span>
              </div>
            ))
          ) : (
            <div className="no-analyses">
              <p>기존 분석이 없습니다.</p>
            </div>
          )}
        </div>
      </div>

      {/* Center Content Area */}
      <div className="client-main">
        <div className="analysis-content">
          <h1>{selectedAnalysis}</h1>
          <div className="analysis-body">
            {/* 분석 내용이 여기에 표시됩니다 */}
          </div>
        </div>
      </div>

      {/* Right Panel - AI Assistant */}
      <div className="client-ai-panel">
        <h2>고객 분석 요청</h2>
        
        <div className="chat-container">
          {/* User Message */}
          <div className="message user-message">
            {userMessage}
          </div>

          {/* AI Response */}
          <div className="message ai-message">
            <div className="ai-avatar">👤</div>
            <div className="message-content">
              {aiResponse}
              <div className="ai-prompts">
                <p>제품설명회 세부 내역을 작성해주세요!</p>
                <ul>
                  <li>제품 설명회 주요 내용</li>
                  <li>참석 인원</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="input-area">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="메시지를 입력해주세요"
            className="message-input"
          />
          <button 
            onClick={handleSendMessage}
            className="send-button"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
};

export default ClientPage; 