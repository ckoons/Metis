"""
MCP tool definitions for Metis task management.

This module defines FastMCP tools that provide programmatic access
to Metis task management functionality.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio

from tekton.mcp.fastmcp import mcp_tool
from metis.core.task_manager import TaskManager
from metis.models.task import Task
from metis.models.dependency import Dependency, DependencyType
from metis.models.enums import TaskStatus, Priority
from metis.models.subtask import Subtask
from metis.models.complexity import ComplexityScore
from metis.models.requirement import RequirementRef


class MetisTaskManager:
    """MCP-enabled task manager for Metis operations."""
    
    def __init__(self, task_manager: Optional[TaskManager] = None):
        """Initialize with optional task manager instance."""
        self.task_manager = task_manager or TaskManager()


# ============================================================================
# Task Management Tools (Core CRUD Operations)
# ============================================================================

@mcp_tool(
    name="create_task",
    description="Create a new task in Metis",
    capability="task_management"
)
async def create_task(
    title: str,
    description: str,
    priority: str = "medium",
    status: str = "pending",
    assignee: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None,
    details: Optional[str] = None,
    test_strategy: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new task in the Metis system.
    
    Args:
        title: Title of the task
        description: Detailed description of the task
        priority: Task priority (low, medium, high, urgent)
        status: Task status (pending, in_progress, completed, cancelled)
        assignee: Person assigned to the task
        due_date: Due date in ISO format (YYYY-MM-DD)
        tags: List of tags for categorization
        details: Implementation details
        test_strategy: Testing approach for the task
        
    Returns:
        Dictionary containing the created task information
    """
    # Parse due date if provided
    parsed_due_date = None
    if due_date:
        parsed_due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
    
    # Create task data
    task_data = {
        "title": title,
        "description": description,
        "priority": priority,
        "status": status,
        "assignee": assignee,
        "due_date": parsed_due_date,
        "tags": tags or [],
        "details": details,
        "test_strategy": test_strategy
    }
    
    task = Task(**task_data)
    
    # Use global task manager instance
    from metis.api.routes import task_manager
    created_task = await task_manager.create_task(task)
    
    return {
        "success": True,
        "task": created_task.dict(),
        "message": f"Task '{title}' created successfully"
    }


@mcp_tool(
    name="get_task",
    description="Retrieve details of a specific task",
    capability="task_management"
)
async def get_task(task_id: str) -> Dict[str, Any]:
    """
    Get details of a specific task by ID.
    
    Args:
        task_id: Unique identifier of the task
        
    Returns:
        Dictionary containing task details
    """
    from metis.api.routes import task_manager
    
    task = await task_manager.get_task(task_id)
    if not task:
        return {
            "success": False,
            "message": f"Task with ID '{task_id}' not found"
        }
    
    return {
        "success": True,
        "task": task.dict(),
        "message": "Task retrieved successfully"
    }


