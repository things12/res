from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io, re
from PyPDF2 import PdfReader
import docx
import textstat
from typing import List

app = FastAPI(title='Resume Analyzer API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

ACTION_VERBS = {
    'managed','led','developed','designed','implemented','created','improved','built','analyzed',
    'optimized','collaborated','maintained','deployed','engineered','researched','coordinated',
    'supervised','trained','automated','streamlined','established','initiated','launched',
    'executed','delivered','achieved','exceeded','increased','reduced','enhanced','transformed'
}

SKILL_KEYWORDS = {
    'programming': ['python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift'],
    'web': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask'],
    'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite'],
    'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git'],
    'data': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'tableau', 'powerbi'],
    'soft': ['leadership', 'communication', 'teamwork', 'problem-solving', 'analytical']
}

class RealTimeRequest(BaseModel):
    text: str

class RealTimeAnalysis(BaseModel):
    live_score: int
    suggestions: List[str]
    sections_found: dict
    action_verb_count: int
    word_count: int
    skill_matches: dict

def extract_text_from_pdf(content: bytes):
    try:
        reader = PdfReader(io.BytesIO(content))
        texts = []
        raw = content.decode('latin1', errors='ignore')
        for page in reader.pages:
            texts.append(page.extract_text() or '')
        return '\n'.join(texts), raw
    except Exception:
        return '', ''

def extract_text_from_docx(content: bytes):
    bio = io.BytesIO(content)
    try:
        doc = docx.Document(bio)
        paragraphs = [p.text for p in doc.paragraphs]
        raw = '\n'.join(paragraphs)
        return '\n'.join(paragraphs), raw
    except Exception:
        try:
            return content.decode('utf-8', errors='ignore'), content.decode('utf-8', errors='ignore')
        except:
            return '', ''

def tokenize(text: str):
    return re.findall(r"[A-Za-z]{2,}", text.lower())

def detect_sections(text: str):
    low = text.lower()
    sections = {
        'contact': bool(re.search(r'email|@|phone|tel\b|contact|linkedin', low)),
        'summary': 'summary' in low or 'objective' in low or 'profile' in low,
        'skills': 'skill' in low or 'technical skills' in low or 'competencies' in low,
        'experience': 'experience' in low or 'work experience' in low or 'professional experience' in low or 'employment' in low,
        'education': 'education' in low or 'degree' in low or 'bachelor' in low or 'master' in low or 'university' in low or 'college' in low,
        'projects': 'project' in low or 'portfolio' in low,
        'certifications': 'certification' in low or 'certificate' in low or 'certified' in low
    }
    return sections

def find_skills(text: str):
    """Find technical and soft skills in the text"""
    low_text = text.lower()
    tokens = tokenize(text)
    
    skill_matches = {}
    for category, skills in SKILL_KEYWORDS.items():
        matches = []
        for skill in skills:
            if skill.lower() in low_text:
                matches.append(skill)
        skill_matches[category] = matches
    
    return skill_matches

def keyword_density_score(text: str):
    tokens = tokenize(text)
    total = len(tokens) or 1
    action_count = sum(1 for t in tokens if t in ACTION_VERBS)
    # score scaled 0-100, action verbs ratio weighted
    return int(round((action_count / total) * 1000)) if total else 0, action_count, total

def readability_score(text: str):
    try:
        # use textstat for Flesch Reading Ease then normalize to 0-100 (higher = easier)
        flesch = textstat.flesch_reading_ease(text)
        # Flesch range typically -100 to 121, clamp and map to 0-100
        flesch = max(min(flesch, 121), -100)
        score = int(round((flesch + 100) / 221 * 100))
        return score
    except Exception:
        return 50

def formatting_warnings(text: str, raw_pdf: str):
    warnings = []
    low = text.lower()
    if 'table' in low or '\t' in raw_pdf:
        warnings.append('Detected table-like text — tables may break ATS parsing.')
    if 'photo' in low or 'image' in low or 'picture' in low:
        warnings.append('Contains images/photos — ATS may skip them.')
    # approximate PDF XObject presence for images
    if '/XObject' in raw_pdf or '/Image' in raw_pdf:
        warnings.append('PDF appears to contain embedded objects (images).')
    return warnings

