"""
Gantt Chart Visualizer Module
Creates visual representation of project tasks timeline
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np


class GanttVisualizer:
    """
    Gantt chart visualization for project tasks
    Supports matplotlib-based charts and data generation for frontend charting
    """
    
    # Color mapping for task statuses
    STATUS_COLORS = {
        'terminee': '#28a745',     # Green for completed tasks
        'en_cours': '#007bff',     # Blue for in-progress tasks
        'non_commencee': '#6c757d', # Gray for not started tasks
        'en_retard': '#dc3545'     # Red for delayed tasks
    }
    
    def __init__(self, tasks=None):
        """
        Initialize visualizer with tasks
        
        Args:
            tasks (list): List of task objects
        """
        self.tasks = tasks or []
    
    def create_gantt_chart(self, start_date=None, figure_size=(12, 8)):
        """
        Create Gantt chart using matplotlib
        
        Args:
            start_date (datetime): Project start date
            figure_size (tuple): Figure dimensions (width, height)
            
        Returns:
            matplotlib.figure.Figure: Generated figure
        """
        if not self.tasks:
            # Return empty figure if no tasks
            fig, ax = plt.subplots(figsize=figure_size)
            ax.text(0.5, 0.5, 'No tasks to display', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            return fig
        
        # Use current date if start_date not provided
        if not start_date:
            start_date = datetime.now()
        
        # Calculate task schedule based on dependencies
        scheduled_tasks = self._schedule_tasks(start_date)
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figure_size)
        
        # Plot each task as a horizontal bar
        labels = []
        for i, task in enumerate(scheduled_tasks):
            task_id = task.get('id')
            task_name = task.get('nom', f'Task {task_id}')
            labels.append(f"{task_id}: {task_name}")
            
            start = task['start_date']
            duration = task.get('duree_estimee', 1)
            end = start + timedelta(days=duration)
            
            status = task.get('statut', 'non_commencee')
            color = self.STATUS_COLORS.get(status, self.STATUS_COLORS['non_commencee'])
            
            # Plot the task bar
            ax.barh(i, (end - start).days, left=mdates.date2num(start), 
                   color=color, edgecolor='black', alpha=0.8)
            
            # Add task duration as text
            ax.text(mdates.date2num(start) + (end - start).days / 2, i,
                   f"{duration}d", ha='center', va='center',
                   color='white', fontweight='bold')
        
        # Configure x-axis as dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
        plt.xticks(rotation=45)
        
        # Set y-axis labels and limits
        ax.set_yticks(range(len(scheduled_tasks)))
        ax.set_yticklabels(labels)
        ax.set_ylim(-0.5, len(scheduled_tasks) - 0.5)
        
        # Add grid, title and legend
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        ax.set_title('Project Gantt Chart')
        ax.set_xlabel('Date')
        
        # Create legend for task status
        status_patches = [plt.Rectangle((0, 0), 1, 1, color=color) 
                         for color in self.STATUS_COLORS.values()]
        status_labels = ['Completed', 'In Progress', 'Not Started', 'Delayed']
        ax.legend(status_patches, status_labels, loc='upper right')
        
        # Adjust layout
        fig.tight_layout()
        
        return fig
    
    def get_gantt_data(self, start_date=None):
        """
        Generate Gantt chart data for frontend visualization
        
        Args:
            start_date (datetime): Project start date
            
        Returns:
            dict: Structured data for frontend charting libraries
        """
        if not self.tasks:
            return {"tasks": []}
        
        # Use current date if start_date not provided
        if not start_date:
            start_date = datetime.now()
        
        # Calculate task schedule based on dependencies
        scheduled_tasks = self._schedule_tasks(start_date)
        
        # Format data for frontend
        gantt_data = {
            "tasks": []
        }
        
        for task in scheduled_tasks:
            task_id = task.get('id')
            task_name = task.get('nom', f'Task {task_id}')
            start = task['start_date']
            duration = task.get('duree_estimee', 1)
            end = start + timedelta(days=duration)
            status = task.get('statut', 'non_commencee')
            
            gantt_data["tasks"].append({
                "id": task_id,
                "name": task_name,
                "start_date": start.strftime('%Y-%m-%d'),
                "end_date": end.strftime('%Y-%m-%d'),
                "start_day": (start - start_date).days,
                "duration": duration,
                "status": status,
                "resources": task.get('ressources_requises', []),
                "description": task.get('description', '')
            })
        
        return gantt_data
    
    def _schedule_tasks(self, start_date):
        """
        Schedule tasks based on dependencies and durations
        
        Args:
            start_date (datetime): Project start date
            
        Returns:
            list: Tasks with calculated start dates
        """
        if not self.tasks:
            return []
            
        # Deep copy tasks to avoid modifying original
        scheduled_tasks = []
        for task in self.tasks:
            scheduled_tasks.append(task.copy())
        
        # Task start dates dictionary (ID -> start date)
        task_starts = {}
        
        # Topologically sort tasks based on dependencies
        visited = set()
        temp_mark = set()
        sorted_tasks = []
        
        def visit(task_id):
            """Recursive topological sort visit function"""
            if task_id in temp_mark:
                # Cyclic dependency detected, break cycle
                return
            if task_id not in visited:
                temp_mark.add(task_id)
                
                # Get task by id
                task = None
                for t in scheduled_tasks:
                    if t.get('id') == task_id:
                        task = t
                        break
                
                if task:
                    predecessors = task.get('predecesseurs', [])
                    for pred_id in predecessors:
                        visit(pred_id)
                    
                    visited.add(task_id)
                    temp_mark.remove(task_id)
                    sorted_tasks.append(task)
        
        # Start topological sort
        for task in scheduled_tasks:
            if task.get('id') not in visited:
                visit(task.get('id'))
        
        # Calculate start dates based on dependencies
        for task in sorted_tasks:
            task_id = task.get('id')
            predecessors = task.get('predecesseurs', [])
            
            if not predecessors:
                # If no predecessors, start at project start date
                task_starts[task_id] = start_date
            else:
                # Find the latest end date of all predecessors
                latest_end = start_date
                for pred_id in predecessors:
                    if pred_id in task_starts:
                        # Get predecessor task
                        pred_task = None
                        for t in scheduled_tasks:
                            if t.get('id') == pred_id:
                                pred_task = t
                                break
                        
                        if pred_task:
                            pred_duration = pred_task.get('duree_estimee', 1)
                            pred_end = task_starts[pred_id] + timedelta(days=pred_duration)
                            if pred_end > latest_end:
                                latest_end = pred_end
                
                task_starts[task_id] = latest_end
            
            # Add start date to task
            task['start_date'] = task_starts[task_id]
        
        return sorted_tasks
