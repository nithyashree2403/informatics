
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

# Initialize Flask app with instance folder
# I learned that instance folder is better for storing database files
app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'my-secret-key-2025'  # needed this for session management


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'

db = SQLAlchemy(app)


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


if __name__ == '__main__':
    app.run(debug=True)




