import React, {useState} from 'react'

const API_BASE = 'http://localhost:8000'

export default function App(){
  const [file, setFile] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  async function analyze(e){
    e.preventDefault()
    if(!file) return alert('Please select a resume file (PDF or DOCX).')
    setLoading(true)
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(API_BASE + '/analyze_resume', { method: 'POST', body: form })
    const data = await res.json()
    setReport(data)
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-3xl w-full">
        <div className="text-center mb-6">
          <h1 className="text-4xl font-extrabold text-slate-900">Resume Analyzer</h1>
          <p className="text-slate-600 mt-2">Upload your resume and get an instant score & tips to improve it.</p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <form onSubmit={analyze}>
            <div className="mb-3">
              <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={e=>setFile(e.target.files[0])} className="form-control" />
            </div>
            <div className="d-flex gap-2">
              <button className="btn btn-primary flex-grow-1" disabled={loading}>Analyze Resume</button>
              <button type="button" className="btn btn-outline-secondary" onClick={()=>{ setFile(null); setReport(null); }}>Reset</button>
            </div>
          </form>

          {report && (
            <div className="mt-5">
              <div className="d-flex align-items-center gap-3 mb-3">
                <div className="position-relative" style={{width:80,height:80}}>
                  <div className="rounded-circle d-flex align-items-center justify-content-center" style={{background:'#e6f4ea',width:80,height:80}}>
                    <span className="fs-4 fw-bold" style={{color:'#1b7a48'}}>{report.score}</span>
                  </div>
                </div>
                <div>
                  <h3 className="h5 mb-0">Overall Resume Score</h3>
                  <p className="mb-0 text-muted">Based on sections, action verbs and readability</p>
                </div>
              </div>

              <div className="row">
                <div className="col-md-6 mb-3">
                  <div className="p-3 border rounded">
                    <h6>Sections</h6>
                    <ul className="list-unstyled mb-0">
                      <li>Contact: <strong>{report.sections.contact ? '✔' : '✖'}</strong></li>
                      <li>Summary: <strong>{report.sections.summary ? '✔' : '✖'}</strong></li>
                      <li>Skills: <strong>{report.sections.skills ? '✔' : '✖'}</strong></li>
                      <li>Experience: <strong>{report.sections.experience ? '✔' : '✖'}</strong></li>
                      <li>Education: <strong>{report.sections.education ? '✔' : '✖'}</strong></li>
                    </ul>
                  </div>
                </div>
                <div className="col-md-6 mb-3">
                  <div className="p-3 border rounded">
                    <h6>Metrics</h6>
                    <p className="mb-1">Action verbs: <strong>{report.action_verb_count}</strong></p>
                    <p className="mb-1">Token count: <strong>{report.token_count}</strong></p>
                    <p className="mb-1">Readability score: <strong>{report.readability_score}</strong></p>
                  </div>
                </div>
              </div>

              <div className="mt-3">
                <h6>Suggestions</h6>
                <ul className="list-group">
                  {report.suggestions.map((s,i)=>(
                    <li key={i} className="list-group-item">{s}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="text-center mt-4 text-sm text-muted">Designed to give general guidance — for best results, pair with human review.</div>
      </div>
    </div>
  )
}
