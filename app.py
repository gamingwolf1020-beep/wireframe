from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import secrets
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-this-in-production'

# --- MongoDB Setup ---
MONGO_URI = os.getenv('MONGO_URI')
client = None
db = None

if not MONGO_URI:
    print("WARNING: MONGO_URI environment variable not set!")
else:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # 5s timeout
        db = client['freelance_db']
        # Trigger a connection check
        client.admin.command('ping')
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        db = None

# --- Helper Functions (Refactored for MongoDB) ---
def get_user_by_email(email):
    if db is None: return None
    return db.users.find_one({'email': email})

def get_user_by_id(user_id):
    if db is None: return None
    return db.users.find_one({'id': user_id})

# --- Context Processor ---
@app.context_processor
def inject_user():
    if 'user_id' in session:
        return {'current_user': get_user_by_id(session['user_id'])}
    return {'current_user': None}

# --- Global Session Check ---
@app.before_request
def check_valid_user():
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please login again.')

# --- Routes ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if db is None:
            flash('Database connection unavailable. Please contact support.')
            return redirect(url_for('register'))
            
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'] # In a real app, hash this!
        role = request.form['role']
        
        if get_user_by_email(email):
            flash('Email already registered')
            return redirect(url_for('register'))
            
        new_user = {
            'id': secrets.token_hex(8),
            'name': name,
            'email': email,
            'password': password,
            'role': role,
            'joined_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            db.users.insert_one(new_user)
            session['user_id'] = new_user['id']
            flash('Welcome! Account created successfully.')
            return redirect_to_dashboard(role)
        except Exception as e:
            flash(f'Registration failed: {str(e)}')
            return redirect(url_for('register'))
        
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if db is None:
            flash('Database connection unavailable. Please try again later.')
            return render_template('auth/login.html')
            
        email = request.form['email']
        password = request.form['password']
        
        user = get_user_by_email(email)
        if user and user['password'] == password:
            session['user_id'] = user['id']
            return redirect_to_dashboard(user['role'])
            
        flash('Invalid email or password')
        
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

def redirect_to_dashboard(role):
    if role == 'client':
        return redirect(url_for('client_dashboard'))
    return redirect(url_for('freelancer_dashboard'))

@app.route('/dashboard/client')
def client_dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Get user jobs
    my_jobs = list(db.jobs.find({'client_id': session['user_id']}))
    
    return render_template('dashboard/client_dashboard.html', my_jobs=my_jobs)

@app.route('/dashboard/freelancer')
def freelancer_dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Get proposals sent by this freelancer
    my_proposals = list(db.proposals.find({'freelancer_id': session['user_id']}))
    
    for p in my_proposals:
        # Find job title for each proposal
        job = db.jobs.find_one({'id': p['job_id']})
        p['job_title'] = job['title'] if job else "Unknown Job"
            
    return render_template('dashboard/freelancer_dashboard.html', my_proposals=my_proposals)

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/jobs')
def browse_jobs():
    query = {}
    category_filter = request.args.get('category')
    if category_filter:
        query['category'] = category_filter
        
    jobs = list(db.jobs.find(query))
        
    return render_template('jobs/browse_jobs.html', jobs=jobs, current_category=category_filter)

@app.route('/jobs/post', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))
        
    if user['role'] != 'client':
        flash('Only clients can post jobs.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        if db is None:
            flash('Database connection unavailable.')
            return redirect(url_for('home'))
            
        new_job = {
            'id': secrets.token_hex(8),
            'client_id': session['user_id'],
            'client_name': user['name'],
            'title': request.form['title'],
            'category': request.form['category'],
            'budget': request.form['budget'],
            'deadline': request.form['deadline'],
            'description': request.form['description'],
            'posted_at': datetime.now().strftime("%Y-%m-%d")
        }
        try:
            db.jobs.insert_one(new_job)
            flash('Job posted successfully!')
        except Exception as e:
            flash(f'Error posting job: {str(e)}')
            
        return redirect(url_for('client_dashboard'))
        
    return render_template('jobs/post_job.html')

@app.route('/jobs/<job_id>')
def view_job(job_id):
    job = db.jobs.find_one({'id': job_id})
    if not job:
        flash('Job not found')
        return redirect(url_for('browse_jobs'))
        
    # Get proposals if current user is the client
    proposals = []
    if 'user_id' in session and session['user_id'] == job['client_id']:
        proposals = list(db.proposals.find({'job_id': job_id}))
        
    return render_template('jobs/job_details.html', job=job, proposals=proposals)

@app.route('/jobs/<job_id>/apply', methods=['POST'])
def submit_proposal(job_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if user['role'] != 'freelancer':
        flash('Only freelancers can submit proposals.')
        return redirect(url_for('view_job', job_id=job_id))
        
    # Check if already applied
    existing = db.proposals.find_one({'job_id': job_id, 'freelancer_id': session['user_id']})
    if existing:
        flash('You have already applied to this job.')
        return redirect(url_for('view_job', job_id=job_id))
        
    new_proposal = {
        'id': secrets.token_hex(8),
        'job_id': job_id,
        'freelancer_id': session['user_id'],
        'freelancer_name': user['name'],
        'bid_amount': request.form['bid_amount'],
        'cover_letter': request.form['cover_letter'],
        'status': 'Pending',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    try:
        db.proposals.insert_one(new_proposal)
        flash('Proposal sent successfully!')
    except Exception as e:
        flash(f'Error sending proposal: {str(e)}')
        
    return redirect(url_for('freelancer_dashboard'))

@app.route('/jobs/<job_id>/delete', methods=['POST'])
def delete_job(job_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Find job
    job = db.jobs.find_one({'id': job_id})
    
    if not job:
        flash('Job not found')
        return redirect(url_for('client_dashboard'))
        
    # Check ownership
    if job['client_id'] != session['user_id']:
        flash('Unauthorized action')
        return redirect(url_for('client_dashboard'))
        
    # Remove job
    try:
        db.jobs.delete_one({'id': job_id})
        # Remove associated proposals
        db.proposals.delete_many({'job_id': job_id})
        flash('Job deleted successfully')
    except Exception as e:
        flash(f'Error deleting job: {str(e)}')
    
    return redirect(url_for('client_dashboard'))

@app.route('/proposals/<proposal_id>/delete', methods=['POST'])
def delete_proposal(proposal_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Find proposal
    proposal = db.proposals.find_one({'id': proposal_id})
    
    if not proposal:
        flash('Proposal not found')
        return redirect(url_for('freelancer_dashboard'))
        
    # Check ownership
    if proposal['freelancer_id'] != session['user_id']:
        flash('Unauthorized action')
        return redirect(url_for('freelancer_dashboard'))
        
    # Remove proposal
    try:
        db.proposals.delete_one({'id': proposal_id})
        flash('Proposal deleted successfully')
    except Exception as e:
        flash(f'Error deleting proposal: {str(e)}')
        
    return redirect(url_for('freelancer_dashboard'))

@app.route('/debug-db')
def debug_db():
    status = {
        "mongo_uri_set": bool(MONGO_URI),
        "db_connected": db is not None,
        "env_vars": list(os.environ.keys()) # Safe to show keys, don't show values
    }
    
    if db is not None:
        try:
            client.admin.command('ping')
            status['ping'] = "Success"
        except Exception as e:
            status['ping'] = f"Failed: {str(e)}"
            
    return status

if __name__ == '__main__':
    app.run(debug=True)
