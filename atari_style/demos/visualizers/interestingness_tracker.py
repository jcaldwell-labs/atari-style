"""Interestingness Tracker - Self-tuning system for any animation.

Monitors animation output and adjusts parameters to maintain visual interest.
Avoids boring attractors like:
- Static patterns (no change)
- Blank/empty screens
- Fully saturated screens
- Monotonic parameter drift

Key metrics:
1. Coverage - % of screen with visible content
2. Activity - How much coverage changes over time
3. Modulation Range - For composites, variation in modulation values
4. Color Diversity - Number of distinct colors visible
"""

import math
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any


@dataclass
class InterestingnessBounds:
    """Define the "interesting" range for each metric."""
    coverage_min: float = 15.0      # Below this = too empty
    coverage_max: float = 75.0      # Above this = too full
    coverage_sweet: float = 40.0    # Ideal target

    activity_min: float = 0.5       # Below this = too static
    activity_max: float = 20.0      # Above this = too chaotic
    activity_sweet: float = 3.0     # Ideal rate of change

    modulation_min: float = 0.1     # Below this = modulation not working
    modulation_range_min: float = 0.3  # Modulation should explore at least 30% of range


@dataclass
class AnimationMetrics:
    """Current state of animation metrics."""
    coverage: float = 0.0           # % of screen with content
    coverage_delta: float = 0.0     # Rate of change per second
    coverage_accel: float = 0.0     # 2nd derivative

    activity_variance: float = 0.0  # Variance over recent window

    modulation_value: float = 0.0   # Current modulation output
    modulation_min_seen: float = 1.0   # Min seen in window
    modulation_max_seen: float = -1.0  # Max seen in window
    modulation_range: float = 0.0   # Range explored

    color_count: int = 0            # Distinct colors visible

    # Derived scores (0-1, higher = more interesting)
    coverage_score: float = 0.0
    activity_score: float = 0.0
    modulation_score: float = 0.0
    overall_score: float = 0.0


