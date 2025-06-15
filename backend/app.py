"""
AI-Powered Project Management Assistant
Flask Backend API
"""
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import os
import json
import base64
import traceback
import uuid
import shutil
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

# Import utility modules
from utils.json_parser import ProjectParser
from utils.gantt_visualizer import GanttVisualizer
from utils.critical_path import CriticalPathCalculator
from utils.risk_detector import RiskDetector
from config import Config

app = Flask(__name__)
CORS(app)

# Configure upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Session storage for uploads
user_sessions = {}  # Maps session_id to project data

# Session cleanup interval (in seconds)
SESSION_CLEANUP_INTERVAL = 3600  # 1 hour
LAST_CLEANUP_TIME = datetime.now()

# Initialize app configuration
# Note: removed ChatGPT agent as we're using standard parsers

@app.route('/api/upload', methods=['POST'])
@cross_origin(supports_credentials=True)
def upload_project():
    try:
        # Generate a session ID
        session_id = str(uuid.uuid4())
        file_path = None
        
        # Check if file upload or JSON payload
        if request.files and 'file' in request.files:
            # Handle file upload
            file = request.files['file']
            
            # Create unique directory for this session
            session_dir = os.path.join(UPLOAD_DIR, session_id)
            os.makedirs(session_dir, exist_ok=True)
            
            # Save the uploaded file
            file_path = os.path.join(session_dir, file.filename)
            file.save(file_path)
            
            # Load the saved file
            with open(file_path, 'r') as f:
                project_json = json.load(f)
        else:
            # Handle JSON in request body
            project_json = request.json
        
        if not project_json:
            return jsonify({
                'success': False,
                'error': 'No project data provided'
            }), 400
        
        # Parse project data using the standard parser
        try:
            print(f"Project JSON data: {project_json}")
            
            # Ensure we have a valid dictionary
            if not isinstance(project_json, dict):
                return jsonify({
                    'success': False,
                    'message': 'Invalid JSON data format, expected a dictionary'
                }), 400
                
            # Use the project parser for standard format
            parser = ProjectParser(json_data=project_json)
            summary = parser.get_summary()
            tasks = parser.get_tasks()
            
            print(f"Tasks found: {len(tasks)}")
            
            if not tasks:
                return jsonify({
                    'success': False,
                    'message': 'No tasks found in the project data'
                }), 400
                
            # Create dashboard data
            dashboard_data = {
                'status_distribution': parser.get_task_status_counts(),
                'timeline': {
                    'start': summary.get('start_date', ''),
                    'end': summary.get('end_date', '')
                },
                'completion_percentage': parser.get_completion_percentage(),
                'resource_allocation': parser.get_resource_allocation()
            }
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'Error parsing project data: {str(e)}'
            }), 400
        
        # Calculate critical path
        cp_calculator = CriticalPathCalculator(tasks)
        critical_path = cp_calculator.get_critical_path_details()
        
        # Detect risks
        risk_detector = RiskDetector(tasks)
        risks = risk_detector.detect_risks()
        
        # Store session data with comprehensive information
        user_sessions[session_id] = {
            'project_data': project_json,           # Raw project data
            'parsed_data': summary,                 # Parsed summary
            'dashboard_data': dashboard_data,       # Dashboard visualization data
            'critical_path': critical_path,         # Critical path analysis
            'risks': risks,                         # Risk analysis
            'file_path': file_path,                 # Path to uploaded file if any
            'timestamp': datetime.now(),            # Upload time
            'expiry': datetime.now() + timedelta(days=30)  # Keep for 30 days
        }
        
     
        
        # Create response with cookie and dashboard data
        response = {
            'success': True,
            'summary': summary,
            'critical_path': critical_path,
            'risks': risks,
            'dashboard': dashboard_data,  # Include AI-generated dashboard data
            'session_id': session_id
        }
        
        # Create response object to set cookie
        resp = make_response(jsonify(response))
        resp.set_cookie('project_session_id', session_id, max_age=86400)  # 24 hours
        
        return resp
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing project data: {str(e)}'
        }), 500

