from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io, re
from PyPDF2 import PdfReader
import docx
import textstat

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
    'supervised','trained','automated','streamlined'
}

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
        'contact': bool(re.search(r'email|@|phone|tel\b|contact', low)),
        'summary': 'summary' in low or 'objective' in low,
        'skills': 'skill' in low or 'technical skills' in low,
        'experience': 'experience' in low or 'work experience' in low or 'professional experience' in low,
        'education': 'education' in low or 'degree' in low or 'bachelor' in low or 'master' in low
    }
    return sections

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

        # combine into final score (weights)
        overall = int(round(0.5 * kw_score + 0.3 * read_score + 0.2 * (sum(sections.values())/len(sections)*100)))
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
        suggestions.extend(warnings)

        return {
            'score': overall,
            'sections': sections,
            'action_verb_count': action_count,
            'token_count': total_tokens,
            'readability_score': read_score,
            'suggestions': suggestions
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
