import re
import PyPDF2
import docx
import pdfplumber
from io import BytesIO

def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        try:
            file.seek(0)
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        except:
            text = ""
    return text

def extract_text_from_docx(file):
    text = ""
    try:
        doc = docx.Document(file)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except:
        text = ""
    return text

def extract_text_from_file(file):
    file_name = file.name.lower()
    text = ""
    
    try:
        if file_name.endswith('.pdf'):
            text = extract_text_from_pdf(file)
        elif file_name.endswith('.docx'):
            text = extract_text_from_docx(file)
        elif file_name.endswith('.doc'):
            try:
                text = file.read().decode('utf-8', errors='ignore')
            except:
                text = ""
        elif file_name.endswith('.txt'):
            text = file.read().decode('utf-8', errors='ignore')
        else:
            text = ""
    except Exception as e:
        print(f"Error extracting text: {e}")
        text = ""
    
    return text

def extract_experience_years(text):
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience',
        r'experience\s*(?:of)?\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)',
        r'(\d+)\s*\+\s*(?:years?|yrs?)',
        r'(\d+\.?\d*)\s*(?:years?|yrs?)\s*experience',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(float(match.group(1)))
            except:
                pass
    return 0

def extract_skills(text):
    common_skills = [
        'python', 'java', 'javascript', 'html', 'css', 'sql', 'nosql',
        'django', 'flask', 'react', 'angular', 'vue', 'node', 'express',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
        'agile', 'scrum', 'project management', 'leadership', 'communication',
        'problem solving', 'teamwork', 'critical thinking', 'creativity',
        'data analysis', 'machine learning', 'deep learning', 'nlp', 'ai',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
        'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'typescript',
        'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'rest api', 'graphql', 'soap', 'microservices', 'cloud computing',
        'devops', 'ci/cd', 'linux', 'unix', 'windows', 'macos',
        'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd',
        'sales', 'marketing', 'finance', 'accounting', 'hr', 'recruitment',
        'copywriting', 'content writing', 'seo', 'sem', 'social media',
        'ui design', 'ux design', 'product design', 'graphic design',
        'frontend', 'backend', 'full stack', 'mobile development'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))

def extract_education(text):
    education_keywords = [
        'bachelor', 'master', 'phd', 'b.sc', 'm.sc', 'b.tech', 'm.tech',
        'be', 'me', 'b.com', 'm.com', 'mba', 'bca', 'mca', 'ba', 'ma',
        'bs', 'ms', 'ph.d', 'doctorate', 'degree', 'university', 'college'
    ]
    
    education_lines = []
    lines = text.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in education_keywords):
            education_lines.append(line.strip())
    
    return '\n'.join(education_lines[:5])

def parse_resume(file):

    text = extract_text_from_file(file)
    
    if not text:
        return {
            'text': '',
            'skills': [],
            'experience_years': 0,
            'education': '',
            'success': False
        }
    
    skills = extract_skills(text)
    experience_years = extract_experience_years(text)
    education = extract_education(text)
    
    return {
        'text': text,
        'skills': skills,
        'experience_years': experience_years,
        'education': education,
        'success': True
    }