@app.route('/api/gantt', methods=['POST'])
@cross_origin(supports_credentials=True)
def generate_gantt():
    """API endpoint to generate Gantt chart data"""
    try:
        # Get session ID from request
        session_id = request.cookies.get('project_session_id')
        if not session_id or session_id not in user_sessions:
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 400
        
        # Generate Gantt chart
        tasks = user_sessions[session_id]['parsed_data']['tasks']
        gantt_viz = GanttVisualizer(tasks)
        gantt_data = gantt_viz.generate_chart_data()
        
        return jsonify({
            'success': True,
            'gantt_data': gantt_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating Gantt chart: {str(e)}'
        }), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard data based on stored session data"""
    # Get session ID from cookie
    session_id = request.cookies.get('project_session_id')
    
    if not session_id or session_id not in user_sessions:
        return jsonify({
            'success': False,
            'message': 'No active session found. Please upload a project first.'
        }), 404
        
    # Retrieve stored data
    data = user_sessions[session_id]
    
    try:
        # Return the dashboard data
        return jsonify({
            'success': True,
            'dashboard': data.get('dashboard_data', {})
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating dashboard: {str(e)}"
        }), 500

@app.route('/api/charts/network-diagram', methods=['GET'])
def get_network_diagram():
    """Generate network diagram for critical path visualization"""
    # Get session ID from cookie
    session_id = request.cookies.get('project_session_id')
    
    if not session_id or session_id not in user_sessions:
        return jsonify({
            'success': False,
            'message': 'No active session found. Please upload a project first.'
        }), 404
        
    # Retrieve stored data
    data = user_sessions[session_id]
    tasks = data.get('parsed_data', {}).get('tasks', [])
    critical_path = data.get('critical_path', {}).get('path_ids', [])
    
    try:
        # Create critical path calculator
        calculator = CriticalPathCalculator(tasks, critical_path)
        
        # Generate network diagram
        diagram_data = calculator.generate_network_diagram()
        
        return jsonify({
            'success': True,
            'diagram': diagram_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating network diagram: {str(e)}"
        }), 500
        
@app.route('/api/charts/risk-analysis', methods=['GET'])
def get_risk_charts():
    """Get detailed risk analysis and chart data"""
    # Get session ID from cookie
    session_id = request.cookies.get('project_session_id')
    
    if not session_id or session_id not in user_sessions:
        return jsonify({
            'success': False,
            'message': 'No active session found. Please upload a project first.'
        }), 404
        
    # Retrieve stored data
    data = user_sessions[session_id]
    tasks = data.get('parsed_data', {}).get('tasks', [])
    critical_path = data.get('critical_path', {}).get('path_ids', [])
    
    try:
        # Create risk detector
        detector = RiskDetector(tasks, critical_path)
        
        # Get enhanced risk analysis
        risk_analysis = detector.detect_risks()
        
        return jsonify({
            'success': True,
            'analysis': risk_analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating risk charts: {str(e)}"
        }), 500
        
@app.route('/api/charts/advanced-schedule', methods=['GET'])
def get_advanced_schedule():
    """Get advanced schedule analysis with slack times and critical path details"""
    # Get session ID from cookie
    session_id = request.cookies.get('project_session_id')
    
    if not session_id or session_id not in user_sessions:
        return jsonify({
            'success': False,
            'message': 'No active session found. Please upload a project first.'
        }), 404
        
    # Retrieve stored data
    data = user_sessions[session_id]
    tasks = data.get('parsed_data', {}).get('tasks', [])
    
    try:
        # Create critical path calculator
        calculator = CriticalPathCalculator(tasks)
        
        # Get advanced schedule analysis
        advanced_analysis = calculator.get_advanced_analysis()
        
        return jsonify({
            'success': True,
            'advanced_schedule': advanced_analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating advanced schedule: {str(e)}"
        }), 500

@app.route('/api/ask', methods=['POST'])
@cross_origin(supports_credentials=True)
def ask_question():
    """API endpoint for project-related questions"""
    try:
        # Get question from request
        data = request.json
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        question = data['question']
        
        # Check if session ID is provided
        session_id = data.get('session_id', request.cookies.get('project_session_id'))
        
        # Prepare response based on session data (simulated response)
        if session_id and session_id in user_sessions:
            session_data = user_sessions[session_id]
            
            project_name = session_data.get('parsed_data', {}).get('project_name', 'Untitled Project')
            task_count = len(session_data.get('parsed_data', {}).get('tasks', []))
            completion = session_data.get('dashboard_data', {}).get('completion_percentage', 0)
            
            # Generate a simple response based on the question
            answer = f"I analyzed the project '{project_name}' with {task_count} tasks. "
            
            if 'status' in question.lower() or 'progress' in question.lower():
                answer += f"The project is {completion}% complete."
            elif 'risk' in question.lower():
                risks = session_data.get('risks', [])
                answer += f"I found {len(risks)} potential risks in this project."
            elif 'critical' in question.lower() or 'path' in question.lower():
                cp = session_data.get('critical_path', {})
                answer += f"The critical path contains {len(cp.get('path', []))} tasks."
            else:
                answer += "How can I help you analyze this project further?"
        else:
            # No session data available
            answer = "Please upload a project or load sample data first to get project-specific answers."
        
        # Return response
        return jsonify({
            'success': True,
            'answer': answer
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing question: {str(e)}'
        }), 500

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    global LAST_CLEANUP_TIME
    
    # Only run cleanup if enough time has passed since last cleanup
    if (datetime.now() - LAST_CLEANUP_TIME).total_seconds() < SESSION_CLEANUP_INTERVAL:
        return
    
    # Update cleanup time
    LAST_CLEANUP_TIME = datetime.now()
    
    # Find expired sessions
    expired_sessions = []
    for session_id, session_data in user_sessions.items():
        if datetime.now() > session_data['expiry']:
            expired_sessions.append(session_id)
    
    # Remove expired sessions
    for session_id in expired_sessions:
        # Clean up files if any
        if 'file_path' in user_sessions[session_id] and user_sessions[session_id]['file_path']:
            session_dir = os.path.dirname(user_sessions[session_id]['file_path'])
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
        
        # Remove from session storage
        del user_sessions[session_id]
    
    # Log cleanup
    if expired_sessions:
        print(f"Cleaned up {len(expired_sessions)} expired sessions")

@app.route('/api/session/<session_id>', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_session_data(session_id):
    """API endpoint to retrieve session data"""
    try:
        # Run session cleanup
        cleanup_expired_sessions()
        
        # Check if session ID is valid
        if not session_id or session_id not in user_sessions:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 404
        
        # Get session data
        session_data = user_sessions[session_id]
        
        # Check if session has expired
        if datetime.now() > session_data['expiry']:
            # Clean up expired session
            if 'file_path' in session_data and session_data['file_path']:
                session_dir = os.path.dirname(session_data['file_path'])
                if os.path.exists(session_dir):
                    shutil.rmtree(session_dir)
            
            del user_sessions[session_id]
            
            return jsonify({
                'success': False,
                'error': 'Session has expired'
            }), 410
        
        # Return session data with dashboard information
        return jsonify({
            'success': True,
            'summary': session_data['parsed_data'],
            'critical_path': session_data['critical_path'],
            'risks': session_data['risks'],
            'dashboard': session_data.get('dashboard_data', {}),  # Include dashboard data if available
            'project_data': session_data['project_data'],
            'session_id': session_id
        })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error retrieving session data: {str(e)}'
        }), 500

@app.route('/api/sample', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_sample_data():
    """API endpoint to load sample project data"""
    try:
        # Generate a session ID for the sample data
        session_id = str(uuid.uuid4())
        
        # Path to sample JSON file
        sample_file = os.path.join(os.path.dirname(__file__), 'sample_project.json')
        
        if not os.path.exists(sample_file):
            return jsonify({
                'success': False,
                'error': 'Sample project file not found'
            }), 404
        
        # Load sample data
        with open(sample_file, 'r') as f:
            data = json.load(f)
        
        # Use standard ProjectParser for sample data
        parser = ProjectParser(json_data=data)
        summary = parser.get_summary()
        tasks = parser.get_tasks()
        
        # Create dashboard data
        dashboard_data = {
            'status_distribution': parser.get_task_status_counts(),
            'timeline': {
                'start': summary.get('start_date', ''),
                'end': summary.get('end_date', '')
            },
            'completion_percentage': parser.get_completion_percentage(),
            'resource_allocation': parser.get_resource_allocation()
        }
        
        # Calculate critical path
        cp_calculator = CriticalPathCalculator(tasks)
        critical_path = cp_calculator.get_critical_path_details()
        
        # Detect risks
        risk_detector = RiskDetector(tasks)
        risks = risk_detector.detect_risks()
        
        # Store in session
        user_sessions[session_id] = {
            'project_data': data,
            'parsed_data': summary,
            'dashboard_data': dashboard_data,
            'critical_path': critical_path,
            'risks': risks,
            'file_path': sample_file,
            'timestamp': datetime.now(),
            'expiry': datetime.now() + timedelta(days=30)  # Extended to 30 days
        }
        
        # Sample project data loaded successfully
        
        # Create response with cookie and dashboard data
        response = {
            'success': True,
            'summary': summary,
            'critical_path': critical_path,
            'risks': risks,
            'dashboard': dashboard_data,  
            'session_id': session_id
        }
        
        # Create response object to set cookie
        resp = make_response(jsonify(response))
        resp.set_cookie('project_session_id', session_id, max_age=86400*30)  # 30 days
        
        return resp
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading sample data: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
