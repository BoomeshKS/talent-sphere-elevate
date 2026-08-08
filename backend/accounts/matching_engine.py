import re
from .models import Job, JobApplication

def calculate_match_score(application):
    job = application.job
    candidate = application.candidate
    
    candidate_skills = application.parsed_skills or ""
    candidate_experience = application.experience_years or 0
    job_requirements = job.requirements or ""
    job_skills = job.required_skills or ""
    
    skill_score = calculate_skill_match(candidate_skills, job_skills)
    
    experience_score = calculate_experience_match(candidate_experience, job.experience_level)
    
    keyword_score = calculate_keyword_match(application.resume_text or "", job_requirements)
    
    overall_score = (
        skill_score * 0.40 +
        experience_score * 0.35 +
        keyword_score * 0.25
    )
    
    overall_score = int(round(overall_score))
    
    return {
        'overall_score': min(overall_score, 100),
        'skill_score': int(round(skill_score)),
        'experience_score': int(round(experience_score)),
        'keyword_score': int(round(keyword_score))
    }

def calculate_skill_match(candidate_skills, job_skills):
    if not candidate_skills or not job_skills:
        return 0
    
    candidate_list = [s.strip().lower() for s in candidate_skills.split(',') if s.strip()]
    job_list = [s.strip().lower() for s in job_skills.split(',') if s.strip()]
    
    if not job_list:
        return 50  
    
    matched_skills = set(candidate_list) & set(job_list)
    
    match_percentage = (len(matched_skills) / len(job_list)) * 100
    
    return min(match_percentage, 100)

def calculate_experience_match(candidate_years, job_level):

    level_requirements = {
        'entry': (0, 2),
        'mid': (2, 5),
        'senior': (5, 8),
        'lead': (8, 12),
        'executive': (12, 20)
    }
    
    if job_level not in level_requirements:
        return 50
    
    min_exp, max_exp = level_requirements[job_level]
    
    if candidate_years <= 0:
        return 0
    
    if candidate_years >= min_exp and candidate_years <= max_exp:
        return 100
    elif candidate_years < min_exp:
        return (candidate_years / min_exp) * 100
    else:
        if candidate_years <= max_exp * 1.5:
            return 100
        else:
            return 80

def calculate_keyword_match(candidate_text, job_requirements):
    if not candidate_text or not job_requirements:
        return 0
    
    job_keywords = extract_keywords(job_requirements)
    
    if not job_keywords:
        return 50
    
    candidate_text_lower = candidate_text.lower()
    matched_count = 0
    
    for keyword in job_keywords:
        if keyword.lower() in candidate_text_lower:
            matched_count += 1
    
    match_percentage = (matched_count / len(job_keywords)) * 100
    
    return min(match_percentage, 100)

def extract_keywords(text):
    stopwords = {
        'a', 'an', 'the', 'of', 'for', 'with', 'to', 'from', 'by',
        'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall'
    }
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    keywords = [word for word in words if word not in stopwords]
    
    from collections import Counter
    word_freq = Counter(keywords)
    top_keywords = [word for word, count in word_freq.most_common(20)]
    
    return top_keywords

def rank_candidates(job_id):
    applications = JobApplication.objects.filter(job_id=job_id)
    
    ranked_applications = []
    
    for application in applications:
        scores = calculate_match_score(application)
        
        application.match_score = scores['overall_score']
        application.skill_match_score = scores['skill_score']
        application.experience_match_score = scores['experience_score']
        application.ai_recommendation = generate_recommendation(scores)
        application.save()
        
        ranked_applications.append({
            'application': application,
            'scores': scores
        })
    
    ranked_applications.sort(key=lambda x: x['scores']['overall_score'], reverse=True)
    
    return ranked_applications

def generate_recommendation(scores):
    overall = scores['overall_score']
    skill = scores['skill_score']
    experience = scores['experience_score']
    
    if overall >= 85:
        return "Highly Recommended - Excellent match for this position"
    elif overall >= 70:
        return "Recommended - Good match, suitable for this position"
    elif overall >= 55:
        return "Potentially Suitable - Consider for interview"
    elif overall >= 40:
        return "Average Match - May need additional training"
    else:
        return "Not Recommended - Low match score"

def auto_rank_and_update(job_id):
    ranked = rank_candidates(job_id)
    
    for index, item in enumerate(ranked, 1):
        item['application'].notes = f"AI Rank: #{index} | Score: {item['scores']['overall_score']}%"
        item['application'].save()
    
    return ranked