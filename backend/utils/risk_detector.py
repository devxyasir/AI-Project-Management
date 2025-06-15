"""
Risk Detection Module
Analyzes project data to identify potential risks and issues
"""
from collections import defaultdict


class RiskDetector:
    """
    Detects potential risks and issues in project data
    Analyzes task dependencies, resources, and durations
    """
    
    def __init__(self, tasks=None, critical_path=None):
        """
        Initialize risk detector with tasks and optional critical path
        
        Args:
            tasks (list): List of task objects
            critical_path (list): Critical path task IDs
        """
        self.tasks = tasks or []
        self.critical_path = critical_path or []
        self.critical_path_ids = set(self.critical_path)
    
    def detect_risks(self):
        """
        Detect all risks in project
        
        Returns:
            dict: Risk analysis results
        """
        # Collect all risk types
        no_resources = self._tasks_without_resources()
        no_dependencies = self._tasks_without_dependencies()
        bottlenecks = self._detect_bottlenecks()
        overloaded_resources = self._detect_overloaded_resources()
        timeline_risks = self._detect_timeline_risks()
        dependency_conflicts = self._detect_dependency_conflicts()
        resource_conflicts = self._detect_resource_allocation_conflicts()
        
        # Calculate risk scores by category
        risk_scores = {
            "resource_risks": len(no_resources) * 10 + len(overloaded_resources) * 15,
            "dependency_risks": len(no_dependencies) * 5 + len(dependency_conflicts) * 20,
            "timeline_risks": len(bottlenecks) * 15 + len(timeline_risks) * 10,
            "resource_conflicts": len(resource_conflicts) * 20
        }
        
        # Calculate overall risk level
        total_risks = (len(no_resources) + len(no_dependencies) + 
                      len(bottlenecks) + len(overloaded_resources) +
                      len(timeline_risks) + len(dependency_conflicts) +
                      len(resource_conflicts))
        
        risk_level = self._calculate_risk_level(total_risks)
        
        # Calculate detailed risk metrics
        risk_metrics = self._calculate_risk_metrics(
            no_resources, no_dependencies, bottlenecks, 
            overloaded_resources, timeline_risks,
            dependency_conflicts, resource_conflicts
        )
        
        # Generate recommendations based on detected risks
        recommendations = self._generate_recommendations(
            no_resources, no_dependencies, bottlenecks, 
            overloaded_resources, timeline_risks,
            dependency_conflicts, resource_conflicts
        )
        
        # Generate data for visualizations
        chart_data = self._generate_risk_chart_data(risk_scores)
        risk_distribution = self._generate_risk_distribution()
        critical_vs_noncritical_risks = self._analyze_critical_path_risks()
        
        return {
            "total_risks": total_risks,
            "risk_level": risk_level,
            "risk_scores": risk_scores,
            "risk_metrics": risk_metrics,
            "risks": {
                "no_resources": no_resources,
                "no_dependencies": no_dependencies,
                "bottlenecks": bottlenecks,
                "overloaded_resources": overloaded_resources,
                "timeline_risks": timeline_risks,
                "dependency_conflicts": dependency_conflicts,
                "resource_conflicts": resource_conflicts
            },
            "recommendations": recommendations,
            "chart_data": chart_data,
            "risk_distribution": risk_distribution,
            "critical_path_analysis": critical_vs_noncritical_risks
        }
    
    def _tasks_without_resources(self):
        """
        Find tasks with no assigned resources
        
        Returns:
            list: Tasks without resources
        """
        result = []
        
        for task in self.tasks:
            resources = task.get('ressources_requises', [])
            
            # Check if resources is empty or contains only empty strings
            if not resources or all(not r for r in resources):
                # Determine risk level - higher for critical path tasks
                risk_level = "Élevé" if task.get('id') in self.critical_path_ids else "Moyen"
                
                # Add task to result with risk level
                task_copy = task.copy()
                task_copy['risk_level'] = risk_level
                result.append(task_copy)
        
        return result
    
    def _tasks_without_dependencies(self):
        """
        Find tasks with no dependencies (except for initial tasks)
        
        Returns:
            list: Tasks without dependencies that aren't initial tasks
        """
        result = []
        
        # Skip the first task(s) as they naturally have no predecessors
        initial_task_ids = set()
        for task in self.tasks:
            has_predecessors = bool(task.get('predecesseurs', []))
            if not has_predecessors:
                initial_task_ids.add(task.get('id'))
        
        # Find all task IDs for reference
        all_task_ids = {task.get('id') for task in self.tasks}
        
        # Track tasks that are referenced as dependencies
        referenced_as_dependency = set()
        for task in self.tasks:
            for dep in task.get('predecesseurs', []):
                if dep in all_task_ids:
                    referenced_as_dependency.add(dep)
        
        # Find tasks that are neither initial nor referenced as dependencies
        for task in self.tasks:
            task_id = task.get('id')
            if task_id not in initial_task_ids and task_id not in referenced_as_dependency:
                # Tasks not referenced as dependencies might be forgotten or isolated
                risk_level = "Faible"  # Generally lower risk, but worth checking
                
                task_copy = task.copy()
                task_copy['risk_level'] = risk_level
                result.append(task_copy)
        
        return result
    
    def _detect_bottlenecks(self):
        """
        Detect potential bottleneck tasks (long duration on critical path)
        
        Returns:
            list: Potential bottleneck tasks
        """
        result = []
        
        # Calculate average task duration
        if not self.tasks:
            return result
            
        total_duration = sum(task.get('duree_estimee', 0) for task in self.tasks)
        avg_duration = total_duration / len(self.tasks)
        
        # Bottleneck threshold (tasks taking significantly longer than average)
        threshold = avg_duration * 1.5
        
        for task in self.tasks:
            duration = task.get('duree_estimee', 0)
            task_id = task.get('id')
            
            # Task is a bottleneck if it's significantly longer than average
            # and especially if it's on the critical path
            if duration > threshold:
                risk_level = "Élevé" if task_id in self.critical_path_ids else "Moyen"
                
                task_copy = task.copy()
                task_copy['risk_level'] = risk_level
                task_copy['average_duration'] = avg_duration
                task_copy['duration_ratio'] = duration / avg_duration
                result.append(task_copy)
        
        return result
    
    def _detect_overloaded_resources(self):
        """
        Detect overloaded resources (assigned to too many tasks)
        
        Returns:
            list: Overloaded resources with their tasks
        """
        result = []
        
        # Resource to tasks mapping
        resource_tasks = defaultdict(list)
        
        for task in self.tasks:
            resources = task.get('ressources_requises', [])
            
            for resource in resources:
                if resource:  # Skip empty resource strings
                    resource_tasks[resource].append(task)
        
        # Consider resources with more than 3 tasks as potentially overloaded
        threshold = 3
        
        for resource, tasks in resource_tasks.items():
            if len(tasks) > threshold:
                # Higher risk for resources on critical path tasks
                critical_tasks = [task for task in tasks 
                                if task.get('id') in self.critical_path_ids]
                
                risk_level = "Élevé" if critical_tasks else "Moyen"
                
                result.append({
                    "resource": resource,
                    "task_count": len(tasks),
                    "tasks": tasks,
                    "critical_tasks": len(critical_tasks),
                    "risk_level": risk_level
                })
        
        return result
    
    def _calculate_risk_level(self, total_risks):
        """
        Calculate overall project risk level based on number of risks
        
        Args:
            total_risks (int): Total number of detected risks
            
        Returns:
            str: Overall risk level
        """
        if total_risks == 0:
            return "Très faible"
        elif total_risks <= 2:
            return "Faible"
        elif total_risks <= 5:
            return "Moyen"
        else:
            return "Élevé"
    
    def _detect_timeline_risks(self):
        """
        Detect risks related to timeline issues like unrealistic deadlines
        or scheduling conflicts
        
        Returns:
            list: Timeline-related risks
        """
        timeline_risks = []
        
        # Look for tasks with very short durations that might be unrealistic
        for task in self.tasks:
            # Skip tasks with zero or no duration
            if not task.get('duree_estimee'):
                continue
                
            task_id = task.get('id')
            duration = task.get('duree_estimee', 0)
            num_predecessors = len(task.get('predecesseurs', []))
            num_resources = len(task.get('ressources_requises', []))
            
            # Complex tasks (many dependencies or resources) with short durations
            if (num_predecessors > 2 or num_resources > 2) and duration < 3:
                risk_level = "Élevé" if task_id in self.critical_path_ids else "Moyen"
                task_copy = task.copy()
                task_copy['risk_level'] = risk_level
                task_copy['risk_reason'] = "Durée potentiellement sous-estimée pour une tâche complexe"
                timeline_risks.append(task_copy)
        
        return timeline_risks
    
    def _detect_dependency_conflicts(self):
        """
        Detect potential conflicts or issues in task dependencies
        
        Returns:
            list: Dependency conflicts
        """
        conflicts = []
        
        # Build a dependency map
        dependency_map = {}
        for task in self.tasks:
            task_id = task.get('id')
            predecessors = task.get('predecesseurs', [])
            dependency_map[task_id] = predecessors
        
        # Check for circular dependencies and long dependency chains
        for task in self.tasks:
            task_id = task.get('id')
            
            # Check for long dependency chains (5+ dependencies)
            chain = self._get_dependency_chain(task_id, dependency_map)
            if len(chain) > 5:
                risk_level = "Élevé" if task_id in self.critical_path_ids else "Moyen"
                conflicts.append({
                    'task_id': task_id,
                    'task_name': task.get('nom', ''),
                    'risk_level': risk_level,
                    'dependency_chain': chain,
                    'risk_type': 'long_dependency_chain'
                })
                
        return conflicts
    
    def _get_dependency_chain(self, task_id, dependency_map, visited=None):
        """
        Get the full dependency chain for a task
        
        Args:
            task_id: The ID of the task to check
            dependency_map: Map of task IDs to their predecessors
            visited: Set of already visited task IDs (for cycle detection)
            
        Returns:
            list: Chain of dependencies
        """
        if visited is None:
            visited = set()
            
        if task_id in visited:
            # Circular dependency detected
            return [task_id]
            
        visited.add(task_id)
        chain = [task_id]
        
        # Get predecessors
        predecessors = dependency_map.get(task_id, [])
        for pred in predecessors:
            if pred in dependency_map:
                pred_chain = self._get_dependency_chain(pred, dependency_map, visited.copy())
                chain = pred_chain + chain
                
        return chain
    
    def _detect_resource_allocation_conflicts(self):
        """
        Detect potential resource allocation conflicts
        
        Returns:
            list: Resource allocation conflicts
        """
        conflicts = []
        
        # Group tasks by resource
        resource_tasks = defaultdict(list)
        for task in self.tasks:
            resources = task.get('ressources_requises', [])
            for resource in resources:
                if resource:  # Skip empty resource names
                    resource_tasks[resource].append(task)
        
        # Check for conflicts (same resource assigned to parallel tasks)
        for resource, tasks in resource_tasks.items():
            if len(tasks) <= 1:
                continue
                
            # Check if any tasks might be scheduled in parallel
            parallel_task_groups = self._find_potential_parallel_tasks(tasks)
            
            for group in parallel_task_groups:
                if len(group) > 1:
                    # We have a potential conflict
                    critical_tasks = [t for t in group if t.get('id') in self.critical_path_ids]
                    risk_level = "Élevé" if critical_tasks else "Moyen"
                    
                    conflicts.append({
                        'resource': resource,
                        'conflicting_tasks': group,
                        'critical_tasks': len(critical_tasks),
                        'risk_level': risk_level
                    })
        
        return conflicts
    
    def _find_potential_parallel_tasks(self, tasks):
        """
        Find groups of tasks that might be scheduled in parallel
        
        Args:
            tasks: List of tasks to check
            
        Returns:
            list: Groups of potentially parallel tasks
        """
        # For now, a simple heuristic - tasks that don't depend on each other
        # might be scheduled in parallel
        parallel_groups = []
        
        # Create a set of all task IDs in the task list
        task_ids = {task.get('id') for task in tasks}
        
        # Group tasks that don't depend on each other
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            group = []
            task = remaining_tasks.pop(0)
            group.append(task)
            
            task_dependencies = set(task.get('predecesseurs', []))
            task_id = task.get('id')
            
            for other_task in remaining_tasks.copy():
                other_id = other_task.get('id')
                other_dependencies = set(other_task.get('predecesseurs', []))
                
                # If neither task depends on the other, they might be parallel
                if task_id not in other_dependencies and other_id not in task_dependencies:
                    group.append(other_task)
                    remaining_tasks.remove(other_task)
                    
            if len(group) > 1:
                parallel_groups.append(group)
                
        return parallel_groups
    
    def _calculate_risk_metrics(self, no_resources, no_dependencies, bottlenecks, 
                             overloaded_resources, timeline_risks,
                             dependency_conflicts, resource_conflicts):
        """
        Calculate detailed risk metrics for the project
        
        Returns:
            dict: Risk metrics
        """
        # Count risks by level
        high_risks = 0
        medium_risks = 0
        low_risks = 0
        
        # Helper function to count risks by level
        def count_risk_levels(risk_list):
            nonlocal high_risks, medium_risks, low_risks
            for risk in risk_list:
                level = risk.get('risk_level', '')
                if level == "Élevé":
                    high_risks += 1
                elif level == "Moyen":
                    medium_risks += 1
                else:
                    low_risks += 1
        
        # Count risks by level for each risk type
        for risk_list in [no_resources, no_dependencies, bottlenecks]:
            count_risk_levels(risk_list)
            
        # Count overloaded resources
        for risk in overloaded_resources:
            level = risk.get('risk_level', '')
            if level == "Élevé":
                high_risks += 1
            elif level == "Moyen":
                medium_risks += 1
            else:
                low_risks += 1
        
        # Count timeline risks
        for risk in timeline_risks:
            level = risk.get('risk_level', '')
            if level == "Élevé":
                high_risks += 1
            elif level == "Moyen":
                medium_risks += 1
            else:
                low_risks += 1
        
        # Count dependency conflicts
        for risk in dependency_conflicts:
            level = risk.get('risk_level', '')
            if level == "Élevé":
                high_risks += 1
            elif level == "Moyen":
                medium_risks += 1
            else:
                low_risks += 1
        
        # Count resource conflicts
        for risk in resource_conflicts:
            level = risk.get('risk_level', '')
            if level == "Élevé":
                high_risks += 1
            elif level == "Moyen":
                medium_risks += 1
            else:
                low_risks += 1
        
        total_critical_path_risks = sum(
            1 for risk in no_resources + bottlenecks if risk.get('id') in self.critical_path_ids
        )
        
        return {
            "risk_levels": {
                "high": high_risks,
                "medium": medium_risks,
                "low": low_risks
            },
            "critical_path_risk_count": total_critical_path_risks,
            "resource_risk_ratio": len(no_resources) / len(self.tasks) if self.tasks else 0,
            "dependency_risk_ratio": len(no_dependencies) / len(self.tasks) if self.tasks else 0,
            "total_risk_score": high_risks * 3 + medium_risks * 2 + low_risks
        }
    
    def _generate_risk_chart_data(self, risk_scores):
        """
        Generate data for risk visualization charts
        
        Args:
            risk_scores: Dictionary of risk scores by category
            
        Returns:
            dict: Chart data for different visualizations
        """
        # Data for radar chart of risk categories
        radar_data = {
            "labels": ["Resource Risks", "Dependency Risks", "Timeline Risks", "Resource Conflicts"],
            "datasets": [{
                "label": "Risk Score",
                "data": [
                    risk_scores.get("resource_risks", 0),
                    risk_scores.get("dependency_risks", 0),
                    risk_scores.get("timeline_risks", 0),
                    risk_scores.get("resource_conflicts", 0)
                ]
            }]
        }
        
        # Data for pie chart of risk distribution
        risk_counts = self._count_risks_by_type()
        pie_data = {
            "labels": list(risk_counts.keys()),
            "datasets": [{
                "label": "Risk Count",
                "data": list(risk_counts.values())
            }]
        }
        
        # Timeline risk projection
        timeline_data = self._generate_timeline_risk_projection()
        
        return {
            "radar": radar_data,
            "pie": pie_data,
            "timeline": timeline_data
        }
    
    def _count_risks_by_type(self):
        """
        Count risks by type
        
        Returns:
            dict: Risk counts by type
        """
        # Count all risks we've identified
        return {
            "Resource Allocation": len(self._tasks_without_resources()),
            "Dependencies": len(self._tasks_without_dependencies()),
            "Bottlenecks": len(self._detect_bottlenecks()),
            "Overallocated Resources": len(self._detect_overloaded_resources()),
            "Timeline Issues": len(self._detect_timeline_risks()),
            "Dependency Conflicts": len(self._detect_dependency_conflicts()),
            "Resource Conflicts": len(self._detect_resource_allocation_conflicts())
        }
    
    def _generate_timeline_risk_projection(self):
        """
        Generate timeline projection of how risks might impact the project over time
        
        Returns:
            dict: Timeline data for visualization
        """
        # This is a simplified model - in a real application, you'd use
        # more complex risk propagation models
        time_points = ["Project Start", "25%", "50%", "75%", "Project End"]
        
        # Calculate risk impact at different project stages
        risk_impact = []
        
        # Total number of risks
        total_risks = len(self._tasks_without_resources()) + \
                     len(self._tasks_without_dependencies()) + \
                     len(self._detect_bottlenecks()) + \
                     len(self._detect_overloaded_resources()) + \
                     len(self._detect_timeline_risks()) + \
                     len(self._detect_dependency_conflicts()) + \
                     len(self._detect_resource_allocation_conflicts())
        
        # Simple model: risks increase until 50% then decrease
        # This would be more sophisticated in a real application
        if total_risks > 0:
            risk_impact = [total_risks * 0.5, total_risks * 0.8, total_risks, total_risks * 0.7, total_risks * 0.3]
        else:
            risk_impact = [0, 0, 0, 0, 0]
            
        return {
            "labels": time_points,
            "datasets": [{
                "label": "Projected Risk Impact",
                "data": risk_impact
            }]
        }
    
    def _generate_risk_distribution(self):
        """
        Generate data showing distribution of risks across the project
        
        Returns:
            dict: Risk distribution data
        """
        # Count risks by task status
        status_risks = defaultdict(int)
        
        for task in self.tasks:
            task_id = task.get('id')
            status = task.get('statut', '')
            
            # Count risks for this task
            risk_count = 0
            
            # Check if task has resource issues
            resources = task.get('ressources_requises', [])
            if not resources or all(not r for r in resources):
                risk_count += 1
            
            # Check if task is a bottleneck
            if task_id in self.critical_path_ids and task.get('duree_estimee', 0) > 10:
                risk_count += 1
                
            if risk_count > 0:
                status_risks[status] += risk_count
        
        return {
            "labels": list(status_risks.keys()),
            "datasets": [{
                "label": "Risks by Task Status",
                "data": list(status_risks.values())
            }]
        }
    
    def _analyze_critical_path_risks(self):
        """
        Analyze risks on critical path vs non-critical path
        
        Returns:
            dict: Critical path risk analysis
        """
        critical_risks = 0
        non_critical_risks = 0
        
        for task in self.tasks:
            task_id = task.get('id')
            is_critical = task_id in self.critical_path_ids
            
            # Count risks for this task
            risk_count = 0
            
            # Check if task has resource issues
            resources = task.get('ressources_requises', [])
            if not resources or all(not r for r in resources):
                risk_count += 1
            
            # Check if task is a bottleneck
            if is_critical and task.get('duree_estimee', 0) > 10:
                risk_count += 1
                
            # Add to appropriate counter
            if is_critical:
                critical_risks += risk_count
            else:
                non_critical_risks += risk_count
        
        return {
            "labels": ["Critical Path Tasks", "Non-Critical Path Tasks"],
            "datasets": [{
                "label": "Risk Count",
                "data": [critical_risks, non_critical_risks]
            }]
        }
            
    def _generate_recommendations(self, no_resources, no_dependencies, 
                                bottlenecks, overloaded_resources,
                                timeline_risks=None, dependency_conflicts=None, 
                                resource_conflicts=None):
        """
        Generate recommendations based on detected risks
        
        Returns:
            list: Recommendations to address risks
        """
        recommendations = []
        
        # Resource recommendations
        if no_resources:
            if len(no_resources) > 1:
                recommendations.append(
                    f"Assign resources to {len(no_resources)} tasks that currently have none, "
                    f"especially to the critical path tasks."
                )
            else:
                task = no_resources[0]
                recommendations.append(
                    f"Assign resources to task '{task.get('nom', task.get('name', ''))}' which currently has none."
                )
        
        # Dependency recommendations
        if no_dependencies:
            recommendations.append(
                f"Review {len(no_dependencies)} tasks that aren't referenced as dependencies "
                f"by any other task. They might be isolated or disconnected from the project flow."
            )
        
        # Bottleneck recommendations
        if bottlenecks:
            critical_bottlenecks = [t for t in bottlenecks if t.get('id') in self.critical_path_ids]
            if critical_bottlenecks:
                recommendations.append(
                    f"Consider breaking down {len(critical_bottlenecks)} long-duration tasks on the "
                    f"critical path into smaller sub-tasks to reduce risk and improve tracking."
                )
            
            if len(bottlenecks) > len(critical_bottlenecks):
                recommendations.append(
                    f"Review {len(bottlenecks) - len(critical_bottlenecks)} non-critical tasks with "
                    f"unusually long durations. They might benefit from additional resources."
                )
        
        # Overloaded resource recommendations
        if overloaded_resources:
            recommendations.append(
                f"Redistribute work from {len(overloaded_resources)} potentially overloaded resources "
                f"to ensure optimal performance and reduce burnout risk."
            )
            
            # Specific recommendations for severely overloaded resources
            severe_overloads = [r for r in overloaded_resources if r.get('task_count', 0) > 5]
            if severe_overloads:
                for resource in severe_overloads:
                    recommendations.append(
                        f"Resource '{resource.get('resource')}' is assigned to {resource.get('task_count')} "
                        f"tasks which is significantly above recommended limits. Consider immediate reallocation."
                    )
        
        # Add general recommendations if we have risks
        if no_resources or no_dependencies or bottlenecks or overloaded_resources:
            recommendations.append(
                "Consider implementing a regular risk review meeting to address these and "
                "other potential issues before they impact the project timeline."
            )
        
        return recommendations
