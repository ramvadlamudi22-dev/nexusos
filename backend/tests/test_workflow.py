"""Tests for workflow engine - definition, execution, and state tracking."""

import pytest

from backend.runtime.context import RuntimeExecutionContext
from backend.workflow.engine import WorkflowEngine
from backend.workflow.models import (
    WorkflowDefinition,
    WorkflowExecutionState,
    WorkflowStep,
    WorkflowStepType,
)


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestWorkflowCreation:
    """Test workflow definition creation and storage."""

    def test_create_workflow(self):
        """Can create and store a workflow definition."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        definition = WorkflowDefinition(
            id="wf-1",
            name="Test Workflow",
            steps=[
                WorkflowStep(
                    id="step-1",
                    name="First Step",
                    step_type=WorkflowStepType.TERMINAL,
                )
            ],
        )

        result = engine.create_workflow(definition)

        assert result.id == "wf-1"
        assert result.name == "Test Workflow"
        assert result.created_timestamp != ""

    def test_get_workflow(self):
        """Can retrieve a stored workflow by ID."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(id="wf-1", name="Test")
        )

        found = engine.get_workflow("wf-1")
        assert found is not None
        assert found.id == "wf-1"

    def test_get_nonexistent_workflow(self):
        """Getting a nonexistent workflow returns None."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        assert engine.get_workflow("nonexistent") is None

    def test_list_workflows(self):
        """Can list all stored workflows."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(WorkflowDefinition(id="wf-1", name="WF1"))
        engine.create_workflow(WorkflowDefinition(id="wf-2", name="WF2"))

        workflows = engine.list_workflows()
        assert len(workflows) == 2


class TestWorkflowExecution:
    """Test workflow execution and state transitions."""

    def test_execute_simple_workflow(self):
        """Can execute a single-step workflow to completion."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-1",
                name="Simple",
                steps=[
                    WorkflowStep(
                        id="step-1",
                        name="Only Step",
                        step_type=WorkflowStepType.TERMINAL,
                    )
                ],
            )
        )

        execution = engine.execute_workflow("wf-1")

        assert execution.state == WorkflowExecutionState.COMPLETED
        assert execution.workflow_id == "wf-1"
        assert len(execution.steps_completed) == 1
        assert execution.steps_completed[0].step_id == "step-1"
        assert execution.steps_completed[0].status == "success"

    def test_execute_multi_step_workflow(self):
        """Can execute a multi-step workflow sequentially."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-multi",
                name="Multi Step",
                steps=[
                    WorkflowStep(
                        id="step-1",
                        name="Step 1",
                        step_type=WorkflowStepType.BROWSER,
                    ),
                    WorkflowStep(
                        id="step-2",
                        name="Step 2",
                        step_type=WorkflowStepType.TERMINAL,
                    ),
                    WorkflowStep(
                        id="step-3",
                        name="Step 3",
                        step_type=WorkflowStepType.SKILL,
                    ),
                ],
            )
        )

        execution = engine.execute_workflow("wf-multi")

        assert execution.state == WorkflowExecutionState.COMPLETED
        assert len(execution.steps_completed) == 3

    def test_execute_workflow_with_dependencies(self):
        """Steps with dependencies execute after their dependencies."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-deps",
                name="Deps Workflow",
                steps=[
                    WorkflowStep(
                        id="step-b",
                        name="Step B",
                        step_type=WorkflowStepType.TERMINAL,
                        depends_on=["step-a"],
                    ),
                    WorkflowStep(
                        id="step-a",
                        name="Step A",
                        step_type=WorkflowStepType.TERMINAL,
                    ),
                ],
            )
        )

        execution = engine.execute_workflow("wf-deps")

        assert execution.state == WorkflowExecutionState.COMPLETED
        step_ids = [s.step_id for s in execution.steps_completed]
        assert step_ids.index("step-a") < step_ids.index("step-b")

    def test_execute_nonexistent_workflow_raises(self):
        """Executing a nonexistent workflow raises ValueError."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        with pytest.raises(ValueError, match="Workflow not found"):
            engine.execute_workflow("nonexistent")

    def test_execution_has_timestamps(self):
        """Executions record start and end timestamps."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-1",
                name="Timestamps",
                steps=[
                    WorkflowStep(
                        id="step-1",
                        name="Step",
                        step_type=WorkflowStepType.CUSTOM,
                    )
                ],
            )
        )

        execution = engine.execute_workflow("wf-1")

        assert execution.start_timestamp != ""
        assert execution.end_timestamp != ""

    def test_get_execution(self):
        """Can retrieve an execution by its ID."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-1",
                name="Test",
                steps=[
                    WorkflowStep(
                        id="s1",
                        name="S1",
                        step_type=WorkflowStepType.TERMINAL,
                    )
                ],
            )
        )

        execution = engine.execute_workflow("wf-1")
        found = engine.get_execution(execution.id)

        assert found is not None
        assert found.id == execution.id

    def test_list_executions(self):
        """Can list all workflow executions."""
        counter = {"t": 1000000.0}

        def advancing_time():
            counter["t"] += 1.0
            return counter["t"]

        ctx = RuntimeExecutionContext(time_source=advancing_time)
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-1",
                name="Test",
                steps=[
                    WorkflowStep(
                        id="s1",
                        name="S1",
                        step_type=WorkflowStepType.TERMINAL,
                    )
                ],
            )
        )

        engine.execute_workflow("wf-1")
        engine.execute_workflow("wf-1")

        executions = engine.list_executions()
        assert len(executions) == 2

    def test_completed_execution_has_no_current_step(self):
        """A completed execution has current_step_id set to None."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-1",
                name="Test",
                steps=[
                    WorkflowStep(
                        id="s1",
                        name="S1",
                        step_type=WorkflowStepType.TERMINAL,
                    )
                ],
            )
        )

        execution = engine.execute_workflow("wf-1")

        assert execution.current_step_id is None

    def test_cyclic_dependency_raises_error(self):
        """A workflow with cyclic dependencies raises ValueError."""
        ctx = make_context()
        engine = WorkflowEngine(ctx)

        engine.create_workflow(
            WorkflowDefinition(
                id="wf-cycle",
                name="Cyclic Workflow",
                steps=[
                    WorkflowStep(
                        id="step-a",
                        name="Step A",
                        step_type=WorkflowStepType.TERMINAL,
                        depends_on=["step-b"],
                    ),
                    WorkflowStep(
                        id="step-b",
                        name="Step B",
                        step_type=WorkflowStepType.TERMINAL,
                        depends_on=["step-a"],
                    ),
                ],
            )
        )

        with pytest.raises(ValueError, match="Cyclic dependency"):
            engine.execute_workflow("wf-cycle")
