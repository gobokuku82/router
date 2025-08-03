import React, { useState } from 'react';
import './SearchPage.css';

const SearchPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([
    {
      id: 1,
      documentName: '윤리 강령',
      classification: '내부',
      author: '김지수',
      creationDate: '2023-11-15',
      aiSummary: ''
    },
    {
      id: 2,
      documentName: '인사도',
      classification: '내부',
      author: '박민준',
      creationDate: '2023-11-20',
      aiSummary: ''
    },
    {
      id: 3,
      documentName: '의약품 관련 법률',
      classification: '외부',
      author: '자동',
      creationDate: '2023-11-22',
      aiSummary: ''
    },
    {
      id: 4,
      documentName: 'A_제품 설명서',
      classification: '외부',
      author: '자동',
      creationDate: '2023-11-10',
      aiSummary: ''
    },
    {
      id: 5,
      documentName: '공시 정보 관리 규정',
      classification: '내부',
      author: '박민준',
      creationDate: '2023-11-18',
      aiSummary: ''
    },
    {
      id: 6,
      documentName: '지출 보고서 가이드 라인',
      classification: '외부',
      author: '자동',
      creationDate: '2023-11-25',
      aiSummary: ''
    },
    {
      id: 7,
      documentName: 'B_제품 설명서',
      classification: '외부',
      author: '자동',
      creationDate: '2023-11-05',
      aiSummary: ''
    },
    {
      id: 8,
      documentName: '주간 영업 보고서',
      classification: '내부',
      author: '박민준',
      creationDate: '2023-11-12',
      aiSummary: ''
    }
  ]);

  const handleSearch = (e) => {
    e.preventDefault();
    // 실제 검색 로직은 나중에 구현
    console.log('Searching for:', searchQuery);
  };

  return (
    <div className="search-page">
      <div className="search-header">
        <h1>내/외부 문서 검색</h1>
      </div>

      <div className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <div className="search-input-wrapper">
              <i className="search-icon">🔍</i>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="검색어를 입력하세요..."
                className="search-input"
              />
            </div>
            <button type="submit" className="search-button">
              검색
            </button>
          </div>
        </form>

        <div className="search-filters">
          <button className="filter-button active">문서명</button>
          <button className="filter-button">최신순</button>
          <button className="filter-button">작성자</button>
        </div>

        <div className="search-results">
          <div className="results-table">
            <table>
              <thead>
                <tr>
                  <th>문서명</th>
                  <th>내/외부 구분</th>
                  <th>작성자</th>
                  <th>작성일</th>
                  <th>AI 요약</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((result) => (
                  <tr key={result.id}>
                    <td>{result.documentName}</td>
                    <td>
                      <span className={`classification-tag ${result.classification === '내부' ? 'internal' : 'external'}`}>
                        {result.classification}
                      </span>
                    </td>
                    <td>{result.author}</td>
                    <td>{result.creationDate}</td>
                    <td>{result.aiSummary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchPage; 