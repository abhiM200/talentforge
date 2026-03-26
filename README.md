# ⚒ TalentForge — Forging Careers with AI

> **AI-Powered Resume Analyzer & Job Matcher Platform**

**Developed by:**
Abhishek Kumar Mishra
Priyanshu shekhar
Altamsh mallick
**Version:** 1.0.0  
**Tech Stack:** Python · Flask · spaCy · SQLite · HTML/CSS/JS

---

## 🚀 Overview

TalentForge is a production-ready web application that helps job seekers optimize their resumes, calculate ATS compatibility scores, and discover suitable career opportunities — all powered by AI and NLP.

### Core Features

| Feature | Description |
|---------|-------------|
| 📄 **Resume Upload** | Accepts PDF and DOCX files up to 16MB |
| 🧠 **Resume Parsing** | Extracts skills, education, experience using pattern matching + spaCy |
| 📊 **ATS Score Checker** | Compares resume vs job description, generates 0–100 score |
| 🔍 **Keyword Analysis** | Highlights matched and missing keywords |
| 💡 **AI Suggestions** | Action verb improvements, skill gap analysis, formatting tips |
| 💼 **Job Role Matching** | Matches skills to 15+ predefined job roles with % scores |
| 🗄️ **Data Storage** | Stores all analysis results in SQLite |
| 📧 **Email Report** | Sends beautifully formatted HTML report via Gmail SMTP |

---

## 📁 Project Structure

```
talentforge/
├── app.py                    # Flask application & routes
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── talentforge.log           # Application logs (auto-created)
├── talentforge.db            # SQLite database (auto-created)
│
├── templates/
│   └── index.html            # Full-stack SPA frontend
│
├── static/
│   ├── css/                  # Additional stylesheets
│   ├── js/                   # Additional scripts
│   └── img/                  # Images & assets
│
├── utils/
│   ├── __init__.py
│   ├── file_extractor.py     # PDF/DOCX text extraction
│   ├── resume_parser.py      # NLP-based resume parsing
│   ├── ats_scorer.py         # ATS score calculation
│   ├── ai_suggestions.py     # AI improvement suggestions
│   ├── job_matcher.py        # Job role matching
│   └── email_sender.py       # SMTP email report sender
│
├── models/
│   ├── __init__.py
│   └── database.py           # SQLite ORM / data access
│
├── data/
│   └── job_roles.json        # Job roles dataset (15+ roles)
│
└── uploads/                  # Temporary upload directory
```

---

## ⚙️ Installation & Setup

### 1. Clone / Download the Project

```bash
cd talentforge
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate (Linux/Mac):
source venv/bin/activate

# Activate (Windows):
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your values (see Email Setup section below).

### 5. Run the Application

```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 📧 Email Feature — Gmail SMTP Setup

TalentForge sends beautifully formatted HTML email reports using Python's `smtplib` and Gmail SMTP.

### Setting Up Gmail App Password

> ⚠️ Regular Gmail passwords won't work. You need a **Gmail App Password**.

**Step 1:** Enable 2-Factor Authentication on your Google account  
→ https://myaccount.google.com/security

**Step 2:** Generate an App Password  
→ Google Account → Security → 2-Step Verification → App Passwords  
→ Select app: **Mail** | Select device: **Other (Custom name)** → "TalentForge"  
→ Copy the generated 16-character password

**Step 3:** Update your `.env` file:

```env
SMTP_USER=your.gmail@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop   # Your 16-char App Password (spaces OK)
```

### Email Report Contents

The HTML email report includes:
- 🎯 ATS Score (large, color-coded)
- 🛠 All detected skills
- ✅ Matched keywords / ❌ Missing keywords  
- 💼 Top 3 job role matches with salary ranges
- 💡 AI improvement suggestions with impact levels
- 📊 Component score breakdown

### Testing Email Locally

You can test using **Mailtrap** (free email sandbox) by changing SMTP settings:

```env
SMTP_USER=your-mailtrap-user
SMTP_PASSWORD=your-mailtrap-pass
```

And in `utils/email_sender.py`, change:
```python
smtp_host="sandbox.smtp.mailtrap.io"
smtp_port=2525
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Landing page |
| `POST` | `/analyze` | Upload resume + JD → Full analysis JSON |
| `POST` | `/send-report` | Send report to email |
| `GET` | `/history` | Get recent analysis history |
| `GET` | `/health` | Health check |

### POST /analyze

**Request:** `multipart/form-data`
- `resume` — PDF or DOCX file
- `job_description` — Target job description text

**Response:**
```json
{
  "filename": "resume.pdf",
  "parsed_resume": {
    "name": "John Doe",
    "skills": ["python", "react", "aws"],
    "education": [...],
    "experience": [...]
  },
  "ats_score": {
    "total_score": 72.5,
    "tier": "Good",
    "matched_keywords": ["python", "docker"],
    "missing_keywords": ["kubernetes", "terraform"]
  },
  "job_matches": [...],
  "suggestions": {...}
}
```

---

## 🏗️ ATS Scoring Algorithm

| Component | Weight | Description |
|-----------|--------|-------------|
| Keyword Match | 40% | Resume ↔ Job description keyword overlap |
| Experience Indicators | 20% | Quantified achievements, dates, titles |
| Formatting Quality | 10% | Sections, word count, structure |
| Action Verbs | 10% | Strong power words usage |
| Education | 15% | Education section presence |
| Contact Info | 5% | Email, phone, LinkedIn presence |

**Score Tiers:**
- 80–100: 🟢 **Excellent** — Highly ATS-optimized
- 65–79: 🔵 **Good** — Performs well, minor improvements
- 50–64: 🟡 **Average** — Moderate improvements needed
- 0–49: 🔴 **Needs Work** — Significant improvements required

---

## 🧠 NLP & Parsing

- **Skills extraction:** Pattern matching against a database of 100+ skills across 7 categories
- **Experience detection:** Year ranges, action verbs, quantified metrics
- **Education parsing:** Degree keywords, institution names
- **Contact extraction:** Regex for email, phone, LinkedIn, GitHub

---

## 🐛 Troubleshooting

**PDF text extraction fails:**  
→ Ensure PDF is not a scanned image (image-based PDFs can't be parsed)

**Email authentication error:**  
→ Check Gmail App Password is correct (not your regular Gmail password)  
→ Ensure 2FA is enabled on Google account

**Import errors:**  
→ Ensure virtual environment is activated  
→ Run `pip install -r requirements.txt` again

**Database errors:**  
→ Delete `talentforge.db` and restart (it will be recreated)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit changes
4. Open a Pull Request

---

## 📄 License

MIT License — Free to use and modify.

---
| TalentForge © 2024*
