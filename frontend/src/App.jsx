import React, { useState, useEffect, useCallback } from 'react'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [file, setFile] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  async function analyze(e) {
    e.preventDefault()
    if (!file) return alert('Please select a resume file (PDF or DOCX).')
    
    setLoading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(API_BASE + '/analyze_resume', { 
        method: 'POST', 
        body: form 
      })
      const data = await res.json()
      if (res.ok) {
        setReport(data)
      } else {
        alert(data.detail || 'Analysis failed')
      }
    } catch (error) {
      alert('Error analyzing resume. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setFile(null)
    setReport(null)
  }

  function getScoreColor(score) {
    if (score >= 80) return '#10b981'
    if (score >= 60) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Resume Analyzer</h1>
        <p>Upload your resume and get an instant score with actionable tips to improve it</p>
      </div>

      <div className="main-card">
        <form onSubmit={analyze} className="upload-section">
          <div className="file-input-wrapper">
            <input 
              type="file" 
              accept=".pdf,.doc,.docx,.txt" 
              onChange={e => setFile(e.target.files[0])} 
              className="file-input"
              id="resume-file"
            />
            <label htmlFor="resume-file" className={`file-input-label ${file ? 'has-file' : ''}`}>
              <div className="upload-icon">
                {file ? '📄' : '📤'}
              </div>
              <div>
                {file ? (
                  <>
                    <strong>{file.name}</strong>
                    <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                      {(file.size / 1024).toFixed(1)} KB • Click to change
                    </div>
                  </>
                ) : (
                  <>
                    <strong>Choose your resume file</strong>
                    <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>
                      PDF, DOC, DOCX, or TXT format
                    </div>
                  </>
                )}
              </div>
            </label>
          </div>

          <div className="button-group">
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={loading || !file}
            >
              {loading ? (
                <>
                  <div className="loading-spinner"></div>
                  Analyzing...
                </>
              ) : (
                <>
                  ⚡ Analyze Resume
                </>
              )}
            </button>
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={reset}
              disabled={loading}
            >
              🔄 Reset
            </button>
          </div>
        </form>

        {report && (
          <div className="results">
            <div 
              className="score-section"
              style={{ '--score-percentage': `${(report.score / 100) * 360}deg` }}
            >
              <div 
                className="score-circle"
                style={{ 
                  background: `conic-gradient(from 0deg, ${getScoreColor(report.score)} 0%, ${getScoreColor(report.score)} ${(report.score / 100) * 360}deg, #e2e8f0 ${(report.score / 100) * 360}deg, #e2e8f0 100%)`
                }}
              >
                <div className="score-number" style={{ color: getScoreColor(report.score) }}>
                  {report.score}
                </div>
              </div>
              <div className="score-info">
                <h3>Overall Resume Score</h3>
                <p>Based on sections, action verbs, and readability analysis</p>
              </div>
            </div>

            <div className="metrics-grid">
              <div className="metric-card">
                <h4>
                  <span className="metric-icon">📋</span>
                  Resume Sections
                </h4>
                <ul className="sections-list">
                  <li className="section-item">
                    <span className="section-name">Contact Information</span>
                    <span className={`section-status ${report.sections.contact ? 'present' : 'missing'}`}>
                      {report.sections.contact ? '✅' : '❌'}
                    </span>
                  </li>
                  <li className="section-item">
                    <span className="section-name">Summary/Objective</span>
                    <span className={`section-status ${report.sections.summary ? 'present' : 'missing'}`}>
                      {report.sections.summary ? '✅' : '❌'}
                    </span>
                  </li>
                  <li className="section-item">
                    <span className="section-name">Skills</span>
                    <span className={`section-status ${report.sections.skills ? 'present' : 'missing'}`}>
                      {report.sections.skills ? '✅' : '❌'}
                    </span>
                  </li>
                  <li className="section-item">
                    <span className="section-name">Work Experience</span>
                    <span className={`section-status ${report.sections.experience ? 'present' : 'missing'}`}>
                      {report.sections.experience ? '✅' : '❌'}
                    </span>
                  </li>
                  <li className="section-item">
                    <span className="section-name">Education</span>
                    <span className={`section-status ${report.sections.education ? 'present' : 'missing'}`}>
                      {report.sections.education ? '✅' : '❌'}
                    </span>
                  </li>
                </ul>
              </div>

              <div className="metric-card">
                <h4>
                  <span className="metric-icon">📊</span>
                  Content Metrics
                </h4>
                <div className="metric-item">
                  <span className="metric-label">Action Verbs</span>
                  <span className="metric-value">{report.action_verb_count}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Total Words</span>
                  <span className="metric-value">{report.token_count}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Readability Score</span>
                  <span className="metric-value">{report.readability_score}/100</span>
                </div>
              </div>
            </div>

            {report.suggestions && report.suggestions.length > 0 && (
              <div className="suggestions-section">
                <h4>
                  💡 Improvement Suggestions
                </h4>
                <ul className="suggestions-list">
                  {report.suggestions.map((suggestion, index) => (
                    <li key={index} className="suggestion-item">
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="footer">
        <p>Designed to give general guidance — for best results, pair with human review</p>
      </div>
    </div>
  )
}