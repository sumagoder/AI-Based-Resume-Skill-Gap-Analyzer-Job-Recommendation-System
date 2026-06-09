import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

jobs = pd.read_csv("dataset/jobs.csv")
skills_df = pd.read_csv("dataset/skills.csv")

skills_list = skills_df['skill_name'].dropna().str.lower().tolist()


def extract_skills(text):
    return list(set([s for s in skills_list if re.search(r'\b'+re.escape(s)+r'\b', text)]))


def match_top_jobs(skills_text, resume_skills):
    job_texts = jobs['skills'].astype(str).tolist()

    vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words='english')
    vectors = vectorizer.fit_transform(job_texts + [skills_text])

    similarity = cosine_similarity(vectors[-1], vectors[:-1])[0]

    results = []

    for i, row in jobs.iterrows():
        job_skills = [s.strip().lower() for s in row['skills'].split(',')]

        overlap = len(set(job_skills) & set(resume_skills))
        overlap_score = overlap / len(job_skills)

        final_score = (0.4 * similarity[i]) + (0.6 * overlap_score)

        results.append((row['job_title'], round(final_score*100,2)))

    return sorted(results, key=lambda x: x[1], reverse=True)[:3]


def skill_gap(resume_skills, job_role):
    row = jobs[jobs['job_title'] == job_role]
    if row.empty:
        return []

    job_skills = [s.strip().lower() for s in row.iloc[0]['skills'].split(',')]
    return [s for s in job_skills if s not in resume_skills]


# 🔥 ATS SCORE
def calculate_ats_score(text, resume_skills, best_job):
    row = jobs[jobs['job_title'] == best_job]
    if row.empty:
        return 0

    job_skills = [s.strip().lower() for s in row.iloc[0]['skills'].split(',')]

    skill_score = (len(set(job_skills)&set(resume_skills))/len(job_skills))*40
    keyword_score = (sum(1 for s in job_skills if s in text)/len(job_skills))*20

    word_count = len(text.split())
    length_score = 15 if 300<=word_count<=800 else 8

    sections = ["education","experience","skills","projects"]
    section_score = (sum(1 for s in sections if s in text)/4)*15

    readability = 10 if len(text)>100 else 5

    return round(skill_score+keyword_score+length_score+section_score+readability,2)


def career_suggestions(top_jobs):
    return [j for j,_ in top_jobs]


def learning_recommendations(missing):
    return {s: f"Learn {s} via courses/projects" for s in missing}