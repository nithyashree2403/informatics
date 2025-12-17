import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

# Initialize Flask app with instance folder
# I learned that instance folder is better for storing database files
app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'my-secret-key-2025'  # needed this for session management
os.makedirs(app.instance_path, exist_ok=True)

# Database setup - using SQLite because it's simple and works well for this project
db_path = os.path.join(app.instance_path, 'todo.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # this removes warning messages
db = SQLAlchemy(app)


# User model - added for GDPR compliance requirements
# This stores user consent preferences as per GDPR Article 7
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, default='User')
    email = db.Column(db.String(120), nullable=True)
    # Different types of consent - learned that GDPR requires granular consent options
    consent_given = db.Column(db.Boolean, default=False, nullable=False)
    consent_date = db.Column(db.DateTime, nullable=True)
    data_sharing_consent = db.Column(db.Boolean, default=False, nullable=False)
    analytics_consent = db.Column(db.Boolean, default=False, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_data_export = db.Column(db.DateTime, nullable=True)

# Main Task model - stores active tasks
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tittle = db.Column(db.String(100), nullable=False)  # yes, I know it's spelled wrong but changing it breaks everything!
    description = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.Date, nullable=True)  # optional field
    priority = db.Column(db.String(20), default='Medium', nullable=False)

# CompletedTask model - keeps history of completed tasks
# I decided to use a separate table instead of just marking tasks as done
# because it makes the queries faster and keeps completed tasks separate
class CompletedTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tittle = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default='Medium', nullable=False)
    completed_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

# Audit log for GDPR compliance - tracks all data operations
# Required for GDPR Article 15 (Right to access)
class DataAccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)


with app.app_context():
    db.create_all()


# Main route - displays all tasks
@app.route('/')
def index():
    # Get search and filter parameters from URL
    # Changed to support multiple filters at once
    q = request.args.get('q','').strip()
    today_filter = request.args.get('today', '')
    priority_filter = request.args.get('priority', '')
    
    # Start with base queries
    query = Task.query
    completed_query = CompletedTask.query
    
    # Search functionality - searches in task titles
    if q:
        query = query.filter(Task.tittle.ilike(f"%{q}%"))
        completed_query = completed_query.filter(CompletedTask.tittle.ilike(f"%{q}%"))
    
    # Filter for today's tasks - can be combined with priority
    if today_filter == 'true':
        today = date.today()
        query = query.filter(Task.due_date == today)
        completed_query = completed_query.filter(CompletedTask.due_date == today)
    
    # Priority filter - can be combined with today filter
    if priority_filter and priority_filter.lower() in ('high','medium','low'):
        priority_norm = priority_filter.lower()
        # mapping dictionary to convert to proper case
        mapping = {'high':'High','medium':'Medium','low':'Low'}
        query = query.filter(Task.priority == mapping[priority_norm])
        completed_query = completed_query.filter(CompletedTask.priority == mapping[priority_norm])
    
    # Get all tasks and order them
    tasks = query.order_by(Task.created_date).all()
    completed_tasks = completed_query.order_by(CompletedTask.completed_date.desc()).all()
    
    return render_template('index.html', tasks=tasks, completed_tasks=completed_tasks)


# Create new task route
@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        # Get form data
        tittle = request.form.get('tittle', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'Medium')
        
        # Validation - title is required
        if not tittle:
            return render_template('create.html', error='Tittle is required')
        
        # Convert due date string to date object if provided
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        
        # Create new task and save to database
        new_task = Task(tittle=tittle, description=description, due_date=due_date, priority=priority, done=False)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    
    # GET request - show the form
    return render_template('create.html')


