# Flask ToDo Application - Final Project

## Project Overview
A fully functional ToDo web application built with Flask that implements complete CRUD (Create, Read, Update, Delete) functionality.

## Features Implemented

### 1. **Create New Task** ✓
- Form to add new tasks with title, description, due date, and priority
- Input validation to ensure required fields are filled
- Route: `/create`

### 2. **Read All Tasks** ✓
- Display all active tasks in a table format
- Display completed tasks separately
- Search functionality to filter tasks by title
- Filter by priority (High, Medium, Low)
- Filter by due date (Today's tasks)
- Route: `/` (index)

### 3. **Update Existing Task** ✓
- Edit task details including title, description, priority, and due date
- Mark tasks as completed
- Professional form layout with clear UI
- Route: `/update/<id>`

### 4. **Delete Task** ✓
- Delete tasks from both active and completed lists
- Confirmation dialog before deletion
- Route: `/delete/<id>`

## Additional Features

### Task Management
- **Priority Levels**: High (Red), Medium (Yellow), Low (Green)
- **Due Dates**: Set and track task deadlines
- **Task Completion**: Toggle tasks between active and completed states
- **Created Date**: Automatically track when tasks were created

### User Interface
- Clean, modern design with responsive layout
- Sidebar navigation with user profile section
- Color-coded priority badges
- Separate tables for active and completed tasks
- Search and filter functionality
- Visual feedback for user actions

### 🔒 GDPR Compliance Features (Part 2 Integration)

#### Implemented GDPR Rights:
1. **Right to be Informed (Article 13)** ✅
   - Comprehensive privacy policy page
   - Clear explanation of data collection and processing
   - Route: `/gdpr/privacy-policy`

2. **Right of Access (Article 15)** ✅
   - View all stored personal data
   - Access audit log showing all data operations
   - Route: `/gdpr/access-log`

3. **Right to Rectification (Article 16)** ✅
   - Update tasks and personal information anytime
   - Implemented through update functionality

4. **Right to Erasure (Article 17)** ✅
   - "Right to be Forgotten" - delete all data permanently
   - Confirmation dialog before deletion
   - Route: `/gdpr/delete-all-data`

5. **Right to Data Portability (Article 20)** ✅
   - Export all data in JSON format
   - Downloadable file with complete data dump
   - Route: `/gdpr/export-data`

6. **Conditions for Consent (Article 7)** ✅
   - Granular consent management
   - Essential vs optional data processing
   - Withdraw consent anytime
   - Route: `/gdpr/consent`

7. **Storage Limitation (Article 5)** ✅
   - Clear data retention policies
   - Automatic deletion timelines
   - User control over data lifecycle
   - Route: `/gdpr/data-retention`

8. **Integrity and Confidentiality (Article 32)** ✅
   - Audit logging for all data operations
   - IP address tracking with anonymization
   - Session management

#### GDPR Database Tables:
- `User`: Stores consent preferences and user settings
- `DataAccessLog`: Audit trail of all data operations (exports, deletions, consent changes)
- `Task`: Active tasks (with GDPR controls)
- `CompletedTask`: Completed tasks (with retention policy)

#### Consent Management System:
- **Essential Consent**: Required for app functionality (data storage)
- **Analytics Consent**: Optional - for productivity insights
- **Data Sharing Consent**: Optional - for third-party personalization services
- All consents can be withdrawn independently
- Consent timestamp tracking for compliance proof

### Data Persistence
- SQLite database stored in `instance/todo.db`
- Four database tables:
  - `Task`: Active tasks
  - `CompletedTask`: Completed tasks with completion timestamp
  - `User`: User preferences and consent records (GDPR)
  - `DataAccessLog`: Audit trail for GDPR compliance

## Project Structure

```
Final_project/
├── app.py                 # Main Flask application
├── instance/
│   └── todo.db           # SQLite database (INCLUDED)
├── static/
│   └── style.css         # CSS styling
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Main page (Read all tasks)
│   ├── create.html       # Create new task form
│   └── update.html       # Update task form
└── README.md             # This file
```

## Database Schema

### Task Table
- `id`: Integer (Primary Key)
- `tittle`: String(100) - Task title
- `description`: Text - Task description
- `done`: Boolean - Completion status
- `created_date`: DateTime - When task was created
- `due_date`: Date - Task deadline (optional)
- `priority`: String(20) - High/Medium/Low

### CompletedTask Table
- `id`: Integer (Primary Key)
- `tittle`: String(100) - Task title
- `description`: Text - Task description
- `created_date`: DateTime - When task was originally created
- `due_date`: Date - Task deadline (optional)
- `priority`: String(20) - High/Medium/Low
- `completed_date`: DateTime - When task was completed

## How to Run

1. Activate the virtual environment:
```bash
source /Users/nithyashree/Documents/myflaskapp/myenvironment/bin/activate
```

2. Navigate to project directory:
```bash
cd /Users/nithyashree/Documents/myflaskapp/Final_project
```

3. Run the Flask application:
```bash
python app.py
```

4. Open your browser and visit:
```
http://127.0.0.1:5000/
```

## Technologies Used
- **Backend**: Flask 2.x, Flask-SQLAlchemy
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3
- **Template Engine**: Jinja2

## CRUD Operations Summary

| Operation | Route | Method | Description |
|-----------|-------|--------|-------------|
| Create | `/create` | GET, POST | Add new task |
| Read | `/` | GET | View all tasks with filters |
| Update | `/update/<id>` | GET, POST | Edit existing task |
| Delete | `/delete/<id>` | POST | Remove task |

## Additional Routes

### Task Management
- `/toggle/<id>` (POST): Toggle task between active and completed

### GDPR Compliance Routes
| Route | Method | GDPR Article | Description |
|-------|--------|--------------|-------------|
| `/gdpr/privacy-policy` | GET | Article 13 | View privacy policy and data protection info |
| `/gdpr/consent` | GET, POST | Article 7 | Manage consent preferences |
| `/gdpr/export-data` | GET | Articles 15, 20 | Download all personal data (JSON) |
| `/gdpr/delete-all-data` | POST | Article 17 | Exercise right to erasure |
| `/gdpr/access-log` | GET | Article 15 | View audit trail of data operations |
| `/gdpr/data-retention` | GET | Article 5 | View retention policy and data summary |

## Form Validation
- Title field is required for all operations
- Empty titles show error messages
- Safe handling of optional fields (description, due date)

## Part 2: GDPR Implementation

This application demonstrates practical GDPR compliance through:

### API Services for Personalization (Theoretical)
The app supports potential API endpoints for personalization services:
- Task analytics and patterns
- Productivity metrics
- User behavior insights
- All with proper consent management

### GDPR Principles Implemented:

1. **Transparency**: Clear privacy policy and data usage information
2. **Consent**: Granular consent management with opt-in/opt-out
3. **Access**: Users can view all their data and access logs
4. **Portability**: JSON export of all personal data
5. **Erasure**: Complete data deletion capability
6. **Accuracy**: Users can update/correct their data
7. **Storage Limitation**: Defined retention periods
8. **Security**: Audit logging and session management

### Real-World Application:
The consent system allows users to:
- Approve basic data storage (required)
- Opt into analytics (optional)
- Consent to third-party data sharing (optional)
- Withdraw any consent at any time

This demonstrates how a todo app could partner with personalization services while maintaining GDPR compliance.

## Notes for Submission
- ✓ All CRUD operations implemented and tested
- ✓ Database file (`instance/todo.db`) included in submission
- ✓ Professional UI with modern design
- ✓ Input validation and error handling
- ✓ Search and filter functionality (bonus features)
- ✓ **GDPR compliance features fully implemented**
- ✓ Complete documentation
- ✓ Part 2 requirements integrated into application

## Screenshots
Please include screenshots of:
1. Home page showing active tasks
2. Create task form
3. Update task form
4. Task filtering in action
5. Completed tasks section
6. **Privacy Policy page**
7. **Consent Management page**
8. **Data Export functionality**
9. **Access Log page**
10. **Data Retention policy page**

---

**Student**: Nithyashree
**Date**: December 17, 2025
**Course**: Web Development with Flask