@mcp_tool(
    name="update_task",
    description="Update an existing task",
    capability="task_management"
)
async def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None,
    details: Optional[str] = None,
    test_strategy: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing task with new information.
    
    Args:
        task_id: Unique identifier of the task to update
        title: New title for the task
        description: New description for the task
        priority: New priority (low, medium, high, urgent)
        status: New status (pending, in_progress, completed, cancelled)
        assignee: New assignee for the task
        due_date: New due date in ISO format
        tags: New list of tags
        details: New implementation details
        test_strategy: New testing approach
        
    Returns:
        Dictionary containing the updated task information
    """
    from metis.api.routes import task_manager
    
    # Get existing task
    existing_task = await task_manager.get_task(task_id)
    if not existing_task:
        return {
            "success": False,
            "message": f"Task with ID '{task_id}' not found"
        }
    
    # Build update data
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if priority is not None:
        update_data["priority"] = priority
    if status is not None:
        update_data["status"] = status
    if assignee is not None:
        update_data["assignee"] = assignee
    if due_date is not None:
        update_data["due_date"] = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
    if tags is not None:
        update_data["tags"] = tags
    if details is not None:
        update_data["details"] = details
    if test_strategy is not None:
        update_data["test_strategy"] = test_strategy
    
    updated_task = await task_manager.update_task(task_id, update_data)
    
    return {
        "success": True,
        "task": updated_task.dict(),
        "message": f"Task '{task_id}' updated successfully"
    }


@mcp_tool(
    name="delete_task",
    description="Delete a task from the system",
    capability="task_management"
)
async def delete_task(task_id: str) -> Dict[str, Any]:
    """
    Delete a task from the Metis system.
    
    Args:
        task_id: Unique identifier of the task to delete
        
    Returns:
        Dictionary confirming the deletion
    """
    from metis.api.routes import task_manager
    
    success = await task_manager.delete_task(task_id)
    if not success:
        return {
            "success": False,
            "message": f"Task with ID '{task_id}' not found"
        }
    
    return {
        "success": True,
        "message": f"Task '{task_id}' deleted successfully"
    }


@mcp_tool(
    name="list_tasks",
    description="Retrieve a list of tasks with optional filtering",
    capability="task_management"
)
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieve a list of tasks with optional filtering.
    
    Args:
        status: Filter by task status
        priority: Filter by task priority
        assignee: Filter by assignee
        tags: Filter by tags (tasks must have all specified tags)
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        
    Returns:
        Dictionary containing list of tasks and metadata
    """
    from metis.api.routes import task_manager
    
    # Build filter criteria
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if assignee:
        filters["assignee"] = assignee
    if tags:
        filters["tags"] = tags
    
    tasks = await task_manager.list_tasks(
        filters=filters,
        limit=limit,
        offset=offset
    )
    
    return {
        "success": True,
        "tasks": [task.dict() for task in tasks],
        "count": len(tasks),
        "filters_applied": filters,
        "pagination": {
            "limit": limit,
            "offset": offset
        },
        "message": f"Retrieved {len(tasks)} tasks"
    }


# ============================================================================
# Dependency Management Tools
# ============================================================================