class InterestingnessTracker:
    """Tracks and optimizes animation interestingness.

    Usage:
        tracker = InterestingnessTracker(bounds)

        # Each frame:
        tracker.sample_frame(buffer, modulation_value)
        metrics = tracker.get_metrics()

        # Get tuning suggestions:
        action = tracker.get_adjustment_action()
    """

    def __init__(self, bounds: InterestingnessBounds = None):
        self.bounds = bounds or InterestingnessBounds()

        # History windows
        self.coverage_history: List[float] = []
        self.modulation_history: List[float] = []
        self.history_window = 60  # ~2 seconds at 30fps

        # Current metrics
        self.metrics = AnimationMetrics()

        # Tracking state
        self.session_time = 0.0
        self.last_adjustment_time = 0.0
        self.settling_time = 1.0  # Wait after adjustments

        # Color tracking
        self.colors_seen: set = set()

    def sample_frame(self, buffer: List[List[str]], color_buffer: List[List[Any]] = None,
                    modulation_value: float = None):
        """Sample current frame and update metrics.

        Args:
            buffer: 2D character buffer (height x width)
            color_buffer: Optional 2D color buffer
            modulation_value: Current modulation output (for composites)
        """
        if not buffer:
            return

        height = len(buffer)
        width = len(buffer[0]) if buffer else 0
        total_cells = height * width

        if total_cells == 0:
            return

        # Count non-empty cells
        filled = 0
        for row in buffer:
            for char in row:
                if char != ' ':
                    filled += 1

        coverage = (filled / total_cells) * 100

        # Update coverage history
        self.coverage_history.append(coverage)
        if len(self.coverage_history) > self.history_window:
            self.coverage_history.pop(0)

        self.metrics.coverage = coverage

        # Calculate delta (rate of change)
        if len(self.coverage_history) >= 2:
            # Use 5-frame window for smoothing
            window = min(5, len(self.coverage_history))
            old_avg = sum(self.coverage_history[-window-5:-window]) / window if len(self.coverage_history) > window + 5 else self.coverage_history[0]
            new_avg = sum(self.coverage_history[-window:]) / window
            # Convert to per-second (assuming 30 fps)
            self.metrics.coverage_delta = (new_avg - old_avg) * 30 / window

        # Calculate activity variance
        if len(self.coverage_history) >= 10:
            mean = sum(self.coverage_history) / len(self.coverage_history)
            variance = sum((c - mean) ** 2 for c in self.coverage_history) / len(self.coverage_history)
            self.metrics.activity_variance = math.sqrt(variance)

        # Track modulation
        if modulation_value is not None:
            self.modulation_history.append(modulation_value)
            if len(self.modulation_history) > self.history_window:
                self.modulation_history.pop(0)

            self.metrics.modulation_value = modulation_value
            self.metrics.modulation_min_seen = min(self.metrics.modulation_min_seen, modulation_value)
            self.metrics.modulation_max_seen = max(self.metrics.modulation_max_seen, modulation_value)
            self.metrics.modulation_range = self.metrics.modulation_max_seen - self.metrics.modulation_min_seen

        # Track colors
        if color_buffer:
            for row in color_buffer:
                for color in row:
                    if color is not None:
                        self.colors_seen.add(color)
            self.metrics.color_count = len(self.colors_seen)

        # Calculate scores
        self._calculate_scores()

    def _calculate_scores(self):
        """Calculate interest scores from metrics."""
        b = self.bounds
        m = self.metrics

        # Coverage score: Gaussian around sweet spot
        coverage_diff = abs(m.coverage - b.coverage_sweet)
        max_diff = max(b.coverage_sweet - b.coverage_min, b.coverage_max - b.coverage_sweet)
        m.coverage_score = max(0, 1 - (coverage_diff / max_diff) ** 2)

        # Activity score: Higher is better up to a point
        if m.activity_variance < b.activity_min:
            m.activity_score = m.activity_variance / b.activity_min
        elif m.activity_variance > b.activity_max:
            m.activity_score = max(0, 1 - (m.activity_variance - b.activity_max) / b.activity_max)
        else:
            # In sweet spot
            m.activity_score = 1.0

        # Modulation score: Based on range explored
        if m.modulation_range > 0:
            m.modulation_score = min(1.0, m.modulation_range / b.modulation_range_min)
        else:
            m.modulation_score = 0.0

        # Overall: weighted average
        m.overall_score = (
            m.coverage_score * 0.4 +
            m.activity_score * 0.3 +
            m.modulation_score * 0.3
        )

    def get_metrics(self) -> AnimationMetrics:
        """Get current metrics."""
        return self.metrics

    def is_boring(self) -> bool:
        """True if animation is currently boring."""
        return self.metrics.overall_score < 0.4

    def is_interesting(self) -> bool:
        """True if animation is currently interesting."""
        return self.metrics.overall_score > 0.7

    def get_diagnosis(self) -> str:
        """Get human-readable diagnosis of current state."""
        m = self.metrics
        b = self.bounds

        issues = []

        if m.coverage < b.coverage_min:
            issues.append(f"TOO EMPTY ({m.coverage:.0f}%)")
        elif m.coverage > b.coverage_max:
            issues.append(f"TOO FULL ({m.coverage:.0f}%)")

        if m.activity_variance < b.activity_min:
            issues.append("STATIC (no motion)")
        elif m.activity_variance > b.activity_max:
            issues.append("CHAOTIC (too fast)")

        if m.modulation_range < b.modulation_range_min and len(self.modulation_history) > 30:
            issues.append(f"WEAK MODULATION (range={m.modulation_range:.2f})")

        if not issues:
            return f"INTERESTING (score={m.overall_score:.2f})"

        return " | ".join(issues)

    def get_adjustment_suggestion(self) -> Dict[str, Any]:
        """Get suggested parameter adjustments.

        Returns dict with:
            - 'action': What to do ('increase_activity', 'decrease_activity', etc.)
            - 'reason': Why
            - 'magnitude': How much (0-1)
        """
        m = self.metrics
        b = self.bounds

        # Priority 1: Fix empty/full
        if m.coverage < b.coverage_min:
            return {
                'action': 'increase_energy',
                'reason': f'Screen too empty ({m.coverage:.0f}%)',
                'magnitude': (b.coverage_min - m.coverage) / b.coverage_sweet
            }

        if m.coverage > b.coverage_max:
            return {
                'action': 'decrease_energy',
                'reason': f'Screen too full ({m.coverage:.0f}%)',
                'magnitude': (m.coverage - b.coverage_max) / (100 - b.coverage_max)
            }

        # Priority 2: Fix static/chaotic
        if m.activity_variance < b.activity_min:
            return {
                'action': 'increase_dynamics',
                'reason': f'Too static (variance={m.activity_variance:.1f})',
                'magnitude': 1 - (m.activity_variance / b.activity_min)
            }

        if m.activity_variance > b.activity_max:
            return {
                'action': 'decrease_dynamics',
                'reason': f'Too chaotic (variance={m.activity_variance:.1f})',
                'magnitude': (m.activity_variance - b.activity_max) / b.activity_max
            }

        # Priority 3: Fix weak modulation
        if m.modulation_range < b.modulation_range_min and len(self.modulation_history) > 30:
            return {
                'action': 'increase_modulation',
                'reason': f'Weak modulation (range={m.modulation_range:.2f})',
                'magnitude': 1 - (m.modulation_range / b.modulation_range_min)
            }

        # All good
        return {
            'action': 'none',
            'reason': 'Animation is interesting',
            'magnitude': 0
        }

    def reset_modulation_tracking(self):
        """Reset modulation range tracking (call when changing modes)."""
        self.metrics.modulation_min_seen = 1.0
        self.metrics.modulation_max_seen = -1.0
        self.metrics.modulation_range = 0.0
        self.modulation_history.clear()
        self.colors_seen.clear()


