"""
ChatGPT Agent Module
Handles interactions with OpenAI's API to answer project-related questions
"""
import os
import json
import re
import openai


class ChatGPTAgent:
    """
    AI assistant agent using OpenAI's API
    Answers natural language questions about project data
    """
    
    def __init__(self, api_key=None, project_data=None):
        """
        Initialize the agent with API key and project data
        
        Args:
            api_key (str): OpenAI API key
            project_data (dict): Project data to provide context
        """
        self.api_key = api_key
        
        # Set API key if provided, otherwise use environment variable
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        
        self.project_data = project_data or {}
        self.raw_project_json = None  # Store the complete raw project JSON
        
        # Initialize conversation history and conversation store
        self.conversation_history = []
        self.conversation_store = {}
        
        # Add system message to establish agent purpose and behavior
        self._add_system_message()
        
    def set_api_key(self, api_key):
        """
        Update the API key
        
        Args:
            api_key (str): OpenAI API key
        """
        self.api_key = api_key
        openai.api_key = api_key
        
    def has_api_key(self):
        """
        Check if a valid API key is available
        
        Returns:
            bool: True if API key is available, False otherwise
        """
        return bool(self.api_key or os.environ.get("OPENAI_API_KEY"))
        
    def set_project_context(self, project_context):
        """
        Set project context data for AI responses
        
        Args:
            project_context (dict): Project context data
        """
        self.project_data = project_context
        
        # Store the raw project JSON as well if it exists
        if project_context and 'raw_project' in project_context:
            self.raw_project_json = project_context['raw_project']
        elif project_context and 'project_data' in project_context:
            self.raw_project_json = project_context['project_data']
        else:
            self.raw_project_json = project_context
            
        self._add_system_message()  # Refresh system message with new context
    
    def _add_system_message(self):
        """Add system message with context about project data"""
        # Create system message with project metadata
        system_message = {
            "role": "system",
            "content": "You are an AI project management assistant. "
                       "Your job is to analyze project data and answer questions about it. "
                       "Be concise, accurate, and helpful. "
                       "Remember the complete details of the user's project. "
                       "Here's the project data you have access to:\n\n"
        }
                # Add project summary
        if self.project_data:
            try:
                # Add project basics
                project_name = self.project_data.get("project_name", "Untitled Project")
                task_count = self.project_data.get("task_count", 0)
                project_summary = (
                    f"Project: {project_name}\n"
                    f"Number of tasks: {task_count}\n"
                )
                
                if "total_duration" in self.project_data:
                    duration = self.project_data["total_duration"]
                    unit = self.project_data.get("duration_unit", "days")
                    project_summary += f"Total duration: {duration} {unit}\n"
                
                # Add critical path info if available
                if "critical_path" in self.project_data:
                    cp_data = self.project_data["critical_path"]
                    cp_duration = cp_data.get("total_duration", "unknown")
                    cp_unit = cp_data.get("duration_unit", "days")
                    cp_tasks = len(cp_data.get("critical_path", []))
                    
                    project_summary += (
                        f"\nCritical Path:\n"
                        f"- Duration: {cp_duration} {cp_unit}\n"
                        f"- Number of tasks: {cp_tasks}\n"
                    )
                
                # Add risk info if available
                if "risks" in self.project_data:
                    risk_data = self.project_data["risks"]
                    risk_level = risk_data.get("risk_level", "Unknown")
                    total_risks = risk_data.get("total_risks", 0)
                    
                    project_summary += (
                        f"\nRisk Assessment:\n"
                        f"- Overall risk level: {risk_level}\n"
                        f"- Total risks identified: {total_risks}\n"
                    )
                    
                # Add raw project data as JSON for better context
                if hasattr(self, 'raw_project_json') and self.raw_project_json:
                    # Add basic info about the raw JSON structure
                    project_summary += f"\nComplete Project Data Structure:\n"
                    
                    # Extract key information about project structure
                    if isinstance(self.raw_project_json, dict):
                        # Add key fields from the top level
                        for key in self.raw_project_json.keys():
                            if key == 'taches' or key == 'tasks':
                                continue  # Skip the tasks array as we'll detail it separately
                            value = self.raw_project_json.get(key)
                            if isinstance(value, (str, int, float, bool)):
                                project_summary += f"- {key}: {value}\n"
                            elif isinstance(value, dict):
                                project_summary += f"- {key}: {type(value).__name__} with {len(value)} items\n"
                            elif isinstance(value, list):
                                project_summary += f"- {key}: List with {len(value)} items\n"
                        
                        # Add detailed info about tasks
                        tasks = self.raw_project_json.get('taches', []) or self.raw_project_json.get('tasks', [])
                        if tasks and len(tasks) > 0:
                            project_summary += f"\nDetailed Task Information:\n"
                            # Include full details of up to 10 tasks
                            for task in tasks[:10]:  # Limit to first 10 tasks to avoid token limit
                                task_id = task.get('id', 'unknown')
                                task_name = task.get('nom', '') or task.get('name', f'Task {task_id}')
                                project_summary += f"\nTask ID: {task_id}\n"
                                project_summary += f"Name: {task_name}\n"
                                
                                # Add other important task attributes
                                for key, value in task.items():
                                    if key not in ('id', 'nom', 'name'):
                                        if isinstance(value, (list, dict)):
                                            project_summary += f"- {key}: {str(value)}\n"
                                        else:
                                            project_summary += f"- {key}: {value}\n"
                            
                            if len(tasks) > 10:
                                project_summary += f"...and {len(tasks) - 10} more tasks (not shown for brevity)\n"
                
                # Add task list summary (truncated)
                if "tasks" in self.project_data:
                    tasks = self.project_data["tasks"]
                    project_summary += f"\nTask Overview (showing up to 10 of {len(tasks)} tasks):\n"
                    
                    for i, task in enumerate(tasks[:10]):
                        task_id = task.get("id", "unknown")
                        task_name = task.get("nom", f"Task {task_id}")
                        task_status = task.get("statut", "unknown")
                        project_summary += f"- Task {task_id}: {task_name} (Status: {task_status})\n"
                    
                    if len(tasks) > 10:
                        project_summary += f"... and {len(tasks) - 10} more tasks\n"
                
                system_message["content"] += project_summary
                
            except Exception as e:
                system_message["content"] += f"Error parsing project data: {str(e)}"
        else:
            system_message["content"] += "No project data available yet."
        
        # Add instructions for answering
        system_message["content"] += (
            "\n\nGuidelines for answering questions:\n"
            "1. If asked about specific task details, provide the most relevant information including exact values from the JSON.\n"
            "2. For timeline questions, reference the critical path and project duration.\n"
            "3. If asked about risks, suggest mitigation strategies.\n"
            "4. Keep answers concise but informative.\n"
            "5. If you don't have enough information to answer accurately, say so.\n"
            "6. Always use the exact data from the project file to answer questions.\n"
            "7. Remember all task details, dependencies, durations, and other information from the JSON file.\n"
            "8. You should be able to recall specific tasks by ID or name when asked.\n"
            "9. If the project has French field names like 'nom_projet', 'taches', etc., translate them appropriately in your answers."
        )
        
        self.conversation_history.append(system_message)
    
    def update_project_data(self, project_data):
        """
        Update project data and refresh system message
        
        Args:
            project_data (dict): New project data
        """
        self.project_data = project_data
        self._add_system_message()
    
    def ask(self, question, conversation_id=None):
        """
        Ask a question about the project
        
        Args:
            question (str): User's question
            conversation_id (str, optional): ID for conversation context
            
        Returns:
            dict: Response with success status and message
        """
        # Check if API key is available
        if not self.has_api_key():
            simulated_response = self._simulate_response(question)
            return {
                'success': True,
                'response': simulated_response,
                'simulated': True
            }
            
        # Get conversation history based on ID
        if conversation_id and conversation_id in self.conversation_store:
            self.conversation_history = self.conversation_store[conversation_id]
        
        try:
            # Add user question to conversation history
            self.conversation_history.append({"role": "user", "content": question})
            
            # Prepare messages, ensuring we don't exceed token limits
            messages = self._prepare_messages()
            
            # Call OpenAI API
            completion = openai.ChatCompletion.create(
                model="gpt-4",  # Using GPT-4, can be changed to other models
                messages=messages,
                max_tokens=1024,
                temperature=0.5,  # Lower temperature for more focused responses
                top_p=0.9,
                frequency_penalty=0.2,
                presence_penalty=0.2
            )
            
            # Extract response
            response = completion.choices[0].message['content'].strip()
            
            # Add assistant's response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Store conversation history if ID provided
            if conversation_id:
                self.conversation_store[conversation_id] = self.conversation_history
                
            return {
                'success': True,
                'response': response,
                'conversation_id': conversation_id
            }
        
        except Exception as e:
            error_msg = f"Error communicating with OpenAI: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _prepare_messages(self):
        """
        Prepare messages for API request, handling token limits
        
        Returns:
            list: List of message dicts ready for API
        """
        # Always include the system message
        messages = [self.conversation_history[0]]
        
        # Include up to last 10 messages (to stay within token limits)
        recent_messages = self.conversation_history[1:11]
        messages.extend(recent_messages)
        
        return messages
    
    def analyze_json(self, json_data):
        """
        Use ChatGPT to analyze raw project JSON data and extract structured information
        
        Args:
            json_data (dict): Raw JSON project data
            
        Returns:
            dict: Structured project information including:
                - tasks: normalized task list
                - metadata: project metadata
                - dashboard_data: data for visualizations
                - critical_path: critical path analysis
                - risks: identified project risks
        """
        if not self.has_api_key():
            print("Warning: No API key available. Using simulated JSON analysis.")
            return self._simulate_json_analysis(json_data)
        
        try:
            # Special system prompt focused on JSON analysis
            system_message = {
                "role": "system",
                "content": (
                    "You are a specialized AI project management analyzer. "
                    "Your task is to analyze raw JSON project data and extract structured information. "
                    "The data may follow different schemas and structures. "
                    "Carefully analyze the data structure and extract: "
                    "1. Project metadata (name, description, dates, manager, etc.) "
                    "2. Tasks with their attributes (normalize to consistent structure) "
                    "3. Dependencies between tasks "
                    "4. Resources and their allocations "
                    "5. Critical path information "
                    "6. Risk assessment "
                    "7. Dashboard visualization data "
                    "Return your analysis in a structured JSON format with these sections. "
                    "Be exhaustive in your analysis but ensure data is normalized to consistent formats."
                )
            }
            
            # Convert JSON to string if needed
            json_str = json_data if isinstance(json_data, str) else json.dumps(json_data, indent=2)
            
            # User message contains the JSON data
            user_message = {
                "role": "user", 
                "content": f"Analyze this project JSON data and extract structured information:\n```json\n{json_str}\n```"
            }
            
            # Request structured analysis from ChatGPT
            completion = openai.ChatCompletion.create(
                model="gpt-4",  # Use most capable model for complex JSON analysis
                messages=[system_message, user_message],
                temperature=0.2,  # Lower temperature for more deterministic results
                max_tokens=4000,  # Allow larger response for detailed analysis
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract structured response
            response_text = completion.choices[0].message['content'].strip()
            print(f"Received ChatGPT response of length: {len(response_text)}")
            
            # Extract JSON from the response
            # First try to extract JSON block if enclosed in ```json ... ```
            json_match = re.search(r'```json\n(.+?)\n```', response_text, re.DOTALL)
            if json_match:
                print("Found JSON code block in response")
                response_text = json_match.group(1)
            else:
                # Try other common patterns
                json_match = re.search(r'```(.+?)```', response_text, re.DOTALL)
                if json_match:
                    print("Found generic code block in response")
                    response_text = json_match.group(1)
                else:
                    print("No code block found, treating entire response as JSON")
            
            try:
                # Try to parse the structured data
                analysis = json.loads(response_text)
                print(f"Successfully parsed JSON response with {len(analysis.keys()) if isinstance(analysis, dict) else 0} top-level keys")
                
                # Ensure we have minimum required fields
                if isinstance(analysis, dict):
                    if 'tasks' not in analysis or not analysis['tasks']:
                        print("WARNING: No tasks found in AI analysis, adding minimal task data")
                        analysis['tasks'] = [{
                            'id': '1',
                            'name': 'Project Start',
                            'duration': 1,
                            'status': 'not_started',
                            'dependencies': []
                        }]
                    
                    if 'metadata' not in analysis:
                        print("WARNING: No metadata found in AI analysis, adding default metadata")
                        analysis['metadata'] = {'project_name': 'Untitled Project'}
                    
                    if 'dashboard_data' not in analysis:
                        print("WARNING: No dashboard data found in AI analysis, adding default dashboard data")
                        analysis['dashboard_data'] = {
                            'status_distribution': {'not_started': len(analysis['tasks'])},
                            'timeline': {'start': '2023-01-01', 'end': '2023-12-31'}
                        }
                else:
                    print("WARNING: AI analysis result is not a dictionary, creating default structure")
                    analysis = {
                        'tasks': [{
                            'id': '1',
                            'name': 'Project Start',
                            'duration': 1,
                            'status': 'not_started',
                            'dependencies': []
                        }],
                        'metadata': {'project_name': 'Untitled Project'},
                        'dashboard_data': {
                            'status_distribution': {'not_started': 1},
                            'timeline': {'start': '2023-01-01', 'end': '2023-12-31'}
                        }
                    }
                
                return analysis
            except json.JSONDecodeError as je:
                print(f"ERROR: Could not parse JSON from response: {str(je)}")
                print(f"First 500 chars of response_text: {response_text[:500]}...")
                # Return a default analysis structure
                return {
                    'tasks': [{
                        'id': '1',
                        'name': 'Project Start',
                        'duration': 1,
                        'status': 'not_started',
                        'dependencies': []
                    }],
                    'metadata': {'project_name': 'Untitled Project'},
                    'dashboard_data': {
                        'status_distribution': {'not_started': 1},
                        'timeline': {'start': '2023-01-01', 'end': '2023-12-31'}
                    }
                }
        
        except Exception as e:
            print(f"Error during ChatGPT JSON analysis: {str(e)}")
            # Fall back to simulated analysis
            return self._simulate_json_analysis(json_data)
    
    def _simulate_json_analysis(self, json_data):
        """
        Simulate JSON analysis when API key is not available
        
        Args:
            json_data (dict): Raw JSON project data
            
        Returns:
            dict: Basic simulated analysis
        """
        # Basic task detection
        tasks = []
        metadata = {"project_name": "Untitled Project"}
        detected_tasks = []
        
        # Try to find tasks array
        if isinstance(json_data, dict):
            # Look for common task list keys
            task_keys = ["tasks", "items", "activities", "work_items", "issues"]
            for key in task_keys:
                if key in json_data and isinstance(json_data[key], list):
                    detected_tasks = json_data[key]
                    break
            
            # Try to find project metadata
            name_keys = ["name", "title", "project_name", "projectName"]
            for key in name_keys:
                if key in json_data and isinstance(json_data[key], str):
                    metadata["project_name"] = json_data[key]
                    break
        
        # Process detected tasks
        for i, task in enumerate(detected_tasks):
            if not isinstance(task, dict):
                continue
                
            # Try to extract task data
            task_id = None
            if "id" in task:
                task_id = task["id"]
            elif "ID" in task:
                task_id = task["ID"]
            else:
                task_id = str(i + 1)
            
            # Name
            task_name = None
            name_keys = ["name", "title", "task", "description"]
            for key in name_keys:
                if key in task and task[key]:
                    task_name = task[key]
                    break
            
            # Create normalized task
            normalized_task = {
                "id": str(task_id),
                "name": task_name or f"Task {task_id}",
                "duration": task.get("duration", 1),
                "dependencies": [],
                "resources": [],
                "status": "not_started"
            }
            tasks.append(normalized_task)
        
        # Return basic analysis
        return {
            "tasks": tasks,
            "metadata": metadata,
            "dashboard_data": {
                "status_distribution": {"not_started": len(tasks)},
                "timeline": {"start": "2023-01-01", "end": "2023-12-31"}
            },
            "critical_path": [],
            "risks": []
        }
        
    def _simulate_response(self, question):
        """
        Simulate a response when API key is not available
        
        Args:
            question (str): User's question
            
        Returns:
            str: Simulated response
        """
        # Add question to history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Predefined responses based on question keywords
        question_lower = question.lower()
        
        if "critical path" in question_lower:
            response = "The critical path represents the sequence of tasks that determine the minimum project duration. Based on the project data, these are the tasks that need special attention as any delay will impact the overall project timeline."
        
        elif "risk" in question_lower or "risks" in question_lower:
            response = "The project risk assessment looks at potential issues like resource allocation, dependencies, and bottlenecks. Proper risk management should include regular reviews and mitigation strategies."
        
        elif "duration" in question_lower or "timeline" in question_lower or "schedule" in question_lower:
            response = "Project duration is calculated based on task dependencies and estimated task durations. The critical path determines the minimum project completion time."
        
        elif "resources" in question_lower or "resource" in question_lower:
            response = "Resource allocation is important for project success. Overallocated resources can cause bottlenecks and delays, while underutilized resources represent inefficiency. Each task should have clear resource assignments."
        
        elif "task" in question_lower and any(word in question_lower for word in ["status", "progress", "complete"]):
            response = "Task status tracking helps monitor project progress. Tasks can be not started, in progress, completed, or delayed. The dashboard shows the current status distribution."
        
        else:
            response = "I can help answer questions about project details including tasks, timeline, critical path, resources, and risks. Could you please provide a more specific question about the project?"
        
        # Add simulated response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Add note about simulated mode
        response += "\n\n(Note: This is a simulated response as no OpenAI API key was provided. For more accurate and detailed answers, please add an API key.)"
        
        return response
