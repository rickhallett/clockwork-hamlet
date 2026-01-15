"""Long-term goal planning system for multi-day agent ambitions."""

import random
import time
from typing import Optional

from sqlalchemy.orm import Session

from hamlet.db.models import Agent, Goal, GoalPlan
from hamlet.goals.types import (
    AMBITION_BASE_PRIORITY,
    AMBITION_MILESTONES,
    AMBITION_SUBGOALS,
    TRAIT_AMBITION_MAPPINGS,
    AmbitionType,
    GoalType,
    PlanStatus,
)


class GoalPlanner:
    """Manages long-term goal plans for agents."""

    def __init__(self, db: Session):
        self.db = db

    def generate_ambition(self, agent: Agent) -> Optional[GoalPlan]:
        """Generate a long-term ambition for an agent based on traits."""
        # Check if agent already has an active ambition
        existing = (
            self.db.query(GoalPlan)
            .filter(
                GoalPlan.agent_id == agent.id,
                GoalPlan.status.in_([PlanStatus.PLANNING.value, PlanStatus.ACTIVE.value]),
            )
            .first()
        )
        if existing:
            return None

        # Get weighted ambition types based on traits
        traits = agent.traits_dict
        weighted_ambitions: list[tuple[AmbitionType, float]] = []

        for trait, ambition_types in TRAIT_AMBITION_MAPPINGS.items():
            trait_value = traits.get(trait, 5)
            if trait_value >= 6:  # Only consider high traits
                weight = (trait_value - 5) / 5  # 0.2 to 1.0 for values 6-10
                for ambition_type in ambition_types:
                    weighted_ambitions.append((ambition_type, weight))

        if not weighted_ambitions:
            return None

        # Select an ambition based on weights
        total_weight = sum(w for _, w in weighted_ambitions)
        if total_weight == 0:
            return None

        r = random.random() * total_weight
        cumulative = 0
        selected_ambition = None

        for ambition_type, weight in weighted_ambitions:
            cumulative += weight
            if r <= cumulative:
                selected_ambition = ambition_type
                break

        if not selected_ambition:
            selected_ambition = weighted_ambitions[0][0]

        return self._create_plan(agent, selected_ambition)

    def _create_plan(
        self,
        agent: Agent,
        ambition_type: AmbitionType,
        target_agent_id: Optional[str] = None,
    ) -> GoalPlan:
        """Create a new goal plan for an ambition."""
        milestones = AMBITION_MILESTONES.get(ambition_type, [])
        milestone_data = [
            {
                "description": m["description"],
                "weight": m["weight"],
                "status": "pending",
                "completed_at": None,
            }
            for m in milestones
        ]

        description = self._get_ambition_description(agent, ambition_type)

        plan = GoalPlan(
            agent_id=agent.id,
            type=ambition_type.value,
            description=description,
            progress=0.0,
            target_agent_id=target_agent_id,
            status=PlanStatus.ACTIVE.value,
            created_at=time.time(),
        )
        plan.milestones_list = milestone_data

        self.db.add(plan)
        return plan

    def _get_ambition_description(
        self,
        agent: Agent,
        ambition_type: AmbitionType,
    ) -> str:
        """Generate a description for an ambition."""
        descriptions = {
            AmbitionType.WEALTH: f"{agent.name} seeks to build wealth and prosperity",
            AmbitionType.POWER: f"{agent.name} aspires to gain power and influence",
            AmbitionType.KNOWLEDGE: f"{agent.name} is driven to acquire knowledge and wisdom",
            AmbitionType.ROMANCE: f"{agent.name} dreams of finding true love",
            AmbitionType.FAME: f"{agent.name} desires recognition and fame",
            AmbitionType.LEADERSHIP: f"{agent.name} wants to lead and inspire others",
            AmbitionType.COMMUNITY: f"{agent.name} is dedicated to improving village life",
            AmbitionType.MENTORSHIP: f"{agent.name} wishes to guide the next generation",
            AmbitionType.REDEMPTION: f"{agent.name} seeks to atone for past mistakes",
            AmbitionType.REVENGE: f"{agent.name} burns for revenge",
            AmbitionType.INDEPENDENCE: f"{agent.name} yearns for freedom and independence",
        }
        return descriptions.get(ambition_type, f"{agent.name} has an ambition")

    def update_plan_progress(self, plan: GoalPlan) -> float:
        """Update and return the progress of a goal plan."""
        milestones = plan.milestones_list
        total_weight = sum(m.get("weight", 25) for m in milestones)
        completed_weight = sum(
            m.get("weight", 25) for m in milestones if m.get("status") == "completed"
        )

        progress = (completed_weight / total_weight * 100) if total_weight > 0 else 0
        plan.progress = progress

        # Check if plan is complete
        if progress >= 100:
            plan.status = PlanStatus.COMPLETED.value

        return progress

    def complete_milestone(
        self,
        plan: GoalPlan,
        milestone_index: int,
    ) -> bool:
        """Mark a milestone as completed."""
        milestones = plan.milestones_list
        if milestone_index >= len(milestones):
            return False

        milestone = milestones[milestone_index]
        if milestone.get("status") == "completed":
            return False

        milestone["status"] = "completed"
        milestone["completed_at"] = time.time()
        plan.milestones_list = milestones

        self.update_plan_progress(plan)
        return True

    def generate_subgoals(self, plan: GoalPlan) -> list[Goal]:
        """Generate immediate sub-goals that support a long-term plan."""
        goals = []
        now = int(time.time())

        ambition_type = AmbitionType(plan.type)
        subgoal_types = AMBITION_SUBGOALS.get(ambition_type, [])

        # Find next pending milestone
        milestones = plan.milestones_list
        current_milestone = None
        for i, m in enumerate(milestones):
            if m.get("status") == "pending":
                current_milestone = m
                break

        for goal_type in subgoal_types[:2]:  # Max 2 subgoals at a time
            description = f"Working toward: {current_milestone['description']}" if current_milestone else f"Pursuing {ambition_type.value}"

            goal = Goal(
                agent_id=plan.agent_id,
                type=goal_type.value,
                description=description,
                priority=AMBITION_BASE_PRIORITY.get(ambition_type, 5),
                target_id=plan.target_agent_id,
                status="active",
                created_at=now,
                plan_id=plan.id,
            )
            goals.append(goal)
            self.db.add(goal)

        return goals

    def check_plan_progress(self, agent: Agent) -> Optional[str]:
        """Check if an agent's plan should progress based on completed goals."""
        plan = (
            self.db.query(GoalPlan)
            .filter(
                GoalPlan.agent_id == agent.id,
                GoalPlan.status == PlanStatus.ACTIVE.value,
            )
            .first()
        )

        if not plan:
            return None

        # Check for completed goals that support this plan
        completed_goals = (
            self.db.query(Goal)
            .filter(
                Goal.agent_id == agent.id,
                Goal.plan_id == plan.id,
                Goal.status == "completed",
            )
            .count()
        )

        # Find current milestone
        milestones = plan.milestones_list
        current_idx = None
        for i, m in enumerate(milestones):
            if m.get("status") == "pending":
                current_idx = i
                break

        # Progress milestone if enough subgoals completed
        if current_idx is not None and completed_goals >= 3:
            self.complete_milestone(plan, current_idx)
            return f"Milestone completed: {milestones[current_idx]['description']}"

        return None

    def get_plan_context(self, agent_id: str) -> str:
        """Get plan context string for LLM prompts."""
        plan = (
            self.db.query(GoalPlan)
            .filter(
                GoalPlan.agent_id == agent_id,
                GoalPlan.status.in_([PlanStatus.ACTIVE.value, PlanStatus.PLANNING.value]),
            )
            .first()
        )

        if not plan:
            return ""

        milestones = plan.milestones_list
        current_milestone = None
        for m in milestones:
            if m.get("status") == "pending":
                current_milestone = m
                break

        context = f"Your long-term ambition: {plan.description}\n"
        context += f"Progress: {plan.progress:.0f}%\n"

        if current_milestone:
            context += f"Current focus: {current_milestone['description']}"

        return context

    def get_all_active_plans(self) -> list[GoalPlan]:
        """Get all active goal plans."""
        return (
            self.db.query(GoalPlan)
            .filter(GoalPlan.status == PlanStatus.ACTIVE.value)
            .all()
        )

    def stall_plan(self, plan: GoalPlan, reason: str) -> None:
        """Mark a plan as stalled."""
        plan.status = PlanStatus.STALLED.value
        milestones = plan.milestones_list
        milestones.append({"note": f"Stalled: {reason}", "timestamp": time.time()})
        plan.milestones_list = milestones

    def resume_plan(self, plan: GoalPlan) -> None:
        """Resume a stalled plan."""
        plan.status = PlanStatus.ACTIVE.value

    def abandon_plan(self, plan: GoalPlan, reason: str = "Changed priorities") -> None:
        """Abandon a goal plan."""
        plan.status = PlanStatus.ABANDONED.value
        milestones = plan.milestones_list
        milestones.append({"note": f"Abandoned: {reason}", "timestamp": time.time()})
        plan.milestones_list = milestones

    def create_revenge_plan(
        self,
        agent: Agent,
        target_id: str,
    ) -> GoalPlan:
        """Create a revenge-focused goal plan (triggered by betrayal)."""
        plan = GoalPlan(
            agent_id=agent.id,
            type=AmbitionType.REVENGE.value,
            description=f"{agent.name} seeks revenge",
            progress=0.0,
            target_agent_id=target_id,
            status=PlanStatus.ACTIVE.value,
            created_at=time.time(),
        )
        plan.milestones_list = [
            {"description": "Gather information about the target", "weight": 20, "status": "pending"},
            {"description": "Build allies against the target", "weight": 25, "status": "pending"},
            {"description": "Undermine the target's reputation", "weight": 25, "status": "pending"},
            {"description": "Confront and defeat the target", "weight": 30, "status": "pending"},
        ]

        self.db.add(plan)
        return plan

    def create_romance_plan(
        self,
        agent: Agent,
        target_id: str,
    ) -> GoalPlan:
        """Create a romance-focused goal plan."""
        target = self.db.query(Agent).filter(Agent.id == target_id).first()
        target_name = target.name if target else "someone"

        plan = GoalPlan(
            agent_id=agent.id,
            type=AmbitionType.ROMANCE.value,
            description=f"{agent.name} is pursuing {target_name}",
            progress=0.0,
            target_agent_id=target_id,
            status=PlanStatus.ACTIVE.value,
            created_at=time.time(),
        )
        plan.milestones_list = [
            {"description": f"Get to know {target_name} better", "weight": 25, "status": "pending"},
            {"description": f"Impress {target_name} with kind acts", "weight": 25, "status": "pending"},
            {"description": f"Express romantic feelings", "weight": 25, "status": "pending"},
            {"description": f"Build a committed relationship", "weight": 25, "status": "pending"},
        ]

        self.db.add(plan)
        return plan