class SelfTuningAnimation:
    """Base class for self-tuning animations.

    Subclass and implement:
    - get_tunable_params() -> dict of param name -> (current, min, max, step)
    - apply_adjustment(action, magnitude)
    - sample_modulation_value() -> float (for composites)
    """

    def __init__(self, bounds: InterestingnessBounds = None):
        self.tracker = InterestingnessTracker(bounds)
        self.auto_tune = True
        self.tune_interval = 0.5  # Check every 0.5s
        self.last_tune_time = 0.0
        self.session_time = 0.0

    def update_tracking(self, dt: float, buffer: List[List[str]],
                       color_buffer: List[List[Any]] = None):
        """Call each frame to update tracking."""
        self.session_time += dt

        # Sample modulation if available
        mod_value = self.sample_modulation_value()
        self.tracker.sample_frame(buffer, color_buffer, mod_value)

        # Auto-tune
        if self.auto_tune and self.session_time - self.last_tune_time > self.tune_interval:
            suggestion = self.tracker.get_adjustment_suggestion()
            if suggestion['action'] != 'none':
                self.apply_adjustment(suggestion['action'], suggestion['magnitude'])
            self.last_tune_time = self.session_time

    def get_tunable_params(self) -> Dict[str, tuple]:
        """Override: Return dict of param_name -> (current, min, max, step)."""
        return {}

    def apply_adjustment(self, action: str, magnitude: float):
        """Override: Apply the suggested adjustment."""
        pass

    def sample_modulation_value(self) -> Optional[float]:
        """Override for composites: Return current modulation value."""
        return None

    def get_status(self) -> str:
        """Get status string for display."""
        m = self.tracker.metrics
        return (f"Score: {m.overall_score:.2f} | "
                f"Cov: {m.coverage:.0f}% | "
                f"Activity: {m.activity_variance:.1f} | "
                f"{self.tracker.get_diagnosis()}")


# Pre-configured bounds for different animation types
BOUNDS_FLUID = InterestingnessBounds(
    coverage_min=20, coverage_max=60, coverage_sweet=40,
    activity_min=1.0, activity_max=15.0, activity_sweet=5.0,
    modulation_range_min=0.4
)

BOUNDS_GEOMETRIC = InterestingnessBounds(
    coverage_min=5, coverage_max=40, coverage_sweet=20,
    activity_min=0.3, activity_max=10.0, activity_sweet=2.0,
    modulation_range_min=0.3
)

BOUNDS_PLASMA = InterestingnessBounds(
    coverage_min=60, coverage_max=95, coverage_sweet=80,
    activity_min=0.5, activity_max=8.0, activity_sweet=2.0,
    modulation_range_min=0.2
)
