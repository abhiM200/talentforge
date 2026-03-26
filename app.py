"""
TalentForge - AI-Powered Resume Analyzer & Job Matcher
Main Flask Application
Developed by: Abhishek Kumar Mishra
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('talentforge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'talentforge-secret-key-2024')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import utilities
from utils.file_extractor import extract_text
from utils.resume_parser import parse_resume
from utils.ats_scorer import calculate_ats_score
from utils.ai_suggestions import generate_suggestions
from utils.job_matcher import match_jobs
from utils.email_sender import send_report_email
from models.database import init_db, save_analysis, get_recent_analyses

# Initialize database on startup
try:
    init_db()
    logger.info("TalentForge started successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_resume():
    """
    Main endpoint: Upload resume + JD → Full analysis.
    Returns JSON with ATS score, skills, job matches, suggestions.
    """
    try:
        # Validate file upload
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PDF or DOCX.'}), 400
        
        # Get job description
        job_description = request.form.get('job_description', '').strip()
        if not job_description:
            job_description = "software engineer developer python javascript technology"
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        logger.info(f"File saved: {safe_filename}")
        
        # Extract text
        resume_text = extract_text(file_path)
        if not resume_text or len(resume_text.strip()) < 50:
            os.remove(file_path)
            return jsonify({'error': 'Could not extract text from file. Ensure it is not a scanned image.'}), 422
        
        # Parse resume
        parsed_resume = parse_resume(resume_text)
        
        # Calculate ATS score
        ats_result = calculate_ats_score(
            resume_text=resume_text,
            jd_text=job_description,
            contact_info=parsed_resume.get('contact', {})
        )
        
        # Get job recommendations
        job_matches = match_jobs(parsed_resume.get('skills', []), top_n=5)
        
        # Generate AI suggestions
        suggestions = generate_suggestions(
            resume_text=resume_text,
            skills=parsed_resume.get('skills', []),
            ats_score=ats_result.get('total_score', 0),
            missing_keywords=ats_result.get('missing_keywords', [])
        )
        
        # Compile full analysis
        analysis = {
            "filename": filename,
            "parsed_resume": parsed_resume,
            "ats_score": ats_result,
            "job_matches": job_matches,
            "suggestions": suggestions,
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Save to database
        record_id = save_analysis(filename, analysis)
        analysis['record_id'] = record_id
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except Exception:
            pass
        
        logger.info(f"Analysis complete for {filename}: ATS={ats_result.get('total_score')}%")
        return jsonify(analysis)
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/send-report', methods=['POST'])
def send_report():
    """
    Send analysis report to user's email.
    Requires SMTP credentials in environment variables.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip()
        analysis = data.get('analysis')
        
        if not email:
            return jsonify({'error': 'Email address is required'}), 400
        
        if not analysis:
            return jsonify({'error': 'No analysis data provided'}), 400
        
        # Basic email validation
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return jsonify({'error': 'Invalid email address format'}), 400
        
        # Get SMTP credentials
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        if not smtp_user or not smtp_password:
            return jsonify({
                'error': 'Email service not configured. Please set SMTP_USER and SMTP_PASSWORD in .env file.',
                'setup_hint': 'See README.md for Gmail App Password setup instructions.'
            }), 503
        
        # Send email
        result = send_report_email(
            recipient_email=email,
            analysis=analysis,
            smtp_user=smtp_user,
            smtp_password=smtp_password
        )
        
        # Update database record if email was sent
        if result['success'] and analysis.get('record_id'):
            from models.database import get_connection
            try:
                conn = get_connection()
                conn.execute(
                    'UPDATE analyses SET email_sent_to = ? WHERE id = ?',
                    (email, analysis['record_id'])
                )
                conn.commit()
                conn.close()
            except Exception:
                pass
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Email send error: {e}", exc_info=True)
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500


@app.route('/history')
def get_history():
    """Get recent analysis history."""
    try:
        analyses = get_recent_analyses(limit=10)
        return jsonify({'analyses': analyses})
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'app': 'TalentForge',
        'version': '1.0.0',
        'developer': 'Abhishek Kumar Mishra'
    })


@app.route('/admin')
def admin_dashboard():
    """Admin dashboard to view all uploads and analyses."""
    password = request.args.get('key', '')
    admin_key = os.getenv('ADMIN_KEY', 'talentforge-admin-2024')
    
    if password != admin_key:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>TalentForge Admin</title>
            <style>
                body { background: #0a0f1e; color: #e2e8f0; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .box { background: #0f1e35; padding: 40px; border-radius: 12px; text-align: center; border: 1px solid #1e3a5f; }
                h2 { color: #60a5fa; } input { padding: 10px 16px; border-radius: 6px; border: 1px solid #1e3a5f; background: #0a0f1e; color: #fff; width: 250px; margin: 10px 0; }
                button { background: #3b82f6; color: #fff; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; }
            </style>
        </head>
        <body>
            <div class="box">
                <h2>⚒ TalentForge Admin</h2>
                <p style="color:#94a3b8;">Enter admin password to continue</p>
                <form method="GET">
                    <input type="password" name="key" placeholder="Admin Password" /><br>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        ''', 401
    
    try:
        from models.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, filename, candidate_name, ats_score, ats_tier,
                   skills_count, top_job_match, email_sent_to, created_at
            FROM analyses ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        analyses = [dict(row) for row in rows]
    except Exception:
        analyses = []
    
    rows_html = ""
    for a in analyses:
        score = a.get('ats_score', 0) or 0
        score_color = "#10b981" if score >= 80 else "#3b82f6" if score >= 65 else "#f59e0b" if score >= 50 else "#ef4444"
        email_sent = a.get('email_sent_to') or '<span style="color:#64748b;">—</span>'
        rows_html += f"""<tr>
            <td style="color:#64748b;">#{a.get('id')}</td>
            <td style="color:#e2e8f0;">{a.get('candidate_name', 'Unknown')}</td>
            <td style="color:#93c5fd;">{a.get('filename', '—')}</td>
            <td><span style="color:{score_color};font-weight:bold;">{score:.0f}</span></td>
            <td><span style="background:{score_color}22;color:{score_color};padding:2px 8px;border-radius:4px;font-size:12px;">{a.get('ats_tier','—')}</span></td>
            <td style="color:#a3e635;">{a.get('skills_count', 0)}</td>
            <td style="color:#c4b5fd;">{a.get('top_job_match', '—')}</td>
            <td style="color:#67e8f9;font-size:12px;">{email_sent}</td>
            <td style="color:#64748b;font-size:12px;">{a.get('created_at','—')}</td>
        </tr>"""
    
    total = len(analyses)
    avg_score = sum(a.get('ats_score', 0) or 0 for a in analyses) / total if total > 0 else 0
    emails_sent = sum(1 for a in analyses if a.get('email_sent_to'))
    
    return f"""<!DOCTYPE html>
    <html><head><title>TalentForge Admin</title><meta charset="UTF-8">
    <style>* {{box-sizing:border-box;margin:0;padding:0;}} body{{background:#0a0f1e;color:#e2e8f0;font-family:'Segoe UI',Arial,sans-serif;}}
    .header{{background:linear-gradient(135deg,#0f2044,#1a3a6b);padding:24px 32px;display:flex;justify-content:space-between;align-items:center;}}
    .header h1{{font-size:24px;font-weight:900;color:#fff;}} .header span{{color:#93c5fd;font-size:14px;}}
    .stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:24px 32px;}}
    .stat{{background:#0f1e35;border:1px solid #1e3a5f;border-radius:10px;padding:20px;text-align:center;}}
    .stat .num{{font-size:36px;font-weight:900;}} .stat .label{{color:#64748b;font-size:13px;margin-top:4px;}}
    .table-wrap{{padding:0 32px 32px;overflow-x:auto;}}
    table{{width:100%;border-collapse:collapse;background:#0f1e35;border-radius:10px;overflow:hidden;}}
    th{{background:#1e3a5f;padding:12px 16px;text-align:left;font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;}}
    td{{padding:12px 16px;border-bottom:1px solid #1e3a5f22;font-size:14px;}} tr:hover td{{background:#1e3a5f22;}}
    .empty{{text-align:center;padding:60px;color:#64748b;}}</style></head>
    <body>
    <div class="header"><h1>⚒ TalentForge Admin</h1><span>Total Users: {total} | Abhishek Kumar Mishra</span></div>
    <div class="stats">
        <div class="stat"><div class="num" style="color:#60a5fa;">{total}</div><div class="label">Total Resumes Analyzed</div></div>
        <div class="stat"><div class="num" style="color:#10b981;">{avg_score:.1f}</div><div class="label">Average ATS Score</div></div>
        <div class="stat"><div class="num" style="color:#a78bfa;">{emails_sent}</div><div class="label">Email Reports Sent</div></div>
    </div>
    <div class="table-wrap"><table>
        <thead><tr><th>ID</th><th>Candidate</th><th>File</th><th>Score</th><th>Tier</th><th>Skills</th><th>Top Job</th><th>Email Sent To</th><th>Date & Time</th></tr></thead>
        <tbody>{rows_html if rows_html else '<tr><td colspan="9" class="empty">No analyses yet!</td></tr>'}</tbody>
    </table></div></body></html>"""


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    logger.info(f"Starting TalentForge on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
