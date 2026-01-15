"""Narrative arc analysis and story digest generation."""

import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from hamlet.db.models import Agent, ArcEvent, Event, NarrativeArc
from hamlet.narrative_arcs.types import (
    ACT_NAMES,
    ARC_BASE_SIGNIFICANCE,
    ARC_THEMES,
    Act,
    ArcStatus,
    ArcType,
)


@dataclass
class StoryDigest:
    """A summary of narrative activity."""

    title: str
    summary: str
    active_arcs: list[dict]
    completed_arcs: list[dict]
    notable_moments: list[str]
    suggested_focus: Optional[str]


class NarrativeAnalyzer:
    """Analyzes narrative arcs and generates story digests."""

    def __init__(self, db: Session):
        self.db = db

    def generate_daily_digest(self) -> StoryDigest:
        """Generate a digest of narrative activity for the past day."""
        day_ago = time.time() - 86400

        # Get active arcs
        active_arcs = (
            self.db.query(NarrativeArc)
            .filter(
                NarrativeArc.status.notin_(
                    [ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]
                )
            )
            .order_by(NarrativeArc.significance.desc())
            .all()
        )

        # Get recently completed arcs
        completed_arcs = (
            self.db.query(NarrativeArc)
            .filter(
                NarrativeArc.status == ArcStatus.RESOLUTION.value,
                NarrativeArc.completed_at >= day_ago,
            )
            .all()
        )

        # Compile active arc summaries
        active_summaries = []
        for arc in active_arcs[:5]:  # Top 5
            active_summaries.append(self._summarize_arc(arc))

        # Compile completed arc summaries
        completed_summaries = []
        for arc in completed_arcs:
            completed_summaries.append(self._summarize_arc(arc, completed=True))

        # Find notable moments
        notable = self._find_notable_moments(day_ago)

        # Generate suggested focus
        suggested = self._suggest_focus(active_arcs)

        # Build summary text
        if active_arcs:
            highest_arc = active_arcs[0]
            summary = (
                f"The village is alive with {len(active_arcs)} ongoing narratives. "
                f"The most significant is '{highest_arc.title}', "
                f"currently in its {ACT_NAMES.get(highest_arc.current_act, 'unfolding')} phase."
            )
        else:
            summary = "The village is quiet, waiting for new stories to unfold."

        if completed_arcs:
            summary += f" {len(completed_arcs)} stories reached their conclusion today."

        return StoryDigest(
            title="Village Chronicle",
            summary=summary,
            active_arcs=active_summaries,
            completed_arcs=completed_summaries,
            notable_moments=notable,
            suggested_focus=suggested,
        )

    def _summarize_arc(self, arc: NarrativeArc, completed: bool = False) -> dict:
        """Create a summary dict for an arc."""
        primary = self.db.query(Agent).filter(Agent.id == arc.primary_agent_id).first()
        secondary = (
            self.db.query(Agent).filter(Agent.id == arc.secondary_agent_id).first()
            if arc.secondary_agent_id
            else None
        )

        # Count events in this arc
        event_count = (
            self.db.query(ArcEvent).filter(ArcEvent.arc_id == arc.id).count()
        )

        # Get key moments from all acts
        acts = arc.acts_list
        key_moments = []
        for act_data in acts:
            act = Act.from_dict(act_data)
            key_moments.extend(act.key_moments)

        return {
            "id": arc.id,
            "title": arc.title,
            "type": arc.type,
            "theme": arc.theme,
            "primary_agent": primary.name if primary else arc.primary_agent_id,
            "secondary_agent": secondary.name if secondary else arc.secondary_agent_id,
            "current_act": ACT_NAMES.get(arc.current_act, "Unknown"),
            "status": arc.status,
            "significance": arc.significance,
            "event_count": event_count,
            "key_moments": key_moments[-3:],  # Last 3 key moments
            "completed": completed,
        }

    def _find_notable_moments(self, since: float) -> list[str]:
        """Find notable moments from arc events."""
        notable = []

        # Get recent arc events that are turning points
        arc_events = (
            self.db.query(ArcEvent)
            .join(Event)
            .filter(
                ArcEvent.is_turning_point == True,
                Event.timestamp >= since,
            )
            .order_by(Event.timestamp.desc())
            .limit(10)
            .all()
        )

        for arc_event in arc_events:
            event = self.db.query(Event).filter(Event.id == arc_event.event_id).first()
            if event:
                notable.append(event.summary)

        return notable

    def _suggest_focus(self, active_arcs: list[NarrativeArc]) -> Optional[str]:
        """Suggest which arc to focus on next."""
        if not active_arcs:
            return None

        # Find arcs at climax - these are the most interesting
        climax_arcs = [a for a in active_arcs if a.status == ArcStatus.CLIMAX.value]
        if climax_arcs:
            arc = climax_arcs[0]
            return f"'{arc.title}' is at its climax! Pay attention to what happens next."

        # Find arcs with highest significance that are rising
        rising_arcs = [a for a in active_arcs if a.status == ArcStatus.RISING_ACTION.value]
        if rising_arcs:
            arc = max(rising_arcs, key=lambda a: a.significance)
            return f"'{arc.title}' is building toward something significant."

        # Default to most significant active arc
        arc = active_arcs[0]
        return f"Watch '{arc.title}' for developing drama."

    def calculate_arc_score(self, arc: NarrativeArc) -> int:
        """Calculate a narrative interest score for an arc."""
        base_score = ARC_BASE_SIGNIFICANCE.get(ArcType(arc.type), 5)

        # Bonus for climax
        if arc.status == ArcStatus.CLIMAX.value:
            base_score += 3

        # Bonus for event count
        event_count = self.db.query(ArcEvent).filter(ArcEvent.arc_id == arc.id).count()
        base_score += min(event_count // 3, 3)

        # Bonus for multiple protagonists
        if arc.secondary_agent_id:
            base_score += 1

        return min(base_score, 10)

    def predict_arc_development(self, arc: NarrativeArc) -> dict:
        """Predict what might happen next in an arc."""
        arc_type = ArcType(arc.type)
        current_act = arc.current_act

        predictions = {
            "likely_next_event": None,
            "potential_turning_point": None,
            "completion_likelihood": 0,
            "interest_trajectory": "stable",
        }

        if current_act == 0:  # Exposition
            predictions["likely_next_event"] = "Character development and relationship building"
            predictions["potential_turning_point"] = "An inciting incident that escalates the situation"
            predictions["interest_trajectory"] = "rising"

        elif current_act == 1:  # Rising Action
            predictions["likely_next_event"] = "Increasing tension and complications"
            predictions["potential_turning_point"] = "A critical confrontation or revelation"
            predictions["completion_likelihood"] = 20
            predictions["interest_trajectory"] = "rising"

        elif current_act == 2:  # Climax
            predictions["likely_next_event"] = "The decisive moment of the story"
            predictions["potential_turning_point"] = "Resolution of the central conflict"
            predictions["completion_likelihood"] = 50
            predictions["interest_trajectory"] = "peak"

        elif current_act == 3:  # Falling Action
            predictions["likely_next_event"] = "Consequences playing out"
            predictions["potential_turning_point"] = "New equilibrium established"
            predictions["completion_likelihood"] = 80
            predictions["interest_trajectory"] = "falling"

        elif current_act == 4:  # Resolution
            predictions["likely_next_event"] = "Story conclusion"
            predictions["completion_likelihood"] = 100
            predictions["interest_trajectory"] = "complete"

        return predictions

    def get_arc_timeline(self, arc_id: int) -> list[dict]:
        """Get a timeline of events for an arc."""
        arc_events = (
            self.db.query(ArcEvent)
            .filter(ArcEvent.arc_id == arc_id)
            .order_by(ArcEvent.act_number)
            .all()
        )

        timeline = []
        for arc_event in arc_events:
            event = self.db.query(Event).filter(Event.id == arc_event.event_id).first()
            if event:
                timeline.append({
                    "act": ACT_NAMES.get(arc_event.act_number, "Unknown"),
                    "timestamp": event.timestamp,
                    "summary": event.summary,
                    "is_turning_point": arc_event.is_turning_point,
                    "significance": event.significance,
                })

        return timeline

    def generate_arc_narrative(self, arc: NarrativeArc) -> str:
        """Generate a prose narrative summary of an arc."""
        primary = self.db.query(Agent).filter(Agent.id == arc.primary_agent_id).first()
        secondary = (
            self.db.query(Agent).filter(Agent.id == arc.secondary_agent_id).first()
            if arc.secondary_agent_id
            else None
        )

        primary_name = primary.name if primary else "Someone"
        secondary_name = secondary.name if secondary else None

        arc_type = ArcType(arc.type)
        acts = arc.acts_list

        narrative_parts = [f"# {arc.title}\n"]
        narrative_parts.append(f"*{arc.theme}*\n")

        for act_data in acts:
            act = Act.from_dict(act_data)
            if not act.key_moments and not act.turning_point:
                continue

            narrative_parts.append(f"\n## {ACT_NAMES.get(act.number, 'Chapter')}\n")

            for moment in act.key_moments:
                narrative_parts.append(f"- {moment}")

            if act.turning_point:
                narrative_parts.append(f"\n*Turning point: {act.turning_point}*")

        if arc.status == ArcStatus.RESOLUTION.value:
            narrative_parts.append("\n---\n*This story has concluded.*")
        else:
            narrative_parts.append(f"\n---\n*This story continues... (Currently in {ACT_NAMES.get(arc.current_act, 'progress')})*")

        return "\n".join(narrative_parts)

    def get_village_story_state(self) -> dict:
        """Get an overview of all narrative activity in the village."""
        all_arcs = self.db.query(NarrativeArc).all()

        active = [a for a in all_arcs if a.status not in [ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]]
        completed = [a for a in all_arcs if a.status == ArcStatus.RESOLUTION.value]
        abandoned = [a for a in all_arcs if a.status == ArcStatus.ABANDONED.value]

        # Count by type
        type_counts = {}
        for arc in active:
            arc_type = arc.type
            type_counts[arc_type] = type_counts.get(arc_type, 0) + 1

        # Find the most dramatic arc (at climax with highest significance)
        climax_arcs = [a for a in active if a.status == ArcStatus.CLIMAX.value]
        most_dramatic = max(climax_arcs, key=lambda a: a.significance) if climax_arcs else None

        return {
            "total_arcs": len(all_arcs),
            "active_arcs": len(active),
            "completed_arcs": len(completed),
            "abandoned_arcs": len(abandoned),
            "arcs_by_type": type_counts,
            "most_dramatic_arc": self._summarize_arc(most_dramatic) if most_dramatic else None,
            "narrative_intensity": self._calculate_narrative_intensity(active),
        }

    def _calculate_narrative_intensity(self, active_arcs: list[NarrativeArc]) -> str:
        """Calculate overall narrative intensity."""
        if not active_arcs:
            return "quiet"

        climax_count = sum(1 for a in active_arcs if a.status == ArcStatus.CLIMAX.value)
        rising_count = sum(1 for a in active_arcs if a.status == ArcStatus.RISING_ACTION.value)

        if climax_count >= 2:
            return "explosive"
        elif climax_count >= 1:
            return "dramatic"
        elif rising_count >= 3:
            return "building"
        elif len(active_arcs) >= 3:
            return "active"
        else:
            return "developing"
