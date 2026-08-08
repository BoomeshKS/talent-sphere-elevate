import re
import PyPDF2
import docx
import pdfplumber
from io import BytesIO

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
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
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = docx.Document(file)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except:
        text = ""
    return text

def extract_text_from_file(file):
    """Extract text from uploaded resume file"""
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

def extract_skills(text):
    """Extract skills from resume text using simple pattern matching"""
    skills = []
    
    skills_db = [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 
        'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'perl', 'r', 'matlab',
        'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django',
        'flask', 'spring', 'asp.net', 'jquery', 'bootstrap', 'tailwind',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'cassandra', 'dynamodb', 'oracle', 'sqlite', 'firebase',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
        'github', 'gitlab', 'bitbucket', 'terraform', 'ansible', 'puppet',
        'chef', 'prometheus', 'grafana', 'elk', 'splunk',
        'machine learning', 'deep learning', 'nlp', 'natural language processing',
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
        'matplotlib', 'seaborn', 'jupyter', 'hadoop', 'spark', 'kafka',
        'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd', 'invision',
        'after effects', 'premiere pro', 'blender', 'autocad',
        'agile', 'scrum', 'kanban', 'jira', 'confluence', 'leadership',
        'communication', 'problem solving', 'teamwork', 'critical thinking',
        'creativity', 'time management', 'project management', 'organization',
        'sales', 'marketing', 'finance', 'accounting', 'hr', 'recruitment',
        'copywriting', 'content writing', 'seo', 'sem', 'social media',
        'google analytics', 'adwords', 'hubspot', 'salesforce',
        'rest api', 'graphql', 'soap', 'microservices', 'linux', 'unix',
        'windows', 'macos', 'ios', 'android', 'react native', 'flutter',
        'ux design', 'ui design', 'product design', 'graphic design',
        'frontend', 'backend', 'full stack', 'mobile development'
    ]
    
    text_lower = text.lower()
    
    for skill in skills_db:
        if skill in text_lower:
            skills.append(skill)
    
    return list(set(skills))

def parse_resume(file):
    """Parse resume and extract only skills"""
    text = extract_text_from_file(file)
    
    if not text:
        return {
            'text': '',
            'skills': [],
            'success': False
        }
    
    skills = extract_skills(text)
    
    return {
        'text': text,
        'skills': skills,
        'success': True
    }