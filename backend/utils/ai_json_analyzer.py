"""
AI-powered JSON Analyzer Module
Analyzes and extracts structure from arbitrary JSON project data
"""
import json
import re
import logging
import networkx as nx
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AIJsonAnalyzer:
    """
    AI-powered JSON analyzer that can detect structure of any project data
    and extract standardized information regardless of the format
    """
    
    def __init__(self, json_data: Union[Dict, str, None] = None, file_path: Optional[str] = None):
        """
        Initialize the analyzer with either JSON data or a file path
        
        Args:
            json_data: JSON data as dictionary or JSON string
            file_path: Path to JSON file
        """
        self.raw_data = None
        self.structured_data = {}
        self.schema = {}
        self.field_mappings = {}
        
        # Load data from one of the sources
        if json_data is not None:
            if isinstance(json_data, dict):
                self.raw_data = json_data
            elif isinstance(json_data, str):
                try:
                    self.raw_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON string: {str(e)}")
                    raise ValueError(f"Invalid JSON string: {str(e)}")
        elif file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.raw_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load JSON from file {file_path}: {str(e)}")
                raise ValueError(f"Could not read JSON file: {str(e)}")
        
        # Validate data
        if not self.raw_data:
            raise ValueError("No valid JSON data provided")
            
        # Analyze the JSON structure
        self._analyze()
    
    def _analyze(self):
        """
        Analyze the JSON structure and extract standardized project information
        """
        logger.info("Starting JSON structure analysis")
        
        # Step 1: Detect project metadata
        self._detect_project_metadata()
        
        # Step 2: Find and normalize tasks
        self._detect_tasks()
        
        # Step 3: Create field mappings from original to standardized schema
        self._create_field_mappings()
        
        # Step 4: Calculate and store critical path if tasks are available
        if self.structured_data.get('tasks', []):
            # Critical path is calculated on demand to save resources
            # but we pre-calculate it once for dashboard data
            _ = self.calculate_critical_path()
        
        # Analysis is complete
        logger.info("JSON analysis complete with:"
                   f" {len(self.structured_data.get('tasks', []))} tasks,"
                   f" schema={self.schema}")
        
        # Set analysis status
        self.analyzed = True
        
    def _detect_project_metadata(self):
        """
        Detects and extracts project metadata like name, description, manager, etc.
        """
        logger.info("Detecting project metadata")
        
        # Common keys for project name
        name_keys = ['project_name', 'name', 'nom_projet', 'nom', 'title', 'titre', 'project']
        
        # Find project name
        self.structured_data['project_name'] = self._find_value_by_keys(self.raw_data, name_keys) or "Untitled Project"
        
        # Common keys for project description
        desc_keys = ['description', 'desc', 'project_description', 'details']
        self.structured_data['description'] = self._find_value_by_keys(self.raw_data, desc_keys) or ""
        
        # Common keys for project manager/owner
        manager_keys = ['manager', 'project_manager', 'owner', 'responsable', 'chef_projet']
        self.structured_data['manager'] = self._find_value_by_keys(self.raw_data, manager_keys) or "Unknown"
        
        # Try to find start and end dates
        date_keys = {
            'start_date': ['start_date', 'date_debut', 'start', 'debut', 'date_start'],
            'end_date': ['end_date', 'date_fin', 'end', 'fin', 'date_end', 'deadline']
        }
        
        for date_type, keys in date_keys.items():
            date_value = self._find_value_by_keys(self.raw_data, keys)
            if date_value:
                try:
                    # Try to parse as ISO date if it's a string
                    if isinstance(date_value, str):
                        # Try common date formats
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                            try:
                                parsed_date = datetime.strptime(date_value, fmt).isoformat().split('T')[0]
                                self.structured_data[date_type] = parsed_date
                                break
                            except ValueError:
                                continue
                    else:
                        self.structured_data[date_type] = date_value
                except Exception as e:
                    logger.warning(f"Failed to parse {date_type}: {str(e)}")
        
        logger.info(f"Found project: {self.structured_data['project_name']}")
    
    def _find_value_by_keys(self, obj: Dict, possible_keys: List[str]) -> Any:
        """
        Find a value in a dictionary using a list of possible keys
        
        Args:
            obj: Dictionary to search in
            possible_keys: List of possible key names
            
        Returns:
            The value if found, None otherwise
        """
        for key in possible_keys:
            if key in obj:
                return obj[key]
        return None
        
    def _detect_tasks(self):
        """
        Detects and extracts tasks from the JSON structure.
        This method is smart enough to find tasks in various formats and structures.
        """
        logger.info("Detecting tasks")
        
        # Common keys for task lists
        task_list_keys = ['tasks', 'taches', 'activities', 'activites', 'items', 'work_items']
        task_list = None
        
        # First try direct access - task list at root level
        for key in task_list_keys:
            if key in self.raw_data and isinstance(self.raw_data[key], list):
                task_list = self.raw_data[key]
                break
                
        # If not found at root level, try to search deeper
        if task_list is None:
            # Look for arrays of dictionaries that might be tasks
            for key, value in self.raw_data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    # Check if items in this list look like tasks
                    sample_item = value[0]
                    # Task-like characteristics: has id, name, duration or similar fields
                    task_indicators = [
                        any(id_key in sample_item for id_key in ['id', 'task_id', 'identifiant']),
                        any(name_key in sample_item for name_key in ['name', 'nom', 'title', 'titre']),
                        any(dur_key in sample_item for dur_key in ['duration', 'duree', 'length', 'days'])
                    ]
                    
                    if sum(task_indicators) >= 2:  # If it has at least 2 task-like attributes
                        task_list = value
                        break
        
        if not task_list:
            logger.warning("No tasks found in JSON data")
            self.structured_data['tasks'] = []
            return
            
        # Now normalize each task
        normalized_tasks = []
        for i, task in enumerate(task_list):
            normalized_task = self._normalize_task(task, i)
            if normalized_task:  # Skip any task that couldn't be normalized
                normalized_tasks.append(normalized_task)
                
        self.structured_data['tasks'] = normalized_tasks
        self.structured_data['task_count'] = len(normalized_tasks)
        logger.info(f"Found {len(normalized_tasks)} tasks")
        
    def _normalize_task(self, task: Dict, index: int) -> Optional[Dict]:
        """
        Normalize a task dictionary to a standard format
        
        Args:
            task: Raw task dictionary
            index: Task index for generating ID if missing
            
        Returns:
            Standardized task dictionary
        """
        # Skip if not a dictionary
        if not isinstance(task, dict):
            return None
            
        # Generate normalized task
        normalized = {}
        
        # Find task ID
        id_keys = ['id', 'task_id', 'identifiant', 'ID', 'key', 'uid']
        task_id = self._find_value_by_keys(task, id_keys)
        if task_id is None:
            # Generate an ID if none exists
            task_id = f"task_{index + 1}"
        
        normalized['id'] = str(task_id)  # Ensure ID is string
        
        # Find task name
        name_keys = ['name', 'nom', 'title', 'titre', 'task_name']
        task_name = self._find_value_by_keys(task, name_keys)
        normalized['name'] = task_name or f"Task {task_id}"
        
        # Find task description
        desc_keys = ['description', 'desc', 'details', 'notes']
        normalized['description'] = self._find_value_by_keys(task, desc_keys) or ""
        
        # Find task duration
        duration_keys = ['duration', 'duree', 'duree_estimee', 'days', 'effort', 'length']
        normalized['duration'] = self._find_value_by_keys(task, duration_keys) or 1
        
        # Try to determine duration unit
        unit_keys = ['unit', 'duration_unit', 'unite', 'unite_duree', 'time_unit']
        normalized['duration_unit'] = self._find_value_by_keys(task, unit_keys) or 'days'
        
        # Find dependencies/predecessors
        pred_keys = ['predecessors', 'dependencies', 'depends_on', 'predecesseurs', 'dependances']
        predecessors = self._find_value_by_keys(task, pred_keys) or []
        
        # Handle different dependency formats
        if isinstance(predecessors, str):
            # Convert comma-separated string to list
            predecessors = [p.strip() for p in predecessors.split(',')]
        elif not isinstance(predecessors, list):
            # If single value that's not a list, wrap in list
            predecessors = [str(predecessors)]
            
        normalized['dependencies'] = predecessors
        
        # Find resources
        resource_keys = ['resources', 'resource', 'assignee', 'assigned_to', 'ressources', 'responsible']
        resources = self._find_value_by_keys(task, resource_keys) or []
        
        # Handle different resource formats
        if isinstance(resources, str):
            resources = [resources]
        elif not isinstance(resources, list):
            resources = [str(resources)]
            
        normalized['resources'] = resources
        
        # Find task status
        status_keys = ['status', 'state', 'statut', 'etat', 'task_status']
        status = self._find_value_by_keys(task, status_keys) or 'not_started'
        normalized['status'] = self._normalize_status(status)
        
        # Preserve original task
        normalized['original'] = task
        
        return normalized
        
    def _normalize_status(self, status) -> str:
        """
        Normalize task status to a standard format
        
        Args:
            status: Raw status value
            
        Returns:
            Normalized status string
        """
        if not status:
            return 'not_started'
            
        status_str = str(status).lower().strip()
        
        # Map to standard statuses
        if status_str in ['completed', 'complete', 'done', 'finished', 'termine', 'terminé', 'terminee']:
            return 'completed'
        elif status_str in ['in progress', 'in_progress', 'ongoing', 'started', 'en cours', 'en_cours']:
            return 'in_progress'
        elif status_str in ['not started', 'not_started', 'to do', 'to-do', 'todo', 'planned', 'non commencé', 'non_commencee']:
            return 'not_started'
        elif status_str in ['delayed', 'late', 'overdue', 'behind', 'en retard', 'en_retard']:
            return 'delayed'
        elif status_str in ['cancelled', 'canceled', 'dropped', 'annulé', 'annule']:
            return 'cancelled'
        else:
            return 'not_started'  # Default status
    
    def _create_field_mappings(self):
        """
        Create mappings from original field names to standardized field names
        """
        # Skip if no tasks found
        if not self.structured_data.get('tasks', []):
            return
            
        # Sample the first task's original data
        sample_task = self.structured_data['tasks'][0]
        if not sample_task or not sample_task.get('original'):
            return
            
        original = sample_task['original']
        mappings = {}
        
        # Detect field mappings
        for std_field, std_value in sample_task.items():
            if std_field == 'original':
                continue
                
            # Find which original field maps to this standardized field
            for orig_field, orig_value in original.items():
                if std_value == orig_value:
                    mappings[std_field] = orig_field
                    break
        
        self.field_mappings = mappings
        logger.info(f"Created field mappings: {mappings}")
    
    def get_summary(self) -> Dict:
        """
        Generate a project summary with metadata and statistics
        
        Returns:
            Dict containing project summary and metadata
        """
        if not self.structured_data:
            return {}
            
        tasks = self.structured_data.get('tasks', [])
        task_count = len(tasks)
        
        # Calculate total duration
        total_duration = sum(task.get('duration', 0) for task in tasks)
        
        # Count tasks by status
        status_counts = {
            'not_started': 0,
            'in_progress': 0,
            'completed': 0,
            'delayed': 0,
            'cancelled': 0
        }
        
        for task in tasks:
            status = task.get('status', 'not_started')
            if status in status_counts:
                status_counts[status] += 1
                
        # Calculate completion percentage
        completion_pct = 0
        if task_count > 0:
            completion_pct = round((status_counts['completed'] / task_count) * 100, 1)
            
        # Build summary
        summary = {
            'project_name': self.structured_data.get('project_name', 'Untitled Project'),
            'description': self.structured_data.get('description', ''),
            'manager': self.structured_data.get('manager', 'Unknown'),
            'start_date': self.structured_data.get('start_date', ''),
            'end_date': self.structured_data.get('end_date', ''),
            'task_count': task_count,
            'total_duration': total_duration,
            'duration_unit': 'days',  # Default
            'status_counts': status_counts,
            'completion_percentage': completion_pct,
            'schema': self.schema,
            'field_mappings': self.field_mappings,
            # Add raw data for AI context
            'raw_project': self.raw_data
        }
        
        return summary
    
    def get_tasks(self) -> List[Dict]:
        """
        Get normalized tasks
        
        Returns:
            List of standardized task dictionaries
        """
        return self.structured_data.get('tasks', [])
        
    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """
        Find a task by its ID
        
        Args:
            task_id: Task ID to find
            
        Returns:
            Task dictionary or None if not found
        """
        tasks = self.structured_data.get('tasks', [])
        for task in tasks:
            if str(task.get('id', '')) == str(task_id):
                return task
        return None
    
    def calculate_critical_path(self) -> Dict:
        """
        Calculate the critical path of the project
        
        Returns:
            Dictionary with critical path information
        """
        tasks = self.get_tasks()
        if not tasks:
            return {
                'critical_path': [],
                'critical_tasks': [],
                'critical_path_length': 0
            }
            
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add all tasks as nodes
        task_map = {}
        for task in tasks:
            task_id = task.get('id')
            if task_id:
                duration = float(task.get('duration', 1))  # Use float for calculations
                G.add_node(task_id, weight=duration, task=task)
                task_map[task_id] = task
        
        # Add edges based on dependencies
        for task in tasks:
            task_id = task.get('id')
            if not task_id:
                continue
                
            dependencies = task.get('dependencies', [])
            for dep in dependencies:
                if dep and dep in task_map:  # Only add valid dependencies
                    G.add_edge(dep, task_id)
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                logger.warning(f"Detected cycles in task dependencies: {cycles}")
                # Remove some edges to break cycles
                for cycle in cycles:
                    if len(cycle) >= 2:
                        G.remove_edge(cycle[0], cycle[1])
                        logger.info(f"Removed edge {cycle[0]} -> {cycle[1]} to break cycle")
        except:
            # Simple cycles not available, use alternative approach
            # Try to make the graph acyclic
            if not nx.is_directed_acyclic_graph(G):
                G = nx.DiGraph([(u, v) for u, v in G.edges() if u < v])  # Use a heuristic to break cycles
                logger.warning("Graph had cycles, converted to acyclic")
        
        # Calculate longest path
        critical_path = []
        critical_path_length = 0
        critical_tasks = []
        
        # Find all paths and identify the longest
        if nx.is_directed_acyclic_graph(G):
            # Find all start and end nodes
            start_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
            end_nodes = [node for node in G.nodes() if G.out_degree(node) == 0]
            
            longest_path = []
            max_length = 0
            
            # Check all start to end paths
            for start in start_nodes:
                for end in end_nodes:
                    try:
                        for path in nx.all_simple_paths(G, start, end):
                            path_length = sum(G.nodes[node]['weight'] for node in path)
                            if path_length > max_length:
                                max_length = path_length
                                longest_path = path
                    except nx.NetworkXNoPath:
                        continue
            
            critical_path = longest_path
            critical_path_length = max_length
            critical_tasks = [task_map[task_id] for task_id in critical_path if task_id in task_map]
            
            # Calculate slack times for all tasks
            # (This is a simplified version that doesn't account for all dependencies)
            earliest_start = {}
            latest_start = {}
            
            # Forward pass to calculate earliest start times
            for node in nx.topological_sort(G):
                # Start nodes can start at time 0
                if G.in_degree(node) == 0:
                    earliest_start[node] = 0
                else:
                    # Node can start after all predecessors are done
                    earliest_start[node] = max(
                        [earliest_start[pred] + G.nodes[pred]['weight'] 
                         for pred in G.predecessors(node)], default=0
                    )
                        
            # Find project completion time
            project_duration = max(
                [earliest_start[node] + G.nodes[node]['weight'] 
                 for node in G.nodes()], default=0
            )
                    
            # Backward pass for latest start times
            for node in reversed(list(nx.topological_sort(G))):
                if G.out_degree(node) == 0:  # End tasks
                    latest_start[node] = project_duration - G.nodes[node]['weight']
                else:
                    # Latest start is determined by successors
                    latest_start[node] = min(
                        [latest_start[succ] - G.nodes[node]['weight'] 
                         for succ in G.successors(node)], 
                        default=project_duration - G.nodes[node]['weight']
                    )
            
            # Calculate slack for each task
            task_analysis = []
            for node in G.nodes():
                slack = latest_start[node] - earliest_start[node]
                task_data = task_map.get(node, {})
                
                task_analysis.append({
                    'id': node,
                    'name': task_data.get('name', f'Task {node}'),
                    'duration': G.nodes[node]['weight'],
                    'earliest_start': earliest_start[node],
                    'latest_start': latest_start[node],
                    'slack': slack,
                    'is_critical': slack == 0
                })
        
        # Return critical path details
        return {
            'critical_path': critical_path,  # List of task IDs in the critical path
            'critical_tasks': critical_tasks,  # Full task data for critical path
            'critical_path_length': critical_path_length,  # Total duration of critical path
            'task_analysis': task_analysis if 'task_analysis' in locals() else [],  # Detailed task timing analysis
            'project_duration': project_duration if 'project_duration' in locals() else 0  # Total project duration
        }
    
    def get_dashboard_data(self) -> Dict:
        """
        Generate data for dashboard visualizations
        
        Returns:
            Dictionary with dashboard-ready data
        """
        summary = self.get_summary()
        tasks = self.get_tasks()
        critical_path = self.calculate_critical_path()
        
        # Status distribution for pie chart
        status_distribution = []
        for status, count in summary.get('status_counts', {}).items():
            if count > 0:  # Only include non-zero statuses
                status_distribution.append({
                    'status': status,
                    'count': count
                })
                
        # Task timeline data
        timeline_data = []
        for task in tasks:
            timeline_data.append({
                'id': task.get('id'),
                'name': task.get('name'),
                'duration': task.get('duration', 1),
                'status': task.get('status'),
                'dependencies': task.get('dependencies', []),
                'is_critical': task.get('id') in critical_path.get('critical_path', [])
            })
        
        # Resource allocation
        resource_allocation = {}
        for task in tasks:
            resources = task.get('resources', [])
            for resource in resources:
                if resource not in resource_allocation:
                    resource_allocation[resource] = 0
                resource_allocation[resource] += task.get('duration', 1)
                
        # Convert to list format for charts
        resource_data = []
        for resource, workload in resource_allocation.items():
            resource_data.append({
                'resource': resource,
                'workload': workload
            })
            
        return {
            'project_summary': summary,
            'status_distribution': status_distribution,
            'timeline_data': timeline_data,
            'resource_allocation': resource_data,
            'critical_path': critical_path
        }