@mcp_tool(
    name="create_dependency",
    description="Create a dependency between two tasks",
    capability="dependency_management"
)
async def create_dependency(
    source_task_id: str,
    target_task_id: str,
    dependency_type: str = "depends_on",
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a dependency relationship between two tasks.
    
    Args:
        source_task_id: ID of the source task
        target_task_id: ID of the target task
        dependency_type: Type of dependency (depends_on, blocks, related_to)
        description: Optional description of the dependency
        
    Returns:
        Dictionary containing the created dependency information
    """
    from metis.api.routes import task_manager
    
    dependency_data = {
        "source_task_id": source_task_id,
        "target_task_id": target_task_id,
        "dependency_type": dependency_type,
        "description": description
    }
    
    dependency = Dependency(**dependency_data)
    created_dependency = await task_manager.create_dependency(dependency)
    
    return {
        "success": True,
        "dependency": created_dependency.dict(),
        "message": f"Dependency created between tasks {source_task_id} and {target_task_id}"
    }


@mcp_tool(
    name="get_task_dependencies",
    description="Get all dependencies for a specific task",
    capability="dependency_management"
)
async def get_task_dependencies(task_id: str) -> Dict[str, Any]:
    """
    Get all dependencies for a specific task.
    
    Args:
        task_id: ID of the task to get dependencies for
        
    Returns:
        Dictionary containing task dependencies
    """
    from metis.api.routes import task_manager
    
    dependencies = await task_manager.get_task_dependencies(task_id)
    
    return {
        "success": True,
        "task_id": task_id,
        "dependencies": [dep.dict() for dep in dependencies],
        "count": len(dependencies),
        "message": f"Retrieved {len(dependencies)} dependencies for task {task_id}"
    }


@mcp_tool(
    name="remove_dependency",
    description="Remove a dependency between tasks",
    capability="dependency_management"
)
async def remove_dependency(dependency_id: str) -> Dict[str, Any]:
    """
    Remove a specific dependency.
    
    Args:
        dependency_id: ID of the dependency to remove
        
    Returns:
        Dictionary confirming the removal
    """
    from metis.api.routes import task_manager
    
    success = await task_manager.delete_dependency(dependency_id)
    if not success:
        return {
            "success": False,
            "message": f"Dependency with ID '{dependency_id}' not found"
        }
    
    return {
        "success": True,
        "message": f"Dependency '{dependency_id}' removed successfully"
    }


# ============================================================================
# Task Analytics Tools
# ============================================================================

@mcp_tool(
    name="analyze_task_complexity",
    description="Analyze and score task complexity",
    capability="task_analytics"
)
async def analyze_task_complexity(
    task_id: str,
    factors: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Analyze and score the complexity of a task.
    
    Args:
        task_id: ID of the task to analyze
        factors: Optional complexity factors and scores
        
    Returns:
        Dictionary containing complexity analysis
    """
    from metis.api.routes import task_manager
    
    task = await task_manager.get_task(task_id)
    if not task:
        return {
            "success": False,
            "message": f"Task with ID '{task_id}' not found"
        }
    
    # Use provided factors or default complexity analysis
    if factors:
        complexity = ComplexityScore(
            technical_difficulty=factors.get("technical_difficulty", 5),
            scope=factors.get("scope", 5),
            uncertainty=factors.get("uncertainty", 5),
            dependencies_count=len(task.dependencies),
            overall_score=sum(factors.values()) / len(factors) if factors else 5
        )
    else:
        # Auto-calculate complexity based on task properties
        technical_difficulty = len(task.description) // 50  # Rough estimate based on description length
        scope = len(task.subtasks) + 1  # Base scope plus subtasks
        uncertainty = 5 if not task.details else 3  # Lower uncertainty if details provided
        
        complexity = ComplexityScore(
            technical_difficulty=min(technical_difficulty, 10),
            scope=min(scope, 10),
            uncertainty=uncertainty,
            dependencies_count=len(task.dependencies),
            overall_score=(technical_difficulty + scope + uncertainty) / 3
        )
    
    # Update task with complexity score
    await task_manager.update_task(task_id, {"complexity": complexity})
    
    return {
        "success": True,
        "task_id": task_id,
        "complexity": complexity.dict(),
        "message": f"Complexity analysis completed for task {task_id}"
    }


@mcp_tool(
    name="get_task_statistics",
    description="Get statistics and metrics for all tasks",
    capability="task_analytics"
)
async def get_task_statistics() -> Dict[str, Any]:
    """
    Get comprehensive statistics about all tasks in the system.
    
    Returns:
        Dictionary containing task statistics and metrics
    """
    from metis.api.routes import task_manager
    
    all_tasks = await task_manager.list_tasks()
    
    # Calculate statistics
    total_tasks = len(all_tasks)
    status_counts = {}
    priority_counts = {}
    assignee_counts = {}
    
    for task in all_tasks:
        # Status counts
        status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        # Priority counts
        priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1
        
        # Assignee counts
        if task.assignee:
            assignee_counts[task.assignee] = assignee_counts.get(task.assignee, 0) + 1
    
    # Calculate completion rate
    completed_tasks = status_counts.get(TaskStatus.COMPLETED.value, 0)
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "success": True,
        "statistics": {
            "total_tasks": total_tasks,
            "completion_rate": completion_rate,
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "assignee_breakdown": assignee_counts,
            "unassigned_tasks": total_tasks - sum(assignee_counts.values())
        },
        "message": f"Statistics calculated for {total_tasks} tasks"
    }


# ============================================================================
# Subtask Management Tools
# ============================================================================

