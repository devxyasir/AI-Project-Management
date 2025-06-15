"""
JSON Parser Module
Parses project JSON files and extracts relevant information
"""
from datetime import datetime, timedelta
import json


class ProjectParser:
    """
    Parser for project JSON files
    Handles various JSON structures and provides task data extraction
    """
    
    def __init__(self, json_data=None, file_path=None):
        """
        Initialize parser with either JSON data or file path
        
        Args:
            json_data (dict): JSON data as dictionary
            file_path (str): Path to JSON file
        """
        self.data = None
        
        if json_data:
            self.data = json_data
        elif file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                raise ValueError(f"Could not parse JSON file: {str(e)}")
                
        # Validate data
        if not self.data:
            raise ValueError("No data provided")
                
    def parse_json(self, json_data):
        """
        Parse JSON data and initialize the parser
        
        Args:
            json_data (dict): JSON data as dictionary
        """
        if not json_data:
            raise ValueError("No data provided")
            
        self.data = json_data
        return True

    def get_tasks(self):
        """
        Extract tasks from project data with normalized structure
        
        Returns:
            list: List of normalized task objects
        """
        if not self.data:
            return []
            
        # Handle different JSON structures
        tasks_key = None
        for key in ['taches', 'tasks', 'activites']:
            if key in self.data:
                tasks_key = key
                break
        
        if not tasks_key:
            return []
            
        raw_tasks = self.data[tasks_key]
        normalized_tasks = []
        
        for task in raw_tasks:
            # Map task properties with different possible naming conventions
            task_id = task.get('id', task.get('identifiant', task.get('task_id', None)))
            
            # Skip tasks without ID
            if task_id is None:
                continue
                
            name_key = self._get_first_match(task, ['nom', 'name', 'titre', 'title'])
            desc_key = self._get_first_match(task, ['description', 'desc', 'detail', 'details'])
            duration_key = self._get_first_match(task, ['duree_estimee', 'duree', 'duration', 'estimated_duration'])
            duration_unit_key = self._get_first_match(task, ['unite_duree', 'duration_unit', 'unite'])
            pred_key = self._get_first_match(task, ['predecesseurs', 'predecessors', 'dependances', 'dependencies'])
            resources_key = self._get_first_match(task, ['ressources_requises', 'resources', 'ressources'])
            status_key = self._get_first_match(task, ['statut', 'status', 'etat'])
            
            # Handle different status values
            status = task.get(status_key, 'non_commencee') if status_key else 'non_commencee'
            normalized_status = self._normalize_status(status)
            
            normalized_task = {
                'id': task_id,
                'nom': task.get(name_key, f"Task {task_id}"),
                'description': task.get(desc_key, ''),
                'duree_estimee': task.get(duration_key, 1),
                'unite_duree': task.get(duration_unit_key, 'jours'),
                'predecesseurs': task.get(pred_key, []),
                'ressources_requises': task.get(resources_key, []),
                'statut': normalized_status
            }
            
            normalized_tasks.append(normalized_task)
            
        return normalized_tasks
    
    def get_summary(self):
        """
        Generate project summary with metadata
        
        Returns:
            dict: Project summary including tasks, count, and duration
        """
        if not self.data:
            return {"error": "No data available"}
            
        # Extract project metadata
        project_name = self._get_project_name()
        project_manager = self._get_project_manager()
        
        # Get normalized tasks
        tasks = self.get_tasks()
        
        # Calculate total duration (simplistic - doesn't account for parallel tasks)
        total_duration = sum(task.get('duree_estimee', 0) for task in tasks)
        duration_unit = 'jours'  # Default
        
        # Try to determine most common duration unit
        if tasks:
            unit_counts = {}
            for task in tasks:
                unit = task.get('unite_duree', 'jours')
                unit_counts[unit] = unit_counts.get(unit, 0) + 1
            
            if unit_counts:
                duration_unit = max(unit_counts.items(), key=lambda x: x[1])[0]
        
        # Count task statuses
        status_counts = {
            'non_commencee': 0,
            'en_cours': 0,
            'terminee': 0,
            'en_retard': 0
        }
        
        for task in tasks:
            status = task.get('statut', 'non_commencee')
            if status in status_counts:
                status_counts[status] += 1
                
        # Calculate completion percentage
        completed = status_counts.get('terminee', 0)
        completion_percentage = round((completed / len(tasks) * 100) if tasks else 0, 1)
        
        # Build summary
        summary = {
            'project_name': project_name,
            'project_manager': project_manager,
            'task_count': len(tasks),
            'total_duration': total_duration,
            'duration_unit': duration_unit,
            'status_counts': status_counts,
            'completion_percentage': completion_percentage,
            'tasks': tasks,
            'raw_tasks': tasks,  # Keep the normalized raw tasks for other modules
            'start_date': self._extract_start_date(),
            'end_date': self._extract_end_date()
        }
        
        return summary
    
    def get_task_by_id(self, task_id):
        """
        Find task by ID
        
        Args:
            task_id: Task ID to find
            
        Returns:
            dict: Task data or None if not found
        """
        tasks = self.get_tasks()
        for task in tasks:
            if task.get('id') == task_id:
                return task
        return None
    
    def _get_project_name(self):
        """Extract project name from data"""
        name_keys = ['nom_projet', 'project_name', 'nom', 'name', 'titre', 'title']
        for key in name_keys:
            if key in self.data:
                return self.data[key]
        return "Untitled Project"
    
    def _get_project_manager(self):
        """Extract project manager from data"""
        manager_keys = ['responsable', 'manager', 'chef_projet', 'project_manager']
        for key in manager_keys:
            if key in self.data:
                return self.data[key]
        return None
    
    def _get_first_match(self, obj, possible_keys):
        """Return first key that exists in object"""
        for key in possible_keys:
            if key in obj:
                return key
        return None
        
    def _normalize_status(self, status):
        """Normalize task status to standard values"""
        status_lower = str(status).lower()
        
        # Map various status terms to standardized values
        if status_lower in ['terminé', 'terminee', 'done', 'complete', 'completed', 'finished']:
            return 'terminee'
        elif status_lower in ['en cours', 'en_cours', 'in progress', 'ongoing', 'in_progress']:
            return 'en_cours'
        elif status_lower in ['non commencé', 'non_commencee', 'not started', 'todo', 'to_do', 'to do', 'planned']:
            return 'non_commencee'
        elif status_lower in ['en retard', 'en_retard', 'late', 'delayed', 'overdue']:
            return 'en_retard'
        else:
            return 'non_commencee'  # Default to not started
    
    def get_dashboard_data(self):
        """
        Generate dashboard visualization data from project tasks
        
        Returns:
            dict: Dashboard data for visualizations
        """
        tasks = self.get_tasks()
        status_distribution = self.get_task_status_counts()
        
        # Calculate timeline
        start_date = self._extract_start_date()
        end_date = self._extract_end_date()
        
        # Get resource allocation
        resource_allocation = self.get_resource_allocation()
        
        # Calculate completion percentage
        completed = status_distribution.get('terminee', 0)
        completion_percentage = round((completed / len(tasks) * 100) if tasks else 0, 1)
        
        # Build dashboard data
        dashboard_data = {
            'status_distribution': status_distribution,
            'timeline': {
                'start': start_date,
                'end': end_date
            },
            'completion_percentage': completion_percentage,
            'resource_allocation': resource_allocation
        }
        
        return dashboard_data
    
    def get_task_status_counts(self):
        """Get counts of tasks by status"""
        tasks = self.get_tasks()
        status_counts = {
            'non_commencee': 0,
            'en_cours': 0,
            'terminee': 0,
            'en_retard': 0
        }
        
        for task in tasks:
            status = task.get('statut', 'non_commencee')
            if status in status_counts:
                status_counts[status] += 1
        
        return status_counts
    
    def get_completion_percentage(self):
        """Calculate project completion percentage"""
        status_counts = self.get_task_status_counts()
        tasks = self.get_tasks()
        
        completed = status_counts.get('terminee', 0)
        return round((completed / len(tasks) * 100) if tasks else 0, 1)
    
    def get_resource_allocation(self):
        """Get resource allocation across tasks"""
        tasks = self.get_tasks()
        resource_allocation = {}
        
        for task in tasks:
            resources = task.get('ressources_requises', [])
            for resource in resources:
                if isinstance(resource, str):
                    resource_name = resource
                else:
                    resource_name = resource.get('name', str(resource))
                    
                if resource_name not in resource_allocation:
                    resource_allocation[resource_name] = 1
                else:
                    resource_allocation[resource_name] += 1
        
        return resource_allocation
    
    def _extract_start_date(self):
        """Extract or estimate project start date"""
        # Try to find project start date in data
        date_keys = ['date_debut', 'start_date', 'debut', 'start']
        for key in date_keys:
            if key in self.data and self.data[key]:
                return self.data[key]
        
        # Default to current date if not found
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_end_date(self):
        """Extract or estimate project end date"""
        # Try to find project end date in data
        date_keys = ['date_fin', 'end_date', 'fin', 'end', 'date_fin_prevue']
        for key in date_keys:
            if key in self.data and self.data[key]:
                return self.data[key]
        
        # Default to 30 days from now if not found using timedelta
        return (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
