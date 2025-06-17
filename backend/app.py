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
import requests
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
        conversation_id = data.get('conversation_id') or str(uuid.uuid4())
        
        # Check if session ID is provided
        session_id = data.get('session_id', request.cookies.get('project_session_id'))
        
        # Get OpenAI API key from config
        openai_api_key = Config.OPENAI_API_KEY
        
        # Check if we have a valid API key
        use_openai_api = openai_api_key and openai_api_key.startswith('sk-')
        
        # Prepare detailed response based on session data
        if session_id and session_id in user_sessions:
            session_data = user_sessions[session_id]
            
            # Get project data
            project_data = session_data.get('project_data', {})
            parsed_data = session_data.get('parsed_data', {})
            tasks = parsed_data.get('tasks', [])
            risks = session_data.get('risks', {})
            critical_path = session_data.get('critical_path', {})
            dashboard = session_data.get('dashboard_data', {})
            
            # Extract specific project details
            project_name = parsed_data.get('project_name', 'Untitled Project')
            task_count = len(tasks)
            completion = dashboard.get('completion_percentage', 0)
            start_date = dashboard.get('timeline', {}).get('start', 'N/A')
            end_date = dashboard.get('timeline', {}).get('end', 'N/A')
            
            # Prepare project context for OpenAI
            if use_openai_api:
                # Create a project context summary for the AI
                project_context = {
                    "project_name": project_name,
                    "task_count": task_count,
                    "completion_percentage": completion,
                    "timeline": {"start": start_date, "end": end_date},
                    "critical_path_count": len(critical_path.get('critical_path', [])),
                    "critical_path_duration": critical_path.get('total_duration', 0),
                    "risks_summary": {
                        "high_risks": len(risks.get('high_risks', [])),
                        "medium_risks": len(risks.get('medium_risks', [])),
                        "low_risks": len(risks.get('low_risks', []))
                    },
                    "status_distribution": dashboard.get('status_distribution', {}),
                    "resource_allocation": dashboard.get('resource_allocation', {})
                }
                
                # Make a call to the OpenAI API
                try:
                    # Define the API endpoint
                    url = "https://api.openai.com/v1/chat/completions"
                    
                    # Set up headers with the API key
                    headers = {
                        "Authorization": f"Bearer {openai_api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Prepare the messages for the API request
                    messages = [
                        {"role": "system", "content": f"You are an AI project management assistant specialized in analyzing project data. You have access to data about the project named '{project_name}'. Provide helpful, accurate, and concise information. Format your responses using basic HTML tags for better readability. Be professional and focus on project management insights."}
                    ]
                    
                    # Add context about the project
                    messages.append({"role": "system", "content": f"Project context: {json.dumps(project_context)}"}) 
                    
                    # Add the user's question
                    messages.append({"role": "user", "content": question})
                    
                    # Prepare the request payload
                    payload = {
                        "model": "gpt-3.5-turbo",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 700
                    }
                    
                    # Make the API request
                    api_response = requests.post(url, headers=headers, json=payload)
                    response_data = api_response.json()
                    
                    # Extract the response from the API
                    if api_response.status_code == 200 and 'choices' in response_data:
                        # Use the API response
                        api_content = response_data['choices'][0]['message']['content']
                        # We'll return this API content later, for now we set response to it
                        response = api_content
                        using_api = True
                    else:
                        # If API call fails, fall back to simulated response
                        print(f"OpenAI API error: {api_response.status_code}")
                        print(f"Response data: {response_data}")
                        # Will continue to generate simulated response
                        using_api = False
                except Exception as api_error:
                    print(f"Error calling OpenAI API: {str(api_error)}")
                    # Will continue to generate simulated response
                    using_api = False
            else:
                # API key not available or invalid, use simulated responses
                using_api = False
            
            # If not using API, generate a simulated context-aware response
            if not use_openai_api or (use_openai_api and not using_api):
                if 'status' in question.lower() or 'progress' in question.lower():
                    # Project status response
                    status_dist = dashboard.get('status_distribution', {})
                    completed = status_dist.get('Completed', 0)
                    in_progress = status_dist.get('In Progress', 0)
                    not_started = status_dist.get('Not Started', 0)
                    
                    response = f"<p>The project <strong>{project_name}</strong> is currently <strong>{completion}%</strong> complete.</p>"
                    response += f"<p>Out of {task_count} tasks:</p>"
                    response += f"<ul>"
                    response += f"<li><strong>{completed}</strong> tasks completed</li>"
                    response += f"<li><strong>{in_progress}</strong> tasks in progress</li>"
                    response += f"<li><strong>{not_started}</strong> tasks not started</li>"
                    response += f"</ul>"
                    response += f"<p>The project is scheduled to run from <strong>{start_date}</strong> to <strong>{end_date}</strong>.</p>"
                
                elif 'risk' in question.lower() or 'risks' in question.lower():
                    # Risk analysis response
                    risk_categories = risks.get('risk_categories', {})
                    high_risks = risks.get('high_risks', [])
                    
                    response = f"<p>I've analyzed the project risks and found:</p>"
                    response += f"<ul>"
                    
                    if 'timeline_risks' in risk_categories:
                        timeline_score = risk_categories.get('timeline_risks', {}).get('score', 0)
                        response += f"<li>Timeline risk score: <strong>{timeline_score}/10</strong></li>"
                    
                    if 'dependency_risks' in risk_categories:
                        dep_score = risk_categories.get('dependency_risks', {}).get('score', 0)
                        response += f"<li>Dependency risk score: <strong>{dep_score}/10</strong></li>"
                    
                    if 'resource_risks' in risk_categories:
                        res_score = risk_categories.get('resource_risks', {}).get('score', 0)
                        response += f"<li>Resource risk score: <strong>{res_score}/10</strong></li>"
                    
                    response += f"</ul>"
                    
                    if high_risks:
                        response += f"<p>The most critical risks to address are:</p>"
                        response += f"<ul>"
                        for i, risk in enumerate(high_risks[:3]):
                            response += f"<li><strong>{risk.get('description', 'Risk ' + str(i+1))}</strong></li>"
                        response += f"</ul>"
                    else:
                        response += f"<p>No critical risks were identified at this time.</p>"
                
                elif 'critical' in question.lower() and ('path' in question.lower() or 'tasks' in question.lower()):
                    # Critical path response
                    critical_tasks = critical_path.get('critical_path', [])
                    total_duration = critical_path.get('total_duration', 0)
                    duration_unit = critical_path.get('duration_unit', 'days')
                    
                    response = f"<p>The critical path consists of <strong>{len(critical_tasks)}</strong> tasks with a total duration of <strong>{total_duration} {duration_unit}</strong>.</p>"
                    
                    if critical_tasks:
                        response += f"<p>Critical path tasks:</p>"
                        response += f"<ol>"
                        for task in critical_tasks[:5]:  # Limit to first 5 tasks to avoid overwhelming responses
                            task_name = task.get('nom', task.get('name', 'Unnamed task'))
                            task_duration = task.get('duree_estimee', 0)
                            response += f"<li><strong>{task_name}</strong> ({task_duration} {duration_unit})</li>"
                        
                        if len(critical_tasks) > 5:
                            response += f"<li>... and {len(critical_tasks) - 5} more tasks</li>"
                        
                        response += f"</ol>"
                        response += f"<p>Any delay in these tasks will directly impact the project end date.</p>"
                
                elif 'resources' in question.lower() or 'resource allocation' in question.lower():
                    # Resource allocation response
                    resources = dashboard.get('resource_allocation', {})
                    
                    response = f"<p>Resource allocation for project <strong>{project_name}</strong>:</p>"
                    
                    if resources:
                        response += f"<ul>"
                        for resource, count in resources.items():
                            response += f"<li><strong>{resource}</strong>: {count} tasks</li>"
                        response += f"</ul>"
                    else:
                        response += f"<p>No resource allocation data available for this project.</p>"
                
                elif 'bottleneck' in question.lower() or 'constraint' in question.lower():
                    # Bottleneck analysis
                    advanced_schedule = session_data.get('advanced_schedule', {})
                    bottlenecks = advanced_schedule.get('bottlenecks', [])
                    
                    if bottlenecks:
                        response = f"<p>I've identified the following bottlenecks in your project:</p>"
                        response += f"<ul>"
                        for bottleneck in bottlenecks[:3]:
                            task_name = bottleneck.get('task_name', 'Unnamed task')
                            duration = bottleneck.get('duration', 0)
                            impact = bottleneck.get('impact_factor', 1.0)
                            response += f"<li><strong>{task_name}</strong> - Duration: {duration} days (Impact factor: {impact:.1f}x)</li>"
                        response += f"</ul>"
                        response += f"<p>These tasks are on the critical path and have durations significantly longer than average, making them potential bottlenecks.</p>"
                    else:
                        response = f"<p>No significant bottlenecks were identified in the critical path of your project.</p>"
                
                elif any(word in question.lower() for word in ['help', 'capability', 'can you', 'what can', 'features']):
                    # Help response
                    response = f"<p>I can help you analyze your project <strong>{project_name}</strong> in several ways:</p>"
                    response += f"<ul>"
                    response += f"<li>Provide project status and completion percentage</li>"
                    response += f"<li>Analyze the critical path and identify bottlenecks</li>"
                    response += f"<li>Assess risks and provide recommendations</li>"
                    response += f"<li>Review resource allocation and constraints</li>"
                    response += f"<li>Generate insights from project timeline</li>"
                    response += f"</ul>"
                    response += f"<p>What specific aspect of your project would you like me to analyze?</p>"
                
                else:
                    # General project overview response
                    response = f"<p>I've analyzed the project <strong>{project_name}</strong> with {task_count} tasks. The project is currently <strong>{completion}%</strong> complete and scheduled to run from {start_date} to {end_date}.</p>"
                    
                    # Add summary of critical path and risks
                    total_cp_tasks = len(critical_path.get('critical_path', []))
                    total_risks = len(risks.get('high_risks', [])) + len(risks.get('medium_risks', []))
                    
                    response += f"<p>The critical path consists of {total_cp_tasks} tasks, and I've identified {total_risks} potential risks.</p>"
                    response += f"<p>To get more specific information, you can ask me about project status, critical path, risks, or resource allocation.</p>"
        
        else:
            # No session data available
            response = "<p>Please upload a project or load sample data first to get project-specific answers.</p>"
            use_openai_api = False
        
        # Return response with proper format for frontend
        return jsonify({
            'success': True,
            'response': response,
            'conversation_id': conversation_id,
            'simulated': not (use_openai_api and 'using_api' in locals() and using_api)  # Only false if we actually used the API
        })
        
    except Exception as e:
        # Return error response with more details for debugging
        error_message = str(e)
        print(f"Error in ask_question: {error_message}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f"<p>Sorry, I encountered an error while processing your question.</p><p>Error details: {error_message}</p>",
            'error': "Could not process your question. Please try again.",
            'conversation_id': conversation_id if 'conversation_id' in locals() else str(uuid.uuid4()),
            'simulated': True
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
