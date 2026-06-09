from flask import Flask, render_template, request
import os

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import requests

from utils import extract_text, preprocess
from model import (
    extract_skills,
    match_top_jobs,
    skill_gap,
    calculate_ats_score,
    career_suggestions,
    learning_recommendations
)

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("static", exist_ok=True)


# 🔥 REAL JOB API
def fetch_jobs(role):
    APP_ID = "your_app_id"
    APP_KEY = "your_app_key"

    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={APP_ID}&app_key={APP_KEY}&what={role}"

    try:
        res = requests.get(url)
        data = res.json()

        jobs = []
        for job in data.get("results", [])[:5]:
            jobs.append({
                "title": job.get("title"),
                "company": job.get("company", {}).get("display_name"),
                "location": job.get("location", {}).get("display_name"),
                "url": job.get("redirect_url")
            })

        return jobs
    except:
        return []


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":

        file = request.files["resume"]
        if file.filename == "":
            return render_template("index.html", error="Upload file")

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        text = extract_text(path)
        clean = preprocess(text)

        skills = extract_skills(clean)
        if not skills:
            return render_template("index.html", error="No skills detected")

        skills_text = " ".join(skills)

        top_jobs = match_top_jobs(skills_text, skills)
        best_job = top_jobs[0][0]

        missing = skill_gap(skills, best_job)
        matched = list(set(skills) - set(missing))

        # 🔥 ATS SCORE
        score = calculate_ats_score(clean, skills, best_job)

        careers = career_suggestions(top_jobs)
        learning = learning_recommendations(missing)

        # GRAPH
        names = [j for j, s in top_jobs]
        scores = [s for j, s in top_jobs]

        plt.figure()
        plt.bar(names, scores)
        plt.xlabel("Jobs")
        plt.ylabel("Score")
        plt.title("Top Job Matches")

        graph_path = "static/graph.png"
        plt.savefig(graph_path)
        plt.close()

        # 🔥 REAL JOBS
        real_jobs = fetch_jobs(best_job)

        return render_template("index.html",
                               skills=skills,
                               top_jobs=top_jobs,
                               missing=missing,
                               matched=matched,
                               score=score,
                               careers=careers,
                               learning=learning,
                               graph=graph_path,
                               real_jobs=real_jobs)

    return render_template("index.html")


@app.route("/download")
def download():
    file_path = "static/report.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("AI Resume Analysis Report", styles['Title']))
    content.append(Spacer(1, 10))
    content.append(Paragraph("Generated using ATS-based Resume Analyzer", styles['Normal']))

    doc.build(content)

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)