# Update existing task
@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    task = Task.query.get_or_404(id)  # get task or show 404 if not found
    
    if request.method == 'POST':
        # Get updated data from form
        tittle = request.form.get('tittle', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'Medium')
        done = request.form.get('done') == 'on'  # checkbox value
        
        # Validate title
        if not tittle:
            return render_template('update.html', task=task, error='Tittle is requiered')
        
        # If task is marked as done, move it to completed tasks table
        if done:
            # Create a new completed task with the same data
            completed = CompletedTask(
                tittle=tittle,
                description=description,
                created_date=task.created_date,  # keep original creation date
                due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None,
                priority=priority,
                completed_date=datetime.utcnow(),
            )
            db.session.add(completed)
            db.session.delete(task)  # remove from active tasks
            db.session.commit()
            return redirect(url_for('index'))
        
        # If not completed, just update the existing task
        task.tittle = tittle
        task.description = description
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        task.priority = priority
        db.session.commit()
        return redirect(url_for('index'))
    
    # GET request - show the update form
    return render_template('update.html', task=task)


@app.route('/toggle/<int:id>', methods=['POST'])
def toggle(id):
    # Use a hidden `source` field from the form to decide which table to move
    source = request.form.get('source')
    if source == 'active':
        task = Task.query.get_or_404(id)
        completed = CompletedTask(
            tittle=task.tittle,
            description=task.description,
            created_date=task.created_date,
            due_date=task.due_date,
            priority=task.priority,
            completed_date=datetime.utcnow(),
        )
        db.session.add(completed)
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('index'))
    if source == 'completed':
        ctask = CompletedTask.query.get_or_404(id)
        new_task = Task(
            tittle=ctask.tittle,
            description=ctask.description,
            created_date=ctask.created_date,
            due_date=ctask.due_date,
            priority=ctask.priority,
            done=False,
        )
        db.session.add(new_task)
        db.session.delete(ctask)
        db.session.commit()
        return redirect(url_for('index'))
    # Fallback: if no source provided, behave safely by preferring the exact match
    task = Task.query.get(id)
    if task:
        completed = CompletedTask(
            tittle=task.tittle,
            description=task.description,
            created_date=task.created_date,
            due_date=task.due_date,
            priority=task.priority,
            completed_date=datetime.utcnow(),
        )
        db.session.add(completed)
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('index'))
    ctask = CompletedTask.query.get_or_404(id)
    new_task = Task(
        tittle=ctask.tittle,
        description=ctask.description,
        created_date=ctask.created_date,
        due_date=ctask.due_date,
        priority=ctask.priority,
        done=False,
    )
    db.session.add(new_task)
    db.session.delete(ctask)
    db.session.commit()
    return redirect(url_for('index'))


