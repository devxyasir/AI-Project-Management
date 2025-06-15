import React, { useState, useEffect } from 'react';
import { Container, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import apiService from '../services/apiService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const GanttChart = ({ projectData, summary }) => {
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [chartData, setChartData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateGanttChart = () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const tasks = summary?.tasks || projectData?.taches || [];
      
      if (tasks.length === 0) {
        setError("No tasks available to generate Gantt chart");
        setIsLoading(false);
        return;
      }
      
      // Generate Gantt data directly on the frontend
      const ganttData = generateGanttData(tasks, startDate);
      prepareChartData(ganttData);
    } catch (err) {
      setError("An error occurred while generating the Gantt chart");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Generate Gantt chart data from tasks
  const generateGanttData = (tasks, startDateStr) => {
    // Sort tasks by dependencies to determine start dates
    const taskMap = {};
    const startDate = new Date(startDateStr);
    
    // First pass: Create task map
    tasks.forEach(task => {
      taskMap[task.id] = {
        ...task,
        earliestStart: 0,
        startDay: null,
        endDay: null,
        dependencies: task.predecesseurs || []
      };
    });
    
    // Second pass: Calculate start and end days
    const processedTasks = [];
    let taskQueue = tasks.filter(task => !task.predecesseurs || task.predecesseurs.length === 0);
    
    // Process tasks with no dependencies first
    while (taskQueue.length > 0) {
      const currentBatch = [...taskQueue];
      taskQueue = [];
      
      currentBatch.forEach(task => {
        const taskId = task.id;
        const currentTask = taskMap[taskId];
        
        // If task has predecessors, find the latest end date
        let earliestStart = 0;
        if (currentTask.dependencies.length > 0) {
          earliestStart = Math.max(...currentTask.dependencies.map(depId => {
            const depTask = taskMap[depId];
            return depTask && depTask.endDay ? depTask.endDay : 0;
          }));
        }
        
        // Set task start and end dates
        currentTask.startDay = earliestStart;
        currentTask.endDay = earliestStart + (currentTask.duree_estimee || 1);
        
        // Add to processed tasks
        processedTasks.push({
          id: currentTask.id,
          name: currentTask.nom || `Task ${currentTask.id}`,
          start_day: currentTask.startDay,
          duration: currentTask.duree_estimee || 1,
          status: currentTask.statut || 'non_commencee',
          dependencies: currentTask.dependencies
        });
        
        // Queue tasks that depend on this task
        tasks.forEach(t => {
          if (t.predecesseurs && t.predecesseurs.includes(taskId) && 
              !processedTasks.find(pt => pt.id === t.id) && 
              !taskQueue.find(qt => qt.id === t.id)) {
            taskQueue.push(t);
          }
        });
      });
    }
    
    // Add any remaining tasks that weren't processed (in case of circular dependencies)
    tasks.forEach(task => {
      if (!processedTasks.find(t => t.id === task.id)) {
        processedTasks.push({
          id: task.id,
          name: task.nom || `Task ${task.id}`,
          start_day: 0,
          duration: task.duree_estimee || 1,
          status: task.statut || 'non_commencee',
          dependencies: task.predecesseurs || []
        });
      }
    });
    
    // Sort tasks by ID for consistency
    processedTasks.sort((a, b) => a.id - b.id);
    
    return {
      start_date: startDateStr,
      tasks: processedTasks
    };
  };

  const prepareChartData = (ganttData) => {
    // Convert backend Gantt data to Chart.js format
    const labels = ganttData.tasks.map(task => task.name);
    
    const datasets = [{
      label: 'Task Duration',
      data: ganttData.tasks.map(task => ({
        x: task.start_day,
        y: labels.indexOf(task.name),
        width: task.duration
      })),
      backgroundColor: ganttData.tasks.map(task => {
        switch (task.status) {
          case 'terminee': return '#28a745';  // Green for completed
          case 'en_cours': return '#007bff';  // Blue for in progress
          case 'en_retard': return '#dc3545';  // Red for delayed
          default: return '#6c757d';  // Gray for not started
        }
      }),
      barPercentage: 0.5,
      categoryPercentage: 0.8,
    }];
    
    setChartData({
      labels,
      datasets
    });
  };

  // Generate chart when component mounts
  useEffect(() => {
    if (projectData && summary) {
      generateGanttChart();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const options = {
    indexAxis: 'y',
    elements: {
      bar: {
        borderWidth: 1,
      },
    },
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Project Gantt Chart',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const task = context.raw;
            return `Duration: ${task.width} days (Days ${task.x} to ${task.x + task.width})`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Days'
        }
      }
    }
  };

  return (
    <Container fluid>
      <h1 className="mb-4">Gantt Chart</h1>
      
      <Card className="mb-4">
        <Card.Body>
          <Form.Group className="mb-3">
            <Form.Label>Project Start Date</Form.Label>
            <Form.Control
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </Form.Group>
          
          <Button 
            variant="primary" 
            onClick={generateGanttChart}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Spinner
                  as="span"
                  animation="border"
                  size="sm"
                  role="status"
                  aria-hidden="true"
                  className="me-2"
                />
                Generating...
              </>
            ) : "Generate Gantt Chart"}
          </Button>
        </Card.Body>
      </Card>
      
      {error && (
        <Alert variant="danger">{error}</Alert>
      )}
      
      {chartData && (
        <Card>
          <Card.Body>
            <div style={{ height: '600px' }}>
              <Bar data={chartData} options={options} />
            </div>
          </Card.Body>
        </Card>
      )}
    </Container>
  );
};

export default GanttChart;