def generate_realtime_suggestions(text: str, sections: dict, action_count: int, skill_matches: dict, word_count: int):
    """Generate real-time suggestions based on current content"""
    suggestions = []
    
    # Length suggestions
    if word_count < 200:
        suggestions.append("📝 Your resume seems short. Aim for 300-600 words to provide enough detail.")
    elif word_count > 800:
        suggestions.append("✂️ Consider condensing your resume. Keep it concise (300-600 words ideal).")
    
    # Section suggestions
    missing_sections = []
    if not sections['contact']:
        missing_sections.append("contact information")
    if not sections['experience']:
        missing_sections.append("work experience")
    if not sections['education']:
        missing_sections.append("education")
    if not sections['skills']:
        missing_sections.append("skills section")
    
    if missing_sections:
        suggestions.append(f"🔍 Add these essential sections: {', '.join(missing_sections)}")
    
    # Action verbs
    if action_count == 0:
        suggestions.append("💪 Start bullet points with strong action verbs (managed, developed, created)")
    elif action_count < 5:
        suggestions.append("💪 Use more action verbs to make your achievements stand out")
    
    # Skills suggestions
    total_skills = sum(len(skills) for skills in skill_matches.values())
    if total_skills < 5:
        suggestions.append("🛠️ Add more relevant technical skills to match job requirements")
    
    # Specific skill category suggestions
    if len(skill_matches.get('programming', [])) == 0 and 'developer' in text.lower():
        suggestions.append("💻 Add programming languages you know (Python, JavaScript, etc.)")
    
    if len(skill_matches.get('soft', [])) == 0:
        suggestions.append("🤝 Include soft skills like leadership, communication, teamwork")
    
    # Content quality suggestions
    if not sections['summary']:
        suggestions.append("📋 Add a professional summary to grab attention")
    
    if not sections['projects'] and 'developer' in text.lower():
        suggestions.append("🚀 Include a projects section to showcase your work")
    
    # Format suggestions
    if text.count('\n') < 10:
        suggestions.append("📐 Use bullet points and proper formatting for better readability")
    
    return suggestions

@app.post('/analyze_realtime')
async def analyze_realtime(request: RealTimeRequest):
    """Real-time analysis endpoint that provides instant feedback"""
    try:
        text = request.text
        
        if not text.strip():
            return RealTimeAnalysis(
                live_score=0,
                suggestions=["Start typing your resume content to get real-time feedback!"],
                sections_found={},
                action_verb_count=0,
                word_count=0,
                skill_matches={}
            )
        
        sections = detect_sections(text)
        tokens = tokenize(text)
        action_count = sum(1 for token in tokens if token in ACTION_VERBS)
        skill_matches = find_skills(text)
        word_count = len(tokens)
        
        # Calculate live score (simplified)
        section_score = (sum(sections.values()) / len(sections)) * 40
        action_score = min(action_count * 5, 30)  # Max 30 points for action verbs
        length_score = min(word_count / 10, 20) if word_count <= 600 else max(20 - (word_count - 600) / 50, 5)
        skill_score = min(sum(len(skills) for skills in skill_matches.values()) * 2, 10)
        
        live_score = int(section_score + action_score + length_score + skill_score)
        live_score = max(0, min(100, live_score))
        
        suggestions = generate_realtime_suggestions(text, sections, action_count, skill_matches, word_count)
        
        return RealTimeAnalysis(
            live_score=live_score,
            suggestions=suggestions,
            sections_found=sections,
            action_verb_count=action_count,
            word_count=word_count,
            skill_matches=skill_matches
        )
        
    except Exception as e:
        return RealTimeAnalysis(
            live_score=0,
            suggestions=[f"Error analyzing content: {str(e)}"],
            sections_found={},
            action_verb_count=0,
            word_count=0,
            skill_matches={}
        )

@app.post('/analyze_resume')
async def analyze_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()
        filename = file.filename.lower()
        if filename.endswith('.pdf'):
            text, raw = extract_text_from_pdf(content)
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            text, raw = extract_text_from_docx(content)
        else:
            try:
                text = content.decode('utf-8', errors='ignore')
                raw = text
            except:
                text = ''
                raw = ''

        if not text.strip():
            raise HTTPException(status_code=400, detail='Could not extract text from resume.')

        sections = detect_sections(text)
        kw_score, action_count, total_tokens = keyword_density_score(text)
        read_score = readability_score(text)
        warnings = formatting_warnings(text, raw)
        skill_matches = find_skills(text)

        # combine into final score (weights)
        overall = int(round(0.4 * kw_score + 0.25 * read_score + 0.25 * (sum(sections.values())/len(sections)*100) + 0.1 * min(sum(len(skills) for skills in skill_matches.values()) * 2, 100)))
        overall = max(0, min(100, overall))

        suggestions = []
        if not sections['contact']:
            suggestions.append('Add contact details (email and phone) in the header.')
        if not sections['skills']:
            suggestions.append('Add a Skills section with bullet points listing technical skills.')
        if not sections['experience']:
            suggestions.append('Include a clear Experience/Work Experience section with company names and dates.')
        if not sections['education']:
            suggestions.append('Add an Education section with degree and institution.')
        if action_count < 3:
            suggestions.append('Use more action verbs (managed, led, developed) to describe achievements.')
        if read_score < 40:
            suggestions.append('Make sentences shorter and simpler to improve readability.')
        
        # Add skill-based suggestions
        total_skills = sum(len(skills) for skills in skill_matches.values())
        if total_skills < 8:
            suggestions.append('Include more relevant technical and soft skills.')
            
        suggestions.extend(warnings)

        return {
            'score': overall,
            'sections': sections,
            'action_verb_count': action_count,
            'token_count': total_tokens,
            'readability_score': read_score,
            'skill_matches': skill_matches,
            'suggestions': suggestions
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))