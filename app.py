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
