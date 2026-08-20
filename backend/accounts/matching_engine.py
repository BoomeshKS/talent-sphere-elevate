import re
from .models import Job, JobApplication

def calculate_match_score(application):
    job = application.job
    candidate = application.candidate
    profile = candidate.profile
    
    candidate_skills = application.parsed_skills or profile.skills or ""
    candidate_experience = application.experience_years or profile.experience_years or 0
    job_skills = job.required_skills or ""
    job_requirements = job.requirements or ""
    job_description = job.description or ""
    
    skill_score = calculate_skill_match(candidate_skills, job_skills, job_requirements, job_description)
    experience_score = calculate_experience_match(candidate_experience, job.experience_level)
    
    overall_score = (
        skill_score * 0.60 +
        experience_score * 0.40 
    )
    
    overall_score = int(round(overall_score))
    
    return {
        'overall_score': min(overall_score, 100),
        'skill_score': int(round(skill_score)),
        'experience_score': int(round(experience_score)),
        'keyword_score': int(round(skill_score))
    }


def calculate_skill_match(candidate_skills, job_skills, job_requirements, job_description):
    if not candidate_skills:
        return 0
    
    candidate_list = [s.strip().lower() for s in candidate_skills.split(',') if s.strip()]
    
    if not candidate_list:
        return 0
    
    job_skill_list = []
    
    if job_skills:
        job_skill_list.extend([s.strip().lower() for s in job_skills.split(',') if s.strip()])
    
    if job_requirements:
        extracted = extract_keywords(job_requirements)
        job_skill_list.extend(extracted)
    
    if job_description:
        extracted = extract_keywords(job_description)
        job_skill_list.extend(extracted)
    
    job_skill_list = list(set(job_skill_list))
    
    if not job_skill_list:
        return 50
    
    matched_skills = []
    missing_skills = []
    
    for skill in job_skill_list:
        found = False
        for candidate_skill in candidate_list:
            if skill in candidate_skill or candidate_skill in skill:
                matched_skills.append(skill)
                found = True
                break
        if not found:
            missing_skills.append(skill)
    
    match_percentage = (len(matched_skills) / len(job_skill_list)) * 100
    
    return min(match_percentage, 100)

def extract_keywords(text):
    stopwords = {
        'a', 'an', 'the', 'of', 'for', 'with', 'to', 'from', 'by',
        'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'than', 'then',
        'into', 'upon', 'about', 'after', 'before', 'between', 'under', 'over'
    }
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    keywords = [word for word in words if word not in stopwords]
    
    from collections import Counter
    word_freq = Counter(keywords)
    top_keywords = [word for word, count in word_freq.most_common(30)]
    
    return top_keywords

def calculate_experience_match(candidate_years, job_level):
    level_requirements = {
        'entry': (0, 1),
        'mid': (2, 4),
        'senior': (5, 7),
        'lead': (8, 10),
        'executive': (11, 20)
    }
    
    if job_level not in level_requirements:
        return 50
    
    min_exp, max_exp = level_requirements[job_level]
    
    if candidate_years <= 0:
        return 0
    
    if candidate_years >= min_exp and candidate_years <= max_exp:
        return 100
    elif candidate_years < min_exp:
        return (candidate_years / min_exp) * 100 if min_exp > 0 else 0
    else:
        if candidate_years <= max_exp * 1.5:
            return 100
        else:
            return 80

def get_experience_range(job_level):
    level_requirements = {
        'entry': '0-1 years',
        'mid': '2-4 years',
        'senior': '5-7 years',
        'lead': '8-10 years',
        'executive': '11+ years'
    }
    return level_requirements.get(job_level, 'Not specified')

def get_matched_and_missing_skills(candidate_skills, job):
    if not candidate_skills:
        return [], []
    
    candidate_list = [s.strip().lower() for s in candidate_skills.split(',') if s.strip()]
    
    if not candidate_list:
        return [], []
    
    job_skill_list = []
    
    if job.required_skills:
        job_skill_list.extend([s.strip().lower() for s in job.required_skills.split(',') if s.strip()])
    
    if job.requirements:
        extracted = extract_keywords(job.requirements)
        job_skill_list.extend(extracted)
    
    if job.description:
        extracted = extract_keywords(job.description)
        job_skill_list.extend(extracted)
    
    job_skill_list = list(set(job_skill_list))[:20]
    
    if not job_skill_list:
        return [], []
    
    matched = []
    missing = []
    
    for skill in job_skill_list:
        found = False
        for candidate_skill in candidate_list:
            if skill in candidate_skill or candidate_skill in skill:
                matched.append(skill)
                found = True
                break
        if not found:
            missing.append(skill)
    
    return matched, missing

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