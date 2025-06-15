"""
Critical Path Calculator Module
Calculates the critical path of a project using network analysis
"""
import networkx as nx
import json
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from collections import defaultdict


class CriticalPathCalculator:
    """
    Calculates critical path for a project
    """
    
    def __init__(self, tasks=None, critical_path=None):
        """Initialize calculator with tasks"""
        self.tasks = tasks or []
        self.critical_path_ids = set(critical_path or [])
        
        # Initialize calculation attributes
        self.earliest_start_times = {}
        self.latest_start_times = {}
        self.slack_times = {}
        
        # Build task map for easy lookup
        self.task_map = {}
        self._build_task_map()
    
    def _build_task_map(self):
        """Build a map of task ID to task object for quick lookups"""
        self.task_map = {task.get('id'): task for task in self.tasks}
    
    def get_critical_path(self):
        """
        Calculate the critical path
        
        Returns:
            list: List of task IDs on the critical path
        """
        if not self.tasks:
            return []
        
        # Build directed graph
        G = self._build_graph()
        
        # Check for cycles (critical path only valid for DAGs)
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                # Handle cycles by removing the lowest weight edge in each cycle
                for cycle in cycles:
                    self._break_cycle(G, cycle)
        except nx.NetworkXNoCycle:
            pass  # No cycles detected
        
        # Find all paths and get the longest (critical path)
        paths = []
        start_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
        end_nodes = [node for node in G.nodes() if G.out_degree(node) == 0]
        
        # If no clear start/end, the graph might be empty or malformed
        if not start_nodes or not end_nodes:
            return []
        
        # Find all paths from each start node to each end node
        for start in start_nodes:
            for end in end_nodes:
                try:
                    for path in nx.all_simple_paths(G, start, end):
                        path_weight = sum(self.task_map[node].get('duree_estimee', 0) 
                                         if node in self.task_map else 0 
                                         for node in path)
                        paths.append((path, path_weight))
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
        
        # Return the path with the highest total weight
        if paths:
            critical_path, _ = max(paths, key=lambda x: x[1])
            return list(critical_path)
        
        return []
    
    def get_critical_path_details(self):
        """
        Get detailed information about the critical path
        
        Returns:
            dict: Critical path details including tasks, duration, etc.
        """
        path_ids = self.get_critical_path()
        critical_tasks = [self.task_map[tid] for tid in path_ids if tid in self.task_map]
        
        # Determine the duration unit from tasks
        duration_unit = "jours"  # Default
        for task in self.tasks:
            if 'unite_duree' in task:
                duration_unit = task['unite_duree']
                break
            elif 'duration_unit' in task:
                duration_unit = task['duration_unit']
                break
                
        total_duration = sum(task.get('duree_estimee', 0) for task in critical_tasks)
        
        # Calculate slack time for all tasks
        slack_times = self._calculate_slack_times()
        
        # Identify near-critical tasks (tasks with slack <= 2 days)
        near_critical_tasks = []
        for task_id, slack in slack_times.items():
            if task_id not in path_ids and slack <= 2 and task_id in self.task_map:
                task_copy = self.task_map[task_id].copy()
                task_copy['slack'] = slack
                near_critical_tasks.append(task_copy)
        
        # Generate visualization data for critical and near-critical paths
        visualization_data = self._generate_path_visualization_data(path_ids, slack_times)
        
        # Find potential bottlenecks (tasks on critical path with longest duration)
        bottlenecks = []
        if critical_tasks:
            avg_duration = total_duration / len(critical_tasks)
            bottlenecks = [task for task in critical_tasks 
                          if task.get('duree_estimee', 0) > avg_duration * 1.5]
        
        return {
            "critical_path": critical_tasks,
            "total_duration": total_duration,
            "duration_unit": duration_unit,
            "path_ids": path_ids,
            "slack_times": slack_times,
            "near_critical_tasks": near_critical_tasks,
            "visualization_data": visualization_data,
            "bottlenecks": bottlenecks
        }
    
    def _build_graph(self):
        """
        Build directed graph from tasks and dependencies
        """
        G = nx.DiGraph()
        
        # Add all tasks as nodes with weight attribute
        for task in self.tasks:
            task_id = task.get('id')
            G.add_node(task_id, weight=task.get('duree_estimee', 0))
        
        # Add edges based on task dependencies
        for task in self.tasks:
            task_id = task.get('id')
            predecessors = task.get('predecesseurs', [])
            
            for pred_id in predecessors:
                if G.has_node(pred_id):
                    G.add_edge(pred_id, task_id)
        
        return G
    
    def _break_cycle(self, G, cycle):
        """
        Break a cycle in the graph by removing the lowest weight edge
        
        Args:
            G (networkx.DiGraph): Directed graph
            cycle (list): List of nodes forming a cycle
        """
        if len(cycle) < 2:
            return
        
        # Find the lowest weight edge in the cycle
        min_weight = float('inf')
        min_edge = None
        
        for i in range(len(cycle)):
            node1 = cycle[i]
            node2 = cycle[(i + 1) % len(cycle)]
            
            if G.has_edge(node1, node2):
                weight1 = self.task_map[node1].get('duree_estimee', 0) if node1 in self.task_map else 0
                if weight1 < min_weight:
                    min_weight = weight1
                    min_edge = (node1, node2)
        
        # Remove the lowest weight edge if found
        if min_edge:
            G.remove_edge(*min_edge)
    
    def _calculate_slack_times(self):
        """Calculate slack time for each task in the project"""
        if not self.earliest_start_times:
            self._calculate_earliest_start_times()
        
        if not self.latest_start_times:
            self._calculate_latest_start_times()
            
        slack_times = {}
        for task_id in self.task_map:
            if task_id in self.earliest_start_times and task_id in self.latest_start_times:
                slack_times[task_id] = self.latest_start_times[task_id] - self.earliest_start_times[task_id]
        
        return slack_times
        
    def calculate_slack_times(self):
        """Public method to calculate slack time for each task in the project"""
        return self._calculate_slack_times()
    
    def _calculate_earliest_start_times(self):
        """Calculate earliest start times for each task in the project"""
        G = self._build_graph()
        
        # Check for cycles and break them
        cycles = list(nx.simple_cycles(G))
        if cycles:
            for cycle in cycles:
                self._break_cycle(G, cycle)
        
        # Reset the earliest start times dictionary
        self.earliest_start_times = {}
        
        # Topologically sort tasks
        try:
            sorted_tasks = list(nx.topological_sort(G))
            
            # Compute earliest start time for each task
            for task_id in sorted_tasks:
                # Skip non-task nodes
                if task_id not in self.task_map:
                    continue
                    
                # Maximum of earliest finish times of predecessors
                max_pred_finish = 0
                for pred in G.predecessors(task_id):
                    if pred in self.earliest_start_times and pred in self.task_map:
                        pred_finish = self.earliest_start_times[pred] + self.task_map[pred].get('duree_estimee', 0)
                        max_pred_finish = max(max_pred_finish, pred_finish)
                
                self.earliest_start_times[task_id] = max_pred_finish
            
            return self.earliest_start_times
        
        except nx.NetworkXUnfeasible:
            # Graph has cycles, can't calculate earliest start times
            return {}
    def _calculate_latest_start_times(self):
        """Calculate latest start times for each task in the project"""
        if not self.earliest_start_times:
            self._calculate_earliest_start_times()
            
        # Find project end time    
        project_finish = 0
        for task_id in self.task_map:
            if task_id in self.earliest_start_times:
                task_finish = self.earliest_start_times[task_id] + self.task_map[task_id].get('duree_estimee', 0)
                project_finish = max(project_finish, task_finish)
        
        G = self._build_graph()
        
        # Check for cycles and break them
        cycles = list(nx.simple_cycles(G))
        if cycles:
            for cycle in cycles:
                self._break_cycle(G, cycle)
        
        # Reset the latest start times dictionary
        self.latest_start_times = {}
        
        # Topologically sort tasks
        try:
            sorted_tasks = list(nx.topological_sort(G))
            
            # Initialize latest finish for all tasks to project end
            for task_id in self.task_map:
                if task_id not in self.latest_start_times:
                    has_successors = False
                    for succ in G.successors(task_id):
                        has_successors = True
                        break
                    
                    # Tasks with no successors can finish at project end
                    if not has_successors:
                        task_duration = self.task_map[task_id].get('duree_estimee', 0)
                        self.latest_start_times[task_id] = project_finish - task_duration
            
            # Calculate latest start for each task (backward pass)
            for task_id in reversed(sorted_tasks):
                if task_id not in self.task_map:
                    continue
                
                task_duration = self.task_map[task_id].get('duree_estimee', 0)
                successors = list(G.successors(task_id))
                
                if successors:
                    # Minimum of latest start times of successors
                    min_succ_start = float('inf')
                    for succ in successors:
                        if succ in self.latest_start_times:
                            min_succ_start = min(min_succ_start, self.latest_start_times[succ])
                    
                    if min_succ_start != float('inf'):
                        self.latest_start_times[task_id] = min_succ_start - task_duration
            
            return self.latest_start_times
        
        except nx.NetworkXUnfeasible:
            # Graph has cycles, can't calculate latest start times
            return {}
            
    def generate_network_diagram(self):
        """Generate a network diagram visualization as base64 encoded PNG"""
        # Use Agg backend which doesn't require a display
        matplotlib.use('Agg')
        
        # Create directed graph
        G = self._build_graph()
        
        # Get critical path for highlighting
        critical_path = self.get_critical_path()
        # Generate critical path edges when we have at least 2 tasks in the path
        critical_path_edges = []
        if len(critical_path) >= 2:
            critical_path_edges = [(critical_path[i], critical_path[i+1]) for i in range(len(critical_path)-1)]
        
        # Set up the figure
        plt.figure(figsize=(12, 8))
        
        # Create layout for nodes
        pos = nx.spring_layout(G)
        
        # Draw regular edges and nodes
        nx.draw_networkx_edges(G, pos, edgelist=[e for e in G.edges if e not in critical_path_edges],
                             edge_color='gray', arrows=True)
        
        # Draw critical path edges
        if critical_path_edges:
            nx.draw_networkx_edges(G, pos, edgelist=critical_path_edges, 
                                 edge_color='red', width=2.0, arrows=True)
        
        # Draw nodes with different colors for critical path
        regular_nodes = [n for n in G.nodes if n not in critical_path]
        critical_nodes = [n for n in G.nodes if n in critical_path]
        
        nx.draw_networkx_nodes(G, pos, nodelist=regular_nodes, node_color='lightblue', 
                              node_size=500, alpha=0.8)
        nx.draw_networkx_nodes(G, pos, nodelist=critical_nodes, node_color='lightcoral', 
                              node_size=600, alpha=0.8)
        
        # Add labels
        labels = {}
        for node in G.nodes:
            if node in self.task_map:
                task_name = self.task_map[node].get('nom', '')
                if task_name and len(task_name) > 10:
                    task_name = task_name[:10] + '...'
                labels[node] = f"{node}\n{task_name}"
            else:
                labels[node] = str(node)
                
        nx.draw_networkx_labels(G, pos, labels=labels)
        
        # Add legend
        plt.plot([0], [0], '-', color='red', label='Critical Path', linewidth=2)
        plt.plot([0], [0], '-', color='gray', label='Normal Path')
        plt.plot([0], [0], 'o', color='lightcoral', label='Critical Task')
        plt.plot([0], [0], 'o', color='lightblue', label='Normal Task')
        plt.legend()
        
        plt.title('Project Network Diagram with Critical Path')
        plt.axis('off')
        
        # Save figure to a BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        plt.close()
        
        # Encode the PNG as base64
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode('utf-8')
        
        return {
            'image': image_data,
            'format': 'png',
            'encoding': 'base64'
        }
        
    def get_advanced_analysis(self):
        """Generate advanced schedule analysis with slack times and critical path details"""
        # Calculate critical path and slack times
        cp_ids = self.get_critical_path()
        slack_times = self._calculate_slack_times()
        self.slack_times = slack_times  # Store for reuse
        
        # Calculate earliest and latest start times
        self._calculate_earliest_start_times()
        self._calculate_latest_start_times()
        
        # Prepare detailed task schedule information
        tasks_schedule = []
        for task_id, task in self.task_map.items():
            duration = task.get('duree_estimee', 0)
            earliest_start = self.earliest_start_times.get(task_id, 0)
            latest_start = self.latest_start_times.get(task_id, 0)
            slack = slack_times.get(task_id, 0)
            
            tasks_schedule.append({
                'task_id': task_id,
                'task_name': task.get('nom', task.get('name', '')),
                'duration': duration,
                'earliest_start': earliest_start,
                'earliest_finish': earliest_start + duration,
                'latest_start': latest_start,
                'latest_finish': latest_start + duration,
                'slack': slack,
                'is_critical': task_id in cp_ids
            })
        
        # Identify bottlenecks (tasks on critical path with long durations)
        bottlenecks = []
        if self.tasks:
            avg_duration = sum(task.get('duree_estimee', 0) for task in self.tasks) / len(self.tasks)
            
            for task_id in cp_ids:
                if task_id in self.task_map:
                    task = self.task_map[task_id]
                    duration = task.get('duree_estimee', 0)
                    if duration > avg_duration * 1.5:  # 50% longer than average
                        bottlenecks.append({
                            'task_id': task_id,
                            'task_name': task.get('nom', task.get('name', '')),
                            'duration': duration,
                            'impact_factor': duration / avg_duration
                        })
        
        # Find near-critical tasks (small slack)
        near_critical = []
        for task_id, slack in slack_times.items():
            if 0 < slack <= 2 and task_id in self.task_map:
                task = self.task_map[task_id]
                near_critical.append({
                    'task_id': task_id,
                    'task_name': task.get('nom', task.get('name', '')),
                    'slack': slack
                })
        
        # Calculate project statistics
        critical_tasks_count = len(cp_ids)
        total_tasks = len(self.tasks)
        critical_duration = sum(self.task_map[tid].get('duree_estimee', 0) for tid in cp_ids if tid in self.task_map)
        total_duration = sum(task.get('duree_estimee', 0) for task in self.tasks)
        avg_slack = sum(slack_times.values()) / len(slack_times) if slack_times else 0
        
        # Generate path visualization data
        path_visualization = self._generate_path_visualization_data(cp_ids, slack_times)
        
        # Return comprehensive analysis
        return {
            'task_schedule': tasks_schedule,
            'critical_path': cp_ids,
            'bottlenecks': bottlenecks,
            'near_critical_tasks': near_critical,
            'project_statistics': {
                'critical_ratio': critical_tasks_count / total_tasks if total_tasks else 0,
                'duration_on_critical_path': critical_duration,
                'total_project_duration': critical_duration,  # Project duration is the critical path duration
                'critical_path_tasks': critical_tasks_count,
                'total_tasks': total_tasks,
                'average_slack': avg_slack
            },
            'path_visualization': path_visualization
        }
    
    def _generate_path_visualization_data(self, path_ids, slack_times):
        """Generate visualization data for critical and near-critical paths"""
        visualization_data = []
        
        # First make sure we have valid slack times
        if not slack_times:
            slack_times = self._calculate_slack_times()
            
        # Process critical path tasks
        for task_id in path_ids:
            if task_id in self.task_map:
                task = self.task_map[task_id]
                visualization_data.append({
                    'task_id': task_id,
                    'task_name': task.get('nom', task.get('name', '')),
                    'duration': task.get('duree_estimee', 0),
                    'slack': slack_times.get(task_id, 0),
                    'is_critical': True
                })
        
        # Add near-critical path tasks
        for task_id, slack in slack_times.items():
            if task_id not in path_ids and slack <= 2 and task_id in self.task_map:
                task = self.task_map[task_id]
                visualization_data.append({
                    'task_id': task_id,
                    'task_name': task.get('nom', task.get('name', '')),
                    'duration': task.get('duree_estimee', 0),
                    'slack': slack,
                    'is_critical': False
                })
        
        return visualization_data
        
    def generate_network_diagram(self):
        """Generate a network diagram visualization of the project"""
        G = self._build_graph()
        path_ids = set(self.get_critical_path())
        
        # Create node colors - red for critical path, blue for others
        colors = []
        labels = {}
        
        for node in G.nodes():
            if node in self.task_map:
                task = self.task_map[node]
                labels[node] = f"{task.get('nom', task.get('name', ''))}\n{task.get('duree_estimee', 0)} days"
                if node in path_ids:
                    colors.append('red')
                else:
                    colors.append('skyblue')
            else:
                labels[node] = str(node)
                colors.append('skyblue')
        
        # Create a BytesIO object to save the figure
        buffer = BytesIO()
        
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)  # positions for all nodes
        
        # Draw the graph with specified node colors
        nx.draw(G, pos, node_color=colors, with_labels=False, node_size=500, arrows=True)
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=10)
        
        plt.title('Project Network Diagram')
        plt.savefig(buffer, format='png')
        plt.close()
        
        # Encode the image to base64 string
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode('utf-8')
        
        return {
            'network_diagram': f'data:image/png;base64,{img_str}',
            'critical_path_nodes': list(path_ids)
        }
        
    def get_advanced_analysis(self):
        """Get advanced analysis of the project schedule"""
        # Calculate slack times
        slack_times = self._calculate_slack_times()
        
        # Identify critical path
        path_ids = self.get_critical_path()
        
        # Calculate earliest and latest start/finish times for all tasks
        earliest_start = self._calculate_earliest_start_times()
        latest_start = self._calculate_latest_start_times()
        
        # Prepare detailed task schedule information
        task_schedule = []
        for task_id, task in self.task_map.items():
            es = earliest_start.get(task_id, 0)
            ls = latest_start.get(task_id, 0)
            duration = task.get('duree_estimee', 0)
            
            task_schedule.append({
                'task_id': task_id,
                'task_name': task.get('nom', task.get('name', '')),
                'duration': duration,
                'earliest_start': es,
                'earliest_finish': es + duration,
                'latest_start': ls,
                'latest_finish': ls + duration,
                'slack': slack_times.get(task_id, 0),
                'is_critical': task_id in path_ids
            })
            
        # Calculate project statistics
        total_tasks = len(self.task_map)
        critical_task_count = len(path_ids)
        critical_ratio = critical_task_count / total_tasks if total_tasks > 0 else 0
        
        return {
            'task_schedule': task_schedule,
            'project_stats': {
                'total_tasks': total_tasks,
                'critical_tasks': critical_task_count,
                'critical_ratio': critical_ratio,
                'avg_slack': sum(slack_times.values()) / len(slack_times) if slack_times else 0
            }
        }