@mcp_tool(
    name="add_subtask",
    description="Add a subtask to an existing task",
    capability="task_management"
)
async def add_subtask(
    task_id: str,
    title: str,
    description: str,
    completed: bool = False
) -> Dict[str, Any]:
    """
    Add a subtask to an existing task.
    
    Args:
        task_id: ID of the parent task
        title: Title of the subtask
        description: Description of the subtask
        completed: Whether the subtask is completed
        
    Returns:
        Dictionary containing the updated task with new subtask
    """
    from metis.api.routes import task_manager
    
    subtask = Subtask(
        title=title,
        description=description,
        completed=completed
    )
    
    updated_task = await task_manager.add_subtask(task_id, subtask)
    if not updated_task:
        return {
            "success": False,
            "message": f"Task with ID '{task_id}' not found"
        }
    
    return {
        "success": True,
        "task": updated_task.dict(),
        "message": f"Subtask '{title}' added to task {task_id}"
    }


@mcp_tool(
    name="update_subtask",
    description="Update a subtask within a task",
    capability="task_management"
)
async def update_subtask(
    task_id: str,
    subtask_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Update a subtask within a task.
    
    Args:
        task_id: ID of the parent task
        subtask_id: ID of the subtask to update
        title: New title for the subtask
        description: New description for the subtask
        completed: New completion status
        
    Returns:
        Dictionary containing the updated task
    """
    from metis.api.routes import task_manager
    
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if completed is not None:
        update_data["completed"] = completed
    
    updated_task = await task_manager.update_subtask(task_id, subtask_id, update_data)
    if not updated_task:
        return {
            "success": False,
            "message": f"Task or subtask not found"
        }
    
    return {
        "success": True,
        "task": updated_task.dict(),
        "message": f"Subtask {subtask_id} updated in task {task_id}"
    }


# ============================================================================
# Telos Integration Tools
# ============================================================================

@mcp_tool(
    name="import_requirement_as_task",
    description="Import a requirement from Telos as a new task",
    capability="telos_integration"
)
async def import_requirement_as_task(
    requirement_id: str,
    priority: str = "medium",
    assignee: Optional[str] = None
) -> Dict[str, Any]:
    """
    Import a requirement from Telos as a new task.
    
    Args:
        requirement_id: ID of the requirement in Telos
        priority: Priority for the new task
        assignee: Optional assignee for the task
        
    Returns:
        Dictionary containing the created task
    """
    from metis.api.routes import task_manager
    
    try:
        # Import requirement from Telos
        imported_task = await task_manager.import_requirement_as_task(
            requirement_id, 
            priority=priority,
            assignee=assignee
        )
        
        return {
            "success": True,
            "task": imported_task.dict(),
            "requirement_id": requirement_id,
            "message": f"Requirement {requirement_id} imported as task {imported_task.id}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to import requirement {requirement_id}: {str(e)}"
        }


@mcp_tool(
    name="link_task_to_requirement",
    description="Link an existing task to a Telos requirement",
    capability="telos_integration"
)
async def link_task_to_requirement(
    task_id: str,
    requirement_id: str,
    relationship_type: str = "implements"
) -> Dict[str, Any]:
    """
    Link an existing task to a Telos requirement.
    
    Args:
        task_id: ID of the task to link
        requirement_id: ID of the requirement in Telos
        relationship_type: Type of relationship (implements, tests, documents)
        
    Returns:
        Dictionary containing the updated task
    """
    from metis.api.routes import task_manager
    
    requirement_ref = RequirementRef(
        requirement_id=requirement_id,
        relationship_type=relationship_type
    )
    
    updated_task = await task_manager.add_requirement_reference(task_id, requirement_ref)
    if not updated_task:
        return {
            "success": False,
            "message": f"Task with ID '{task_id}' not found"
        }
    
    return {
        "success": True,
        "task": updated_task.dict(),
        "message": f"Task {task_id} linked to requirement {requirement_id}"
    }


# Export all tools for registration
task_management_tools = [
    create_task,
    get_task,
    update_task,
    delete_task,
    list_tasks,
    add_subtask,
    update_subtask
]

dependency_management_tools = [
    create_dependency,
    get_task_dependencies,
    remove_dependency
]

analytics_tools = [
    analyze_task_complexity,
    get_task_statistics
]

telos_integration_tools = [
    import_requirement_as_task,
    link_task_to_requirement
]