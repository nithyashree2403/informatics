import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

# Use instance folder for the database to ensure persistence across runs
app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'todo.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tittle = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default='Medium', nullable=False)


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


@app.route('/')
def index():
    q = request.args.get('q','').strip()
    today_filter = request.args.get('today')
    priority_filter = request.args.get('priority')
    
    query = Task.query
    completed_query = CompletedTask.query
    
    # Apply search filter
    if q:
        query = query.filter(Task.tittle.ilike(f"%{q}%"))
        completed_query = completed_query.filter(CompletedTask.tittle.ilike(f"%{q}%"))
    
    # Apply today filter
    if today_filter == 'true':
        today = date.today()
        query = query.filter(Task.due_date == today)
        completed_query = completed_query.filter(CompletedTask.due_date == today)
    
    # Apply priority filter
    if priority_filter and priority_filter.lower() in ('high','medium','low'):
        priority_norm = priority_filter.lower()
        mapping = {'high':'High','medium':'Medium','low':'Low'}
        query = query.filter(Task.priority == mapping[priority_norm])
        completed_query = completed_query.filter(CompletedTask.priority == mapping[priority_norm])
    
    tasks = query.order_by(Task.created_date).all()
    completed_tasks = completed_query.order_by(CompletedTask.completed_date.desc()).all()
    return render_template('index.html', tasks=tasks, completed_tasks=completed_tasks)


@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        tittle = request.form.get('tittle', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'Medium')
        if not tittle:
            return render_template('create.html', error='Tittle is required')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        new_task = Task(tittle=tittle, description=description, due_date=due_date, priority=priority, done=False)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create.html')


@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        tittle = request.form.get('tittle', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'Medium')
        done = request.form.get('done') == 'on'
        if not tittle:
            return render_template('update.html', task=task, error='Tittle is requiered')
        # If user marked task done during update, move it to CompletedTask
        if done:
            completed = CompletedTask(
                tittle=tittle,
                description=description,
                created_date=task.created_date,
                due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None,
                priority=priority,
                completed_date=datetime.utcnow(),
            )
            db.session.add(completed)
            db.session.delete(task)
            db.session.commit()
            return redirect(url_for('index'))
        # otherwise update fields on existing task
        task.tittle = tittle
        task.description = description
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        task.priority = priority
        db.session.commit()
        return redirect(url_for('index'))
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


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    # allow deleting from either active or completed tables
    task = Task.query.get(id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return redirect('/')
    ctask = CompletedTask.query.get_or_404(id)
    db.session.delete(ctask)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)




