"""Workflow engine - step-based orchestration with dependency ordering."""

import hashlib
from typing import Dict, List, Optional

from backend.runtime.context import RuntimeExecutionContext
from backend.workflow.models import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionState,
    WorkflowStepResult,
)


class WorkflowEngine:
    """Orchestrates workflow execution with dependency-based step ordering.

    Executes steps sequentially respecting depends_on ordering.
    Tracks execution state transitions deterministically.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize workflow engine with execution context.

        Args:
            context: Runtime execution context for deterministic timestamps.
        """
        self._context = context
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}

    def create_workflow(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        """Store a workflow definition.

        Args:
            definition: The workflow definition to store.

        Returns:
            The stored workflow definition.
        """
        if not definition.created_timestamp:
            definition.created_timestamp = self._context.now_iso()
        self._workflows[definition.id] = definition
        return definition

    def execute_workflow(self, workflow_id: str) -> WorkflowExecution:
        """Execute a workflow by walking steps in dependency order.

        Args:
            workflow_id: The ID of the workflow to execute.

        Returns:
            The workflow execution record.

        Raises:
            ValueError: If the workflow does not exist.
        """
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        start_timestamp = self._context.now_iso()
        execution_id = hashlib.sha256(
            f"{workflow_id}{start_timestamp}".encode("utf-8")
        ).hexdigest()[:16]

        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            state=WorkflowExecutionState.RUNNING,
            start_timestamp=start_timestamp,
        )
        self._executions[execution_id] = execution

        ordered_steps = self._resolve_execution_order(workflow)

        for step in ordered_steps:
            execution.current_step_id = step.id
            start_time = self._context.now()

            try:
                duration_ms = (self._context.now() - start_time) * 1000
                step_result = WorkflowStepResult(
                    step_id=step.id,
                    status="success",
                    outputs={},
                    duration_ms=duration_ms,
                )
                execution.steps_completed.append(step_result)
            except Exception as e:
                duration_ms = (self._context.now() - start_time) * 1000
                step_result = WorkflowStepResult(
                    step_id=step.id,
                    status="failed",
                    duration_ms=duration_ms,
                    error=str(e),
                )
                execution.steps_completed.append(step_result)
                execution.state = WorkflowExecutionState.FAILED
                execution.end_timestamp = self._context.now_iso()
                execution.current_step_id = None
                return execution

        execution.state = WorkflowExecutionState.COMPLETED
        execution.end_timestamp = self._context.now_iso()
        execution.current_step_id = None
        return execution

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID.

        Args:
            workflow_id: The workflow ID to look up.

        Returns:
            The workflow definition if found, None otherwise.
        """
        return self._workflows.get(workflow_id)

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID.

        Args:
            execution_id: The execution ID to look up.

        Returns:
            The workflow execution if found, None otherwise.
        """
        return self._executions.get(execution_id)

    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all workflow definitions.

        Returns:
            List of all workflow definitions.
        """
        return list(self._workflows.values())

    def list_executions(self) -> List[WorkflowExecution]:
        """List all workflow executions.

        Returns:
            List of all workflow executions.
        """
        return list(self._executions.values())

    def _resolve_execution_order(self, workflow: WorkflowDefinition) -> list:
        """Resolve step execution order based on dependencies.

        Uses topological sort to order steps respecting depends_on.
        Detects cyclic dependencies and raises ValueError.

        Args:
            workflow: The workflow definition to resolve.

        Returns:
            Steps ordered for execution.

        Raises:
            ValueError: If a cyclic dependency is detected.
        """
        steps_by_id = {step.id: step for step in workflow.steps}
        visited = set()
        processing = set()
        order = []

        def visit(step_id: str) -> None:
            if step_id in visited:
                return
            if step_id in processing:
                raise ValueError(f"Cyclic dependency detected at step: {step_id}")
            processing.add(step_id)
            step = steps_by_id[step_id]
            for dep_id in step.depends_on:
                if dep_id in steps_by_id:
                    visit(dep_id)
            processing.discard(step_id)
            visited.add(step_id)
            order.append(step)

        for step in workflow.steps:
            visit(step.id)

        return order