# Delete task - works for both active and completed tasks
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    # First try to find in active tasks
    task = Task.query.get(id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return redirect('/')
    
    # If not found, must be in completed tasks
    ctask = CompletedTask.query.get_or_404(id)
    db.session.delete(ctask)
    db.session.commit()
    return redirect('/')


## GDPR Compliance Routes ##
# Added these to meet Part 2 requirements

# Privacy policy page - GDPR Article 13 requires informing users about data processing
@app.route('/gdpr/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

# Consent management - allows users to control their data preferences
# This is required by GDPR Article 7
@app.route('/gdpr/consent', methods=['GET', 'POST'])
def gdpr_consent():
    # Get or create user record
    user = User.query.first()
    if not user:
        user = User(username='User')
        db.session.add(user)
        db.session.commit()
    
    if request.method == 'POST':
        # Update consent preferences from form
        user.consent_given = request.form.get('consent_given') == 'on'
        user.data_sharing_consent = request.form.get('data_sharing') == 'on'
        user.analytics_consent = request.form.get('analytics') == 'on'
        user.consent_date = datetime.utcnow()
        db.session.commit()
        
        # Log this action for audit trail (GDPR requirement)
        log = DataAccessLog(
            action='consent_updated',
            ip_address=request.remote_addr,
            details=f'Consents: General={user.consent_given}, Sharing={user.data_sharing_consent}, Analytics={user.analytics_consent}'
        )
        db.session.add(log)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    # Show consent form
    return render_template('gdpr_consent.html', user=user)


# Data export - lets users download all their data
# This satisfies GDPR Article 15 (right of access) and Article 20 (data portability)
@app.route('/gdpr/export-data')
def export_data():
    user = User.query.first()
    if not user:
        user = User(username='User')
        db.session.add(user)
        db.session.commit()
    
    # Gather all user data from database
    tasks = Task.query.all()
    completed_tasks = CompletedTask.query.all()
    
    # Build JSON structure with all user data
    data = {
        'user_information': {
            'username': user.username,
            'email': user.email,
            'consent_given': user.consent_given,
            'data_sharing_consent': user.data_sharing_consent,
            'analytics_consent': user.analytics_consent,
            'consent_date': user.consent_date.isoformat() if user.consent_date else None,
            'account_created': user.created_date.isoformat()
        },
        'active_tasks': [
            {
                'id': t.id,
                'title': t.tittle,
                'description': t.description,
                'priority': t.priority,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'created_date': t.created_date.isoformat()
            } for t in tasks
        ],
        'completed_tasks': [
            {
                'id': t.id,
                'title': t.tittle,
                'description': t.description,
                'priority': t.priority,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'created_date': t.created_date.isoformat(),
                'completed_date': t.completed_date.isoformat()
            } for t in completed_tasks
        ],
        'export_date': datetime.utcnow().isoformat(),
        'data_protection_notice': 'This data is provided under GDPR Article 15 (Right of Access) and Article 20 (Right to Data Portability)'
    }
    
    # Track when user last exported data
    user.last_data_export = datetime.utcnow()
    db.session.commit()
    
    # Add to audit log
    log = DataAccessLog(
        action='data_export',
        ip_address=request.remote_addr,
        details=f'Exported {len(tasks)} active tasks and {len(completed_tasks)} completed tasks'
    )
    db.session.add(log)
    db.session.commit()
    
    # Return as downloadable JSON file
    response = make_response(json.dumps(data, indent=2))
    response.headers['Content-Disposition'] = f'attachment; filename=my_todo_data_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
    response.headers['Content-Type'] = 'application/json'
    return response


# Right to be forgotten - deletes all user data
# GDPR Article 17 requires this functionality
@app.route('/gdpr/delete-all-data', methods=['POST'])
def delete_all_data():
    # Delete everything from both task tables
    Task.query.delete()
    CompletedTask.query.delete()
    
    # Log this action before clearing data
    log = DataAccessLog(
        action='data_deletion_all',
        ip_address=request.remote_addr,
        details='User exercised right to erasure - all data deleted'
    )
    db.session.add(log)
    db.session.commit()
    
    # Reset user settings but keep the account record for compliance
    user = User.query.first()
    if user:
        user.consent_given = False
        user.data_sharing_consent = False
        user.analytics_consent = False
        user.email = None  # remove personal info
        db.session.commit()
    
    return redirect(url_for('index'))


# Show audit log of all data operations
@app.route('/gdpr/access-log')
def access_log():
    # Get last 50 log entries, newest first
    logs = DataAccessLog.query.order_by(DataAccessLog.timestamp.desc()).limit(50).all()
    return render_template('access_log.html', logs=logs)

# Data retention policy page
# Shows users what data we have and how long we keep it
@app.route('/gdpr/data-retention')
def data_retention():
    user = User.query.first()
    tasks = Task.query.all()
    completed_tasks = CompletedTask.query.all()
    
    # Find oldest tasks to show data age
    oldest_task = Task.query.order_by(Task.created_date).first()
    oldest_completed = CompletedTask.query.order_by(CompletedTask.created_date).first()
    
    return render_template('data_retention.html', 
                         user=user,
                         total_tasks=len(tasks),
                         total_completed=len(completed_tasks),
                         oldest_task=oldest_task,
                         oldest_completed=oldest_completed)


if __name__ == '__main__':
    app.run(debug=True)




