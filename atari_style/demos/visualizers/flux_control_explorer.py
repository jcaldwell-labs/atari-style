"""Flux Control Explorer - Find self-organized criticality parameters."""

import time
import json
import math
from pathlib import Path
from blessed import Terminal
from ...core.renderer import Renderer, Color
from .flux_control_zen import FluidLattice


# ============================================================
# FLUID EQUILIBRIUM MODEL (derived from empirical analysis)
# ============================================================
#
# At equilibrium: energy_in = energy_out
#   rain * drop_strength = total_energy * (1 - damping) * fps
#
# The relationship between coverage and rain/(1-damping) is exponential:
#   rain / (1 - damping) = A * exp(B * C)
#
# Fitted constants from empirical data:
EQUILIBRIUM_A = 2.346  # Base ratio
EQUILIBRIUM_B = 2.424  # Exponential coefficient

# Damping linear fit (for "normal" dynamics):
#   damping = DAMP_INTERCEPT + DAMP_SLOPE * coverage
DAMP_INTERCEPT = 0.7019
DAMP_SLOPE = 0.2143


def get_equilibrium_params(target_coverage: float, dynamics: str = "normal") -> tuple:
    """Calculate exact rain/damping for target coverage.

    The equilibrium formula was calibrated for "normal" dynamics. Different modes
    have different energy-to-coverage relationships:

    - CALM: Fast decay + concentrated energy = needs MORE rain for same coverage
    - CHAOTIC: Slow decay + spread energy = needs LESS rain for same coverage

    Args:
        target_coverage: Target coverage percentage (0-100)
        dynamics: One of "calm", "normal", "chaotic"

    Returns:
        (rain, damping) tuple that produces target coverage at equilibrium
    """
    C = target_coverage / 100.0

    # Choose damping based on dynamics mode
    if dynamics == "calm":
        # Low damping = fast decay, isolated ripples
        damping = 0.70 + 0.08 * C  # Range 0.70-0.78
        # CALM needs ~8x more rain due to fast decay AND concentrated energy
        # Energy is concentrated so coverage is much lower for same total energy
        dynamics_multiplier = 8.0
    elif dynamics == "chaotic":
        # High damping = slow decay, energy buildup, edge of chaos
        damping = 0.90 + 0.05 * C  # Range 0.90-0.95
        # CHAOTIC needs ~0.12x rain due to slow decay AND spread energy
        # Energy spreads out so coverage is much higher for same rain input
        dynamics_multiplier = 0.12
    else:  # normal
        damping = DAMP_INTERCEPT + DAMP_SLOPE * C
        dynamics_multiplier = 1.0

    # Calculate rain from equilibrium formula (calibrated for normal mode)
    ratio = EQUILIBRIUM_A * math.exp(EQUILIBRIUM_B * C)
    rain = ratio * (1 - damping) * dynamics_multiplier

    # Clamp to valid ranges
    damping = max(0.60, min(0.98, damping))
    rain = max(0.1, min(5.0, rain))

    return rain, damping


def get_time_constant(damping: float, fps: float = 30.0) -> float:
    """Calculate time to reach 97% of equilibrium (5 half-lives).

    Args:
        damping: Damping coefficient (0-1)
        fps: Frames per second

    Returns:
        Time in seconds to reach near-equilibrium
    """
    if damping <= 0 or damping >= 1:
        return float('inf')
    half_life_frames = math.log(0.5) / math.log(damping)
    half_life_seconds = half_life_frames / fps
    return 5 * half_life_seconds  # 5 half-lives = 97% of equilibrium


def get_dynamics_ranges():
    """Return parameter ranges for different dynamics modes.

    Returns:
        Dict with 'calm', 'normal', 'chaotic' keys, each containing
        parameter ranges that produce interesting behavior.
    """
    return {
        'calm': {
            'wave_speed': (0.20, 0.40),
            'damping': (0.70, 0.80),
            'rain_rate': (0.30, 1.00),
            'description': 'Quick decay, isolated ripples, meditative'
        },
        'normal': {
            'wave_speed': (0.35, 0.55),
            'damping': (0.78, 0.88),
            'rain_rate': (0.80, 2.50),
            'description': 'Balanced propagation and decay'
        },
        'chaotic': {
            'wave_speed': (0.50, 0.80),
            'damping': (0.90, 0.96),
            'rain_rate': (2.00, 4.00),
            'description': 'Slow decay, energy buildup, edge of chaos'
        }
    }


class CriticalityTracker:
    """PID-like controller with time constant awareness and acceleration tracking."""

    def __init__(self, fluid: FluidLattice):
        self.fluid = fluid
        self.target_coverage = 40.0
        self.status_text = "Initializing..."

        # Dynamics mode affects equilibrium calculations
        self.dynamics_mode = "normal"  # "calm", "normal", or "chaotic"

        # Stability tracking
        self.stable_time = 0.0
        self.last_adjustment_time = 0.0
        self.settling_time = 2.0  # Wait 2s after adjustment for system to respond
        self.session_time = 0.0

        # Track if system is settling after an adjustment
        self.is_settling = False
        self.last_action = None

        # Second-order tracking (acceleration = d²coverage/dt²)
        self.delta_history = []  # Recent delta values
        self.delta_history_window = 10  # ~0.33s at 30fps

    def update(self, dt):
        """Update status and track stability."""
        self.session_time += dt
        coverage = self.fluid.get_coverage_percent()
        delta = self.fluid.get_coverage_delta()
        diff = coverage - self.target_coverage

        # Track delta history for acceleration calculation
        self.delta_history.append(delta)
        if len(self.delta_history) > self.delta_history_window:
            self.delta_history.pop(0)

        # Check if still settling from last adjustment
        time_since_adjust = self.session_time - self.last_adjustment_time
        if time_since_adjust < self.settling_time:
            self.is_settling = True
            self.status_text = f"Settling... ({time_since_adjust:.1f}s)"
        else:
            self.is_settling = False

            if abs(diff) < 5:
                self.status_text = "ON TARGET"
                self.stable_time += dt
            elif abs(diff) < 10:
                self.status_text = "Nearly there..."
                self.stable_time = max(0, self.stable_time - dt)
            else:
                if diff > 0:
                    self.status_text = f"High ({coverage:.0f}%)"
                else:
                    self.status_text = f"Low ({coverage:.0f}%)"
                self.stable_time = 0

    def get_acceleration(self):
        """Calculate second derivative: rate of change of delta (d²coverage/dt²).

        Positive acceleration = delta is increasing (coverage speeding up)
        Negative acceleration = delta is decreasing (coverage slowing down)
        """
        if len(self.delta_history) < 3:
            return 0.0
        # Compare recent delta to older delta
        # Using first third vs last third of history for stability
        n = len(self.delta_history)
        old_avg = sum(self.delta_history[:n//3]) / (n//3) if n//3 > 0 else 0
        new_avg = sum(self.delta_history[-(n//3):]) / (n//3) if n//3 > 0 else 0
        # Time span is roughly (n * dt) where dt ≈ 0.033s
        time_span = n * 0.033
        if time_span == 0:
            return 0.0
        return (new_avg - old_avg) / time_span

    def is_stable(self):
        """True if we've been on target for 5+ seconds."""
        return self.stable_time > 5.0

    def estimate_equilibrium_params(self, target_pct, dynamics: str = None):
        """Calculate exact equilibrium parameters for target coverage.

        Uses the exponential model derived from empirical analysis:
          rain / (1 - damping) = A * exp(B * C)

        Args:
            target_pct: Target coverage percentage (0-100)
            dynamics: "calm", "normal", or "chaotic". If None, uses self.dynamics_mode

        Returns:
            (rain, damping) tuple for equilibrium at target coverage
        """
        if dynamics is None:
            dynamics = self.dynamics_mode
        return get_equilibrium_params(target_pct, dynamics)

    def get_adjustment(self, params):
        """Controller using acceleration (2nd derivative) for predictive braking.

        Key insight: If acceleration has same sign as delta, system is speeding up
        toward overshoot. If opposite sign, system is naturally slowing down.

        Physics analogy:
        - diff = position error (how far from target)
        - delta = velocity (rate of change)
        - accel = acceleration (is velocity increasing or decreasing?)

        TUNED FOR 30-50% VISUAL RANGE:
        - Soft ceiling at 50%: always brake when above
        - Early braking: trigger at delta > 8 instead of 15
        - Sensitive prediction: brake when predicted_diff > 2
        """
        coverage = self.fluid.get_coverage_percent()
        delta = self.fluid.get_coverage_delta()
        accel = self.get_acceleration()
        diff = coverage - self.target_coverage

        rain_val = params['rain_rate']['value']
        damp_val = params['damping']['value']

        # SOFT CEILING: Above 50% and still rising? Controlled correction
        # This keeps us in the 30-50% visual sweet spot
        # Strategy: Drain frequently to knock down peaks, don't cut rain too low
        if coverage > 50 and delta > 0:
            # Aggressive drain when coverage exceeds 52% - instant effect
            if coverage > 52:
                return 'drain', 0
            # Light rain reduction at 50-52% (don't go below 0.40)
            elif rain_val > 0.40:
                return 'rain_rate', -1
            # Drain if rain already at floor
            else:
                return 'drain', 0

        # On target - no adjustment
        if abs(diff) < 5:
            return None, 0

        # EMERGENCY: Stuck at saturation equilibrium (not moving at all)
        # Only drain when truly stuck, not when already decreasing
        if coverage > 85 and abs(delta) < 0.5 and accel > -0.5:
            # System is stuck at saturation AND not accelerating downward
            return 'drain', 0

        # PREDICTIVE BRAKING using acceleration
        # The key: brake harder when predicted overshoot is larger
        # Return (action, magnitude) where magnitude indicates how many steps

        # Case 1: Below target, rising toward it
        if diff < 0 and delta > 0:
            # MODERATE BRAKE: Don't cut rain below 0.40 to keep equilibrium reasonable
            rain_floor = 0.40

            # Fast growth rate - brake but don't over-correct
            if delta > 8:
                brake_steps = min(3, max(1, int(delta / 5)))
                if rain_val > rain_floor:
                    return 'rain_rate', -brake_steps
                return None, 0

            # Predict where we'll be: kinematic estimate with 1.5-second lookahead
            t_lookahead = 1.5
            predicted_coverage = coverage + delta * t_lookahead + 0.5 * accel * t_lookahead * t_lookahead
            predicted_diff = predicted_coverage - self.target_coverage

            # Brake when predicted to overshoot by 5+
            if predicted_diff > 5:
                brake_steps = min(3, max(1, int(predicted_diff / 5)))
                if rain_val > rain_floor:
                    return 'rain_rate', -brake_steps
                return None, 0

            # Light brake when rising with acceleration
            if accel > 0.5 and delta > 4:
                if rain_val > rain_floor:
                    return 'rain_rate', -1
                return None, 0

            # Already heading toward target with manageable momentum - coast
            if delta > 1:
                return None, 0

        # Case 2: Above target, falling toward it
        if diff > 0 and delta < 0:
            # CRITICAL: If delta alone is very negative, brake immediately!
            if delta < -15:
                # Massive fall rate - emergency brake!
                brake_steps = min(5, max(2, int(abs(delta) / 8)))
                if rain_val < 4.5:
                    return 'rain_rate', brake_steps
                return None, 0

            # Predict where we'll be with 2-second lookahead
            t_lookahead = 2.0
            predicted_coverage = coverage + delta * t_lookahead + 0.5 * accel * t_lookahead * t_lookahead
            predicted_diff = predicted_coverage - self.target_coverage

            if predicted_diff < -5:
                # We're going to undershoot - brake proportionally!
                brake_steps = min(5, int(abs(predicted_diff) / 5))
                if rain_val < 4.5:
                    return 'rain_rate', brake_steps
                return None, 0

            if accel < -1 and delta < -5:
                # Falling fast with negative acceleration - brake lightly
                if rain_val < 4.5:
                    return 'rain_rate', +1
                return None, 0

            # Already heading toward target with manageable momentum - coast
            if delta < -1:
                return None, 0

        # Respect settling time for non-urgent adjustments
        if self.is_settling:
            return None, 0

        # Calculate ideal parameters
        ideal_rain, ideal_damp = self.estimate_equilibrium_params(self.target_coverage)

        if diff > 0:  # Too high and not heading down fast
            rain_diff = rain_val - ideal_rain
            damp_diff = damp_val - ideal_damp

            if rain_diff > 0.1:
                return 'rain_rate', -1
            elif damp_diff > 0.02:
                return 'damping', -1
            elif rain_val > 0.15:
                return 'rain_rate', -1
            elif damp_val > 0.62:
                return 'damping', -1
            else:
                return 'drain', 0

        else:  # Too low and not heading up fast
            # NEAR ZERO: Prioritize damping increase to accumulate energy
            # Higher damping = slower decay = energy builds up faster
            if coverage < 10:
                # At near-zero, increase damping first (more impactful than rain)
                if damp_val < ideal_damp:
                    return 'damping', +1
                elif rain_val < ideal_rain:
                    return 'rain_rate', +1
                return None, 0

            # WELL BELOW TARGET (>15% below): increase rain
            if diff < -15:
                rain_diff = ideal_rain - rain_val
                if rain_diff > 0.05:
                    return 'rain_rate', +1
                elif rain_val < 4.5:
                    return 'rain_rate', +1

            # CLOSE TO TARGET (5-15% below): tiny adjustment
            elif diff < -5:
                if rain_val < ideal_rain - 0.1:
                    return 'rain_rate', +1

            return None, 0

        return None, 0

    def record_adjustment(self):
        """Call this after making an adjustment to start settling timer."""
        self.last_adjustment_time = self.session_time

    def get_status_color(self):
        """Color based on how close to target."""
        coverage = self.fluid.get_coverage_percent()
        diff = abs(coverage - self.target_coverage)
        if diff < 5:
            return Color.BRIGHT_GREEN
        elif diff < 15:
            return Color.YELLOW
        else:
            return Color.RED


class PresetManager:
    """Save/load parameter presets."""

    PRESET_DIR = Path.home() / ".atari-style"
    PRESET_FILE = PRESET_DIR / "flux_presets.json"

    DEFAULT_PRESETS = {
        "default": {"wave_speed": 0.45, "damping": 0.86, "rain_rate": 1.5},
        "chaotic": {"wave_speed": 0.7, "damping": 0.92, "rain_rate": 3.5},
        "calm": {"wave_speed": 0.3, "damping": 0.80, "rain_rate": 0.8},
        "edge": {"wave_speed": 0.5, "damping": 0.88, "rain_rate": 2.0},
    }

    def __init__(self):
        self._ensure_dir()
        self.presets = self.load_all()

    def _ensure_dir(self):
        self.PRESET_DIR.mkdir(parents=True, exist_ok=True)

    def load_all(self) -> dict:
        presets = dict(self.DEFAULT_PRESETS)
        if self.PRESET_FILE.exists():
            try:
                with open(self.PRESET_FILE, 'r') as f:
                    presets.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
        return presets

    def save_preset(self, name: str, params: dict):
        self.presets[name] = {
            'wave_speed': params['wave_speed']['value'],
            'damping': params['damping']['value'],
            'rain_rate': params['rain_rate']['value'],
        }
        user_presets = {k: v for k, v in self.presets.items()
                       if k not in self.DEFAULT_PRESETS}
        try:
            with open(self.PRESET_FILE, 'w') as f:
                json.dump(user_presets, f, indent=2)
        except IOError:
            pass

    def get_preset(self, name: str) -> dict:
        return self.presets.get(name)

    def get_preset_names(self) -> list:
        return list(self.presets.keys())


class FluxControlExplorer:
    """Explorer mode for finding self-organized criticality."""

    def __init__(self):
        self.renderer = Renderer()
        self.term = Terminal()

        # Display layout
        self.control_panel_height = 10
        self.view_height = self.renderer.height - self.control_panel_height
        self.view_width = self.renderer.width

        # Create fluid area
        self.fluid = FluidLattice(self.view_width, self.view_height)

        # Criticality tracker
        self.tracker = CriticalityTracker(self.fluid)

        # Adjustable parameters
        self.params = {
            'wave_speed': {'value': 0.45, 'min': 0.1, 'max': 1.0, 'step': 0.05},
            'damping': {'value': 0.86, 'min': 0.60, 'max': 0.98, 'step': 0.02},
            'rain_rate': {'value': 1.5, 'min': 0.1, 'max': 5.0, 'step': 0.1},
        }
        self.param_names = ['wave_speed', 'damping', 'rain_rate']
        self.selected_param = 0

        # Set initial parameters based on default target (40%)
        self._set_initial_params_for_target(self.tracker.target_coverage)

        # Preset system
        self.preset_manager = PresetManager()
        self.current_preset_name = "default"

        # Auto-tune - start ON by default
        self.auto_tune = True
        self.auto_tune_interval = 0.5  # Faster adjustment for better responsiveness
        self.last_auto_tune = 0

        # Message display
        self.message = ""
        self.message_time = 0

        self.session_time = 0.0

    def apply_params_to_fluid(self):
        self.fluid.wave_speed = self.params['wave_speed']['value']
        self.fluid.damping = self.params['damping']['value']
        self.fluid.rain_rate = self.params['rain_rate']['value']

    def _set_initial_params_for_target(self, target_pct):
        """Set initial parameters for controlled ramp-up to target.

        Instead of starting at exact equilibrium (which causes transient overshoot),
        start with CONSERVATIVE parameters and let the controller ramp up.
        - Rain at 40% of equilibrium (slower fill)
        - Damping at equilibrium (normal decay rate)
        """
        rain, damp = self.tracker.estimate_equilibrium_params(target_pct)

        # START CONSERVATIVE: 40% of equilibrium rain to prevent overshoot
        # The controller will increase rain as needed
        rain = rain * 0.4

        # Clamp to valid ranges
        rain = max(self.params['rain_rate']['min'],
                   min(self.params['rain_rate']['max'], rain))
        damp = max(self.params['damping']['min'],
                   min(self.params['damping']['max'], damp))

        self.params['rain_rate']['value'] = round(rain, 2)
        self.params['damping']['value'] = round(damp, 2)
        self.apply_params_to_fluid()

    def adjust_param(self, param_name: str, direction: int):
        param = self.params[param_name]
        new_value = param['value'] + direction * param['step']
        new_value = max(param['min'], min(param['max'], new_value))
        param['value'] = round(new_value, 3)
        self.apply_params_to_fluid()

    def load_preset(self, name: str):
        preset = self.preset_manager.get_preset(name)
        if preset:
            self.params['wave_speed']['value'] = preset['wave_speed']
            self.params['damping']['value'] = preset['damping']
            self.params['rain_rate']['value'] = preset['rain_rate']
            self.current_preset_name = name
            self.apply_params_to_fluid()
            self.show_message(f"Loaded: {name}")

    def save_current_preset(self):
        name = f"saved_{int(time.time()) % 10000}"
        self.preset_manager.save_preset(name, self.params)
        self.current_preset_name = name
        self.show_message(f"Saved: {name}")

    def show_message(self, msg: str):
        self.message = msg
        self.message_time = self.session_time

    def auto_tune_step(self):
        action, direction = self.tracker.get_adjustment(self.params)
        if action == 'drain':
            # Aggressive drain - remove 90% of energy
            # NOTE: Don't record adjustment - drain is instant, no settling needed
            self.fluid.drain_global(0.9)
            self.show_message("Auto-drain!")
        elif action and direction != 0:
            self.adjust_param(action, direction)
            self.tracker.record_adjustment()
            param_name = action.replace('_', ' ').title()
            self.show_message(f"{param_name}: {self.params[action]['value']:.2f}")

    def update(self, dt):
        self.session_time += dt
        self.fluid.update(dt)
        self.fluid.update_coverage_history()
        self.tracker.update(dt)

        if self.auto_tune:
            if self.session_time - self.last_auto_tune > self.auto_tune_interval:
                self.auto_tune_step()
                self.last_auto_tune = self.session_time

            # Auto-save preset when stable for 5+ seconds
            if self.tracker.is_stable():
                target = int(self.tracker.target_coverage)
                preset_name = f"auto_{target}pct"
                if self.current_preset_name != preset_name:
                    self.preset_manager.save_preset(preset_name, self.params)
                    self.current_preset_name = preset_name
                    self.show_message(f"Auto-saved: {preset_name}")
                    self.tracker.stable_time = 0  # Reset to avoid spam

        # Clear old messages
        if self.message and self.session_time - self.message_time > 2.0:
            self.message = ""

    def draw(self):
        self.renderer.clear_buffer()
        self._draw_fluid_view()
        self._draw_control_panel()
        self.renderer.render()

    def _draw_fluid_view(self):
        for y in range(self.view_height):
            for x in range(self.view_width):
                value = self.fluid.current[y][x]
                if abs(value) < 0.3:
                    continue
                elif abs(value) < 1.0:
                    char, color = '·', Color.BLUE
                elif abs(value) < 2.0:
                    char, color = '∘', Color.CYAN
                elif abs(value) < 4.0:
                    char, color = '○', Color.BRIGHT_CYAN
                elif abs(value) < 6.0:
                    char, color = '◎', Color.BRIGHT_WHITE
                else:
                    char, color = '●', Color.WHITE
                self.renderer.set_pixel(x, y, char, color)

    def _draw_control_panel(self):
        y = self.view_height

        # Separator
        for x in range(self.view_width):
            self.renderer.set_pixel(x, y, '═', Color.BLUE)
        y += 1

        # Row 1: Coverage bar with target marker
        coverage = self.fluid.get_coverage_percent()
        target = self.tracker.target_coverage

        self.renderer.draw_text(2, y, "COVERAGE", Color.WHITE)
        bar_start = 12
        bar_width = 50

        self.renderer.set_pixel(bar_start, y, '[', Color.WHITE)
        for i in range(bar_width):
            pct = (i / bar_width) * 100
            is_target = abs(pct - target) < 2
            is_filled = pct < coverage

            if is_target:
                char = '▼' if not is_filled else '█'
                color = Color.BRIGHT_YELLOW
            elif is_filled:
                char = '█'
                color = self.tracker.get_status_color()
            else:
                char = '░'
                color = Color.BLUE
            self.renderer.set_pixel(bar_start + 1 + i, y, char, color)

        self.renderer.set_pixel(bar_start + 1 + bar_width, y, ']', Color.WHITE)
        self.renderer.draw_text(bar_start + bar_width + 3, y,
                               f"{coverage:.0f}%", self.tracker.get_status_color())

        # Target display
        self.renderer.draw_text(bar_start + bar_width + 10, y,
                               f"Target: {target:.0f}%", Color.YELLOW)

        # Auto indicator
        if self.auto_tune:
            self.renderer.draw_text(bar_start + bar_width + 25, y, "[AUTO]", Color.BRIGHT_GREEN)

        y += 2

        # Row 2: Parameters (left) | Presets (center) | Controls (right)
        # Parameters
        self.renderer.draw_text(2, y, "PARAMETERS", Color.WHITE)
        for i, name in enumerate(self.param_names):
            param = self.params[name]
            is_sel = (i == self.selected_param)
            prefix = '>' if is_sel else ' '
            color = Color.BRIGHT_WHITE if is_sel else Color.CYAN
            label = name.replace('_', ' ').title()[:10]
            self.renderer.draw_text(2, y + 1 + i, f"{prefix}{label}: {param['value']:.2f}", color)

        # Presets
        px = 30
        self.renderer.draw_text(px, y, "PRESETS [1-4]", Color.WHITE)
        names = list(self.preset_manager.DEFAULT_PRESETS.keys())
        for i, name in enumerate(names):
            is_cur = (name == self.current_preset_name)
            color = Color.BRIGHT_GREEN if is_cur else Color.CYAN
            self.renderer.draw_text(px, y + 1 + i, f"[{i+1}] {name}", color)

        # Controls
        cx = 55
        self.renderer.draw_text(cx, y, "CONTROLS", Color.WHITE)
        self.renderer.draw_text(cx, y + 1, "Arrows: Select/Adjust", Color.CYAN)
        self.renderer.draw_text(cx, y + 2, "T: Toggle auto-tune", Color.CYAN)
        self.renderer.draw_text(cx, y + 3, "+/-: Adjust target", Color.CYAN)

        # Status/Message
        sx = 80
        self.renderer.draw_text(sx, y, "STATUS", Color.WHITE)
        self.renderer.draw_text(sx, y + 1, self.tracker.status_text, self.tracker.get_status_color())

        delta = self.fluid.get_coverage_delta()
        delta_color = Color.GREEN if abs(delta) < 3 else Color.YELLOW
        self.renderer.draw_text(sx, y + 2, f"Delta: {delta:+.1f}/s", delta_color)

        if self.message:
            self.renderer.draw_text(sx, y + 3, self.message, Color.BRIGHT_CYAN)

    def run(self):
        self.renderer.enter_fullscreen()
        self.apply_params_to_fluid()

        try:
            last_time = time.time()

            with self.term.cbreak():
                while True:
                    current_time = time.time()
                    dt = current_time - last_time
                    last_time = current_time

                    # Read key with short timeout
                    key = self.term.inkey(timeout=0.016)

                    if key:
                        # Exit
                        if key.name == 'KEY_ESCAPE' or key.lower() == 'q':
                            break

                        # Parameter selection (up/down arrows only)
                        if key.name == 'KEY_UP':
                            self.selected_param = (self.selected_param - 1) % len(self.param_names)
                        elif key.name == 'KEY_DOWN':
                            self.selected_param = (self.selected_param + 1) % len(self.param_names)

                        # Parameter adjustment (left/right arrows only)
                        elif key.name == 'KEY_LEFT':
                            self.adjust_param(self.param_names[self.selected_param], -1)
                        elif key.name == 'KEY_RIGHT':
                            self.adjust_param(self.param_names[self.selected_param], +1)

                        # Manual drain
                        elif key == ' ':
                            self.fluid.drain_global(0.8)
                            self.show_message("Drained!")

                        # Auto-tune toggle
                        elif key.lower() == 't':
                            self.auto_tune = not self.auto_tune
                            self.show_message(f"Auto-tune: {'ON' if self.auto_tune else 'OFF'}")

                        # Target adjustment
                        elif key == '+' or key == '=':
                            self.tracker.target_coverage = min(90, self.tracker.target_coverage + 5)
                            self.show_message(f"Target: {self.tracker.target_coverage:.0f}%")
                        elif key == '-' or key == '_':
                            self.tracker.target_coverage = max(10, self.tracker.target_coverage - 5)
                            self.show_message(f"Target: {self.tracker.target_coverage:.0f}%")

                        # Preset loading (1-4)
                        elif key == '1':
                            self.load_preset('default')
                        elif key == '2':
                            self.load_preset('chaotic')
                        elif key == '3':
                            self.load_preset('calm')
                        elif key == '4':
                            self.load_preset('edge')

                        # Save preset
                        elif key.lower() == 'p':
                            self.save_current_preset()

                    self.update(dt)
                    self.draw()

        finally:
            self.renderer.exit_fullscreen()


def run_flux_explorer():
    """Entry point for explorer mode."""
    game = FluxControlExplorer()
    game.run()


def run_flux_explorer_extended_demo(duration: int = 270, log_metrics: bool = False):
    """Extended demo for YouTube - shows auto-tune finding different targets in the sweet spot.

    Phases (all in NORMAL mode, varying target %):
    1. Find 40% equilibrium (0-45s)
    2. Lower to 30% - bottom of sweet spot (45-90s)
    3. Raise to 50% - top of sweet spot (90-150s)
    4. Return to 40% - middle of sweet spot (150-210s)
    5. Final exploration at 35% (210-270s)

    Args:
        duration: Total demo duration in seconds
        log_metrics: If True, collect and return metrics for evaluation
    """
    game = FluxControlExplorer()

    # Metrics collection for evaluation
    phase_metrics = {
        0: {'name': 'Find 40%', 'target': 40, 'samples': [], 'time_range': (0, 45)},
        1: {'name': 'Target 30%', 'target': 30, 'samples': [], 'time_range': (45, 90)},
        2: {'name': 'Target 50%', 'target': 50, 'samples': [], 'time_range': (90, 150)},
        3: {'name': 'Target 40%', 'target': 40, 'samples': [], 'time_range': (150, 210)},
        4: {'name': 'Target 35%', 'target': 35, 'samples': [], 'time_range': (210, 270)},
    }
    last_sample_time = 0
    sample_interval = 1.0  # Sample every second

    game.renderer.enter_fullscreen()
    game.apply_params_to_fluid()

    try:
        start_time = time.time()
        last_time = start_time
        phase = 0
        phase_start = start_time

        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            elapsed = current_time - start_time
            phase_elapsed = current_time - phase_start

            # Phase 0: Initial stabilization to 40% (0-45s)
            if phase == 0:
                if elapsed > 5 and not game.auto_tune:
                    game.auto_tune = True
                    game.show_message("Auto-tune: Finding 40%")
                if elapsed > 45:
                    phase = 1
                    phase_start = current_time
                    # Phase 1: Lower to 30% (bottom of sweet spot)
                    game.tracker.target_coverage = 30
                    game.show_message("Target: 30% (lower sweet spot)")

            # Phase 1: Target 30% (45-90s)
            elif phase == 1 and phase_elapsed > 45:
                phase = 2
                phase_start = current_time
                # Phase 2: Raise to 50% (top of sweet spot)
                game.tracker.target_coverage = 50
                game.show_message("Target: 50% (upper sweet spot)")

            # Phase 2: Target 50% (90-150s)
            elif phase == 2 and phase_elapsed > 60:
                phase = 3
                phase_start = current_time
                # Phase 3: Return to 40% (middle of sweet spot)
                game.tracker.target_coverage = 40
                game.show_message("Target: 40% (middle sweet spot)")

            # Phase 3: Target 40% (150-210s)
            elif phase == 3 and phase_elapsed > 60:
                phase = 4
                phase_start = current_time
                # Phase 4: Final exploration at 35%
                game.tracker.target_coverage = 35
                game.show_message("Target: 35% (final exploration)")

            # Phase 4: Target 35% (210-270s)
            # Just let it run with auto-tune

            # Collect metrics if enabled
            if log_metrics and elapsed - last_sample_time >= sample_interval:
                coverage = game.fluid.get_coverage_percent()
                delta = game.fluid.get_coverage_delta()
                sample = {
                    'time': elapsed,
                    'coverage': coverage,
                    'delta': delta,
                    'rain': game.params['rain_rate']['value'],
                    'damping': game.params['damping']['value'],
                }
                phase_metrics[phase]['samples'].append(sample)
                last_sample_time = elapsed

            game.update(dt)
            game.draw()
            time.sleep(0.05)  # 20 FPS for VHS compatibility

    finally:
        game.renderer.exit_fullscreen()

    # Return metrics for evaluation if requested
    if log_metrics:
        return phase_metrics
    return None


def evaluate_demo_metrics(metrics: dict) -> dict:
    """Analyze demo metrics and generate performance report.

    Args:
        metrics: Dictionary of phase metrics from run_flux_explorer_extended_demo

    Returns:
        Evaluation report with grades for each phase
    """
    report = {
        'phases': [],
        'overall_score': 0,
        'summary': ''
    }

    total_score = 0
    phase_count = 0

    for phase_id, phase_data in metrics.items():
        if not phase_data['samples']:
            continue

        phase_count += 1
        target = phase_data['target']
        coverages = [s['coverage'] for s in phase_data['samples']]

        # Calculate statistics
        avg_coverage = sum(coverages) / len(coverages)
        min_coverage = min(coverages)
        max_coverage = max(coverages)
        avg_error = sum(abs(c - target) for c in coverages) / len(coverages)

        # Time in sweet spot (30-50%)
        in_sweet_spot = sum(1 for c in coverages if 30 <= c <= 50)
        sweet_spot_pct = (in_sweet_spot / len(coverages)) * 100

        # Time within 10% of target
        on_target = sum(1 for c in coverages if abs(c - target) <= 10)
        on_target_pct = (on_target / len(coverages)) * 100

        # Score: 100 - avg_error (clamped 0-100)
        phase_score = max(0, min(100, 100 - avg_error * 2))
        total_score += phase_score

        # Grade
        if phase_score >= 90:
            grade = 'A'
        elif phase_score >= 80:
            grade = 'B'
        elif phase_score >= 70:
            grade = 'C'
        elif phase_score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        phase_report = {
            'name': phase_data['name'],
            'target': target,
            'avg_coverage': avg_coverage,
            'min_coverage': min_coverage,
            'max_coverage': max_coverage,
            'avg_error': avg_error,
            'sweet_spot_pct': sweet_spot_pct,
            'on_target_pct': on_target_pct,
            'samples': len(coverages),
            'score': phase_score,
            'grade': grade,
        }
        report['phases'].append(phase_report)

    if phase_count > 0:
        report['overall_score'] = total_score / phase_count

    # Generate summary
    if report['overall_score'] >= 80:
        report['summary'] = "Excellent! Controller maintained target coverage well."
    elif report['overall_score'] >= 60:
        report['summary'] = "Good performance with some oscillation."
    else:
        report['summary'] = "Needs tuning - significant deviation from targets."

    return report


def print_demo_report(report: dict):
    """Pretty-print the demo evaluation report."""
    print("=" * 70)
    print("FLUX CONTROL EXPLORER - DEMO EVALUATION REPORT")
    print("=" * 70)
    print()

    for phase in report['phases']:
        print(f"Phase: {phase['name']}")
        print(f"  Target: {phase['target']}%")
        print(f"  Actual: {phase['avg_coverage']:.1f}% avg (range: {phase['min_coverage']:.1f}-{phase['max_coverage']:.1f}%)")
        print(f"  Error:  {phase['avg_error']:.1f}% avg deviation")
        print(f"  Sweet Spot (30-50%): {phase['sweet_spot_pct']:.0f}% of time")
        print(f"  On Target (±10%):    {phase['on_target_pct']:.0f}% of time")
        print(f"  Score: {phase['score']:.0f}/100 ({phase['grade']})")
        print()

    print("-" * 70)
    print(f"OVERALL SCORE: {report['overall_score']:.0f}/100")
    print(f"SUMMARY: {report['summary']}")
    print("=" * 70)


def run_demo_evaluation(duration: int = 270, verbose: bool = True):
    """Headless simulation of extended demo to evaluate performance.

    Same logic as run_flux_explorer_extended_demo but without rendering.
    Collects metrics and prints evaluation report.
    """
    from .flux_control_zen import FluidLattice

    # Create simulation components (smaller for speed)
    fluid = FluidLattice(80, 40)
    tracker = CriticalityTracker(fluid)
    tracker.target_coverage = 40.0

    params = {
        'wave_speed': {'value': 0.45, 'min': 0.1, 'max': 1.0, 'step': 0.05},
        'damping': {'value': 0.79, 'min': 0.60, 'max': 0.98, 'step': 0.02},
        'rain_rate': {'value': 0.53, 'min': 0.1, 'max': 5.0, 'step': 0.1},
    }

    def apply_params():
        fluid.wave_speed = params['wave_speed']['value']
        fluid.damping = params['damping']['value']
        fluid.rain_rate = params['rain_rate']['value']

    def adjust_param(name, direction):
        p = params[name]
        new_val = p['value'] + direction * p['step']
        p['value'] = round(max(p['min'], min(p['max'], new_val)), 3)
        apply_params()
        tracker.record_adjustment()

    # Initialize with conservative params
    ideal_rain, ideal_damp = tracker.estimate_equilibrium_params(40, "normal")
    params['rain_rate']['value'] = round(ideal_rain * 0.4, 2)
    params['damping']['value'] = round(ideal_damp, 2)
    apply_params()

    # Metrics collection - phases now stay in NORMAL mode, only target changes
    phase_metrics = {
        0: {'name': 'Find 40%', 'target': 40, 'samples': []},
        1: {'name': 'Target 30%', 'target': 30, 'samples': []},
        2: {'name': 'Target 50%', 'target': 50, 'samples': []},
        3: {'name': 'Target 40%', 'target': 40, 'samples': []},
        4: {'name': 'Target 35%', 'target': 35, 'samples': []},
    }

    dt = 0.033
    elapsed = 0.0
    phase = 0
    phase_start = 0.0
    last_tune = 0.0
    last_sample = 0.0
    tune_interval = 0.5
    sample_interval = 1.0
    auto_tune = False

    if verbose:
        print(f"Running headless evaluation for {duration}s...")
        print()

    while elapsed < duration:
        phase_elapsed = elapsed - phase_start

        # Phase transitions - STAY IN NORMAL MODE, just change targets
        # This demonstrates auto-tune finding different equilibrium points
        if phase == 0:
            if elapsed > 5 and not auto_tune:
                auto_tune = True
            if elapsed > 45:
                phase = 1
                phase_start = elapsed
                # Phase 1: Lower target to 30% (lower end of sweet spot)
                tracker.target_coverage = 30
                if verbose:
                    print(f"  t={elapsed:.0f}s: Target changed to 30%")

        elif phase == 1 and phase_elapsed > 45:
            phase = 2
            phase_start = elapsed
            # Phase 2: Raise target to 50% (upper end of sweet spot)
            tracker.target_coverage = 50
            if verbose:
                print(f"  t={elapsed:.0f}s: Target changed to 50%")

        elif phase == 2 and phase_elapsed > 60:
            phase = 3
            phase_start = elapsed
            # Phase 3: Return to 40% (middle of sweet spot)
            tracker.target_coverage = 40
            if verbose:
                print(f"  t={elapsed:.0f}s: Target changed to 40%")

        elif phase == 3 and phase_elapsed > 60:
            phase = 4
            phase_start = elapsed
            # Phase 4: Try 35% for final exploration
            tracker.target_coverage = 35
            if verbose:
                print(f"  t={elapsed:.0f}s: Target changed to 35%")

        # Update simulation
        fluid.update(dt)
        fluid.update_coverage_history()
        tracker.update(dt)

        # Auto-tune
        if auto_tune and elapsed - last_tune > tune_interval:
            action, direction = tracker.get_adjustment(params)
            if action == 'drain':
                fluid.drain_global(0.9)
            elif action and direction != 0:
                adjust_param(action, direction)
            last_tune = elapsed

        # Sample metrics
        if elapsed - last_sample >= sample_interval:
            coverage = fluid.get_coverage_percent()
            phase_metrics[phase]['samples'].append({
                'time': elapsed,
                'coverage': coverage,
                'delta': fluid.get_coverage_delta(),
                'rain': params['rain_rate']['value'],
                'damping': params['damping']['value'],
            })
            last_sample = elapsed

        elapsed += dt

    if verbose:
        print()

    # Evaluate and print report
    report = evaluate_demo_metrics(phase_metrics)
    print_demo_report(report)

    return report


def run_flux_explorer_demo(duration: int = 270):
    """Auto-demo - shows auto-tune finding different coverage targets.

    YouTube demo phases (all in NORMAL mode):
    - 0-5s: Initialize, target 40%
    - 5-45s: Enable auto-tune, find 40% equilibrium
    - 45-90s: Target 30% (lower sweet spot)
    - 90-150s: Target 50% (upper sweet spot)
    - 150-210s: Target 40% (return to middle)
    - 210-270s: Target 35% (final exploration)
    """
    game = FluxControlExplorer()
    game.renderer.enter_fullscreen()
    game.apply_params_to_fluid()

    try:
        start_time = time.time()
        last_time = start_time
        phase = 0
        phase_start = start_time

        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            elapsed = current_time - start_time
            phase_elapsed = current_time - phase_start

            # Phase 0: Enable auto-tune at 5s
            if phase == 0 and elapsed > 5:
                game.auto_tune = True
                game.show_message("Auto-tune ON - Finding 40%")
                phase = 1
                phase_start = current_time

            # Phase 1: At 45s total, switch to 30% target
            elif phase == 1 and elapsed > 45:
                game.tracker.target_coverage = 30
                game.show_message("Target: 30% (lower sweet spot)")
                phase = 2
                phase_start = current_time

            # Phase 2: At 90s total, switch to 50% target
            elif phase == 2 and elapsed > 90:
                game.tracker.target_coverage = 50
                game.show_message("Target: 50% (upper sweet spot)")
                phase = 3
                phase_start = current_time

            # Phase 3: At 150s total, return to 40%
            elif phase == 3 and elapsed > 150:
                game.tracker.target_coverage = 40
                game.show_message("Target: 40% (middle sweet spot)")
                phase = 4
                phase_start = current_time

            # Phase 4: At 210s total, try 35%
            elif phase == 4 and elapsed > 210:
                game.tracker.target_coverage = 35
                game.show_message("Target: 35% (final exploration)")
                phase = 5
                phase_start = current_time

            game.update(dt)
            game.draw()
            time.sleep(0.05)  # 20 FPS for VHS compatibility

    finally:
        game.renderer.exit_fullscreen()


def run_simulation(target: int = 40, duration: int = 60, verbose: bool = True):
    """Headless simulation to test auto-tune algorithm.

    Runs without rendering, prints progress every 5 seconds.
    Returns final parameters if target was reached.
    """
    from .flux_control_zen import FluidLattice

    # Create minimal simulation (smaller for speed)
    fluid = FluidLattice(80, 40)
    tracker = CriticalityTracker(fluid)
    tracker.target_coverage = float(target)

    params = {
        'wave_speed': {'value': 0.45, 'min': 0.1, 'max': 1.0, 'step': 0.05},
        'damping': {'value': 0.86, 'min': 0.60, 'max': 0.98, 'step': 0.02},
        'rain_rate': {'value': 1.5, 'min': 0.1, 'max': 5.0, 'step': 0.1},
    }

    def apply_params():
        fluid.wave_speed = params['wave_speed']['value']
        fluid.damping = params['damping']['value']
        fluid.rain_rate = params['rain_rate']['value']

    def adjust_param(name, direction):
        p = params[name]
        new_val = p['value'] + direction * p['step']
        p['value'] = round(max(p['min'], min(p['max'], new_val)), 3)
        apply_params()
        tracker.record_adjustment()  # Track settling time

    # START CONSERVATIVE: Use 40% of equilibrium rain to prevent overshoot
    # The controller will increase rain as coverage stays below target
    ideal_rain, ideal_damp = tracker.estimate_equilibrium_params(target, "normal")
    params['rain_rate']['value'] = round(ideal_rain * 0.4, 2)  # 40% of equilibrium
    params['damping']['value'] = round(ideal_damp, 2)
    apply_params()

    dt = 0.033  # ~30 fps simulation
    elapsed = 0.0
    last_report = 0.0
    last_tune = 0.0
    tune_interval = 0.5  # Check every 0.5s (but settling prevents rapid changes)

    best_diff = 100
    best_params = None

    if verbose:
        print(f"Simulation: target={target}%, duration={duration}s")
        print(f"Initial (estimated): rain={params['rain_rate']['value']:.2f}, damp={params['damping']['value']:.2f}")
        print("-" * 60)

    while elapsed < duration:
        # Update fluid
        fluid.update(dt)
        fluid.update_coverage_history()
        tracker.update(dt)  # This tracks settling time

        coverage = fluid.get_coverage_percent()
        diff = abs(coverage - target)

        # Track best
        if diff < best_diff:
            best_diff = diff
            best_params = {
                'rain_rate': params['rain_rate']['value'],
                'damping': params['damping']['value'],
                'wave_speed': params['wave_speed']['value'],
                'coverage': coverage,
            }

        # Auto-tune (respects settling time via tracker.is_settling)
        if elapsed - last_tune > tune_interval:
            action, direction = tracker.get_adjustment(params)
            if action == 'drain':
                # Drain is instant - no settling needed, can drain again immediately
                fluid.drain_global(0.9)
            elif action and direction != 0:
                adjust_param(action, direction)
            last_tune = elapsed

        # Report
        if verbose and elapsed - last_report >= 5.0:
            delta = fluid.get_coverage_delta()
            accel = tracker.get_acceleration()
            settling = "settling" if tracker.is_settling else "ready"
            print(f"t={elapsed:5.1f}s | cov={coverage:5.1f}% | target={target}% | "
                  f"rain={params['rain_rate']['value']:.2f} | damp={params['damping']['value']:.2f} | "
                  f"delta={delta:+.1f} | accel={accel:+.1f} | {settling}")
            last_report = elapsed

        elapsed += dt

    if verbose:
        print("-" * 60)
        print(f"BEST: diff={best_diff:.1f}% at rain={best_params['rain_rate']:.2f}, "
              f"damp={best_params['damping']:.2f}, cov={best_params['coverage']:.1f}%")

        if best_diff < 5:
            print("SUCCESS: Reached target!")
        else:
            print(f"FAILED: Best was {best_diff:.1f}% off target")

    return best_params


def run_multi_simulation():
    """Run simulations for multiple targets to find parameter mappings."""
    print("=" * 60)
    print("FLUX CONTROL PARAMETER DISCOVERY")
    print("=" * 60)

    results = {}
    for target in [20, 30, 40, 50, 60, 70]:
        print(f"\n>>> Testing target: {target}%")
        result = run_simulation(target=target, duration=45, verbose=True)
        results[target] = result
        print()

    print("\n" + "=" * 60)
    print("SUMMARY: Parameter mappings for each target")
    print("=" * 60)
    for target, params in results.items():
        print(f"  {target}%: rain={params['rain_rate']:.2f}, damp={params['damping']:.2f} "
              f"-> actual {params['coverage']:.1f}%")

    return results


def run_parameter_capture(duration: int = 600):
    """Long-running session to capture stable parameters.

    Logs parameters every 10 seconds and saves successful presets.
    Duration: 600s = 10 minutes by default.

    Output files:
    - /tmp/flux_capture.log - Raw parameter log
    - /tmp/flux_presets_captured.json - Stable presets found
    """
    import json

    game = FluxControlExplorer()
    game.renderer.enter_fullscreen()
    game.apply_params_to_fluid()

    log_file = open('/tmp/flux_capture.log', 'w')
    presets_found = []

    try:
        start_time = time.time()
        last_time = start_time
        last_log = 0
        last_preset_check = 0

        # Start with auto-tune enabled
        game.auto_tune = True
        game.tracker.target_coverage = 40

        print(f"Starting {duration}s parameter capture session...")
        print("Output: /tmp/flux_capture.log, /tmp/flux_presets_captured.json")

        while time.time() - start_time < duration:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            elapsed = current_time - start_time

            # Log every 10 seconds
            if elapsed - last_log >= 10:
                coverage = game.fluid.get_coverage_percent()
                delta = game.fluid.get_coverage_delta()
                params = {
                    'time': round(elapsed, 1),
                    'coverage': round(coverage, 1),
                    'delta': round(delta, 2),
                    'wave_speed': game.params['wave_speed']['value'],
                    'damping': game.params['damping']['value'],
                    'rain_rate': game.params['rain_rate']['value'],
                }
                log_file.write(f"{params}\n")
                log_file.flush()
                last_log = elapsed

            # Check for stable preset every 30 seconds
            if elapsed - last_preset_check >= 30:
                coverage = game.fluid.get_coverage_percent()
                delta = abs(game.fluid.get_coverage_delta())

                # If stable (coverage 30-50%, low delta), save preset
                if 30 <= coverage <= 50 and delta < 2.0:
                    preset = {
                        'name': f'stable_{int(elapsed)}s',
                        'wave_speed': game.params['wave_speed']['value'],
                        'damping': game.params['damping']['value'],
                        'rain_rate': game.params['rain_rate']['value'],
                        'target_coverage': round(coverage, 1),
                    }
                    presets_found.append(preset)
                    game.show_message(f"Preset saved: {coverage:.0f}%")

                last_preset_check = elapsed

            # Run simulation
            game.update(dt)
            game.draw()
            time.sleep(0.05)  # 20 FPS for VHS compatibility

    finally:
        log_file.close()
        game.renderer.exit_fullscreen()

        # Print all captured presets
        print("\n" + "=" * 50)
        print("CAPTURED PRESETS")
        print("=" * 50)
        for p in presets_found:
            print(f"  {p['name']}: wave={p['wave_speed']}, damp={p['damping']}, "
                  f"rain={p['rain_rate']}, cov={p['target_coverage']}%")

        # Save to JSON
        with open('/tmp/flux_presets_captured.json', 'w') as f:
            json.dump(presets_found, f, indent=2)
        print(f"\nSaved {len(presets_found)} presets to /tmp/flux_presets_captured.json")

        # Also print the log file location
        print(f"Full log: /tmp/flux_capture.log")


def run_trajectory_analysis(target: int = 40, duration: int = 120, log_interval: float = 0.5):
    """Analyze trajectory when converging to a target percentage.

    Measures:
    - Time to reach target (within 5%)
    - Time to stabilize (within 2% for 5 seconds)
    - Maximum overshoot/undershoot
    - Number of oscillations around target
    - Final parameters at equilibrium

    Returns dict with all metrics.
    """
    from .flux_control_zen import FluidLattice

    fluid = FluidLattice(80, 40)
    tracker = CriticalityTracker(fluid)
    tracker.target_coverage = float(target)

    params = {
        'wave_speed': {'value': 0.45, 'min': 0.1, 'max': 1.0, 'step': 0.05},
        'damping': {'value': 0.86, 'min': 0.60, 'max': 0.98, 'step': 0.02},
        'rain_rate': {'value': 1.5, 'min': 0.1, 'max': 5.0, 'step': 0.1},
    }

    def apply_params():
        fluid.wave_speed = params['wave_speed']['value']
        fluid.damping = params['damping']['value']
        fluid.rain_rate = params['rain_rate']['value']

    def adjust_param(name, direction):
        p = params[name]
        new_val = p['value'] + direction * p['step']
        p['value'] = round(max(p['min'], min(p['max'], new_val)), 3)
        apply_params()
        tracker.record_adjustment()

    # Start conservative
    ideal_rain, ideal_damp = tracker.estimate_equilibrium_params(target, "normal")
    params['rain_rate']['value'] = round(ideal_rain * 0.4, 2)
    params['damping']['value'] = round(ideal_damp, 2)
    apply_params()

    dt = 0.033
    elapsed = 0.0
    last_tune = 0.0
    last_log = 0.0
    tune_interval = 0.5

    # Trajectory metrics
    coverage_history = []
    time_to_reach = None  # First time within 5% of target
    time_to_stable = None  # First time stable for 5s within 2%
    max_overshoot = 0.0
    max_undershoot = 0.0
    oscillation_count = 0
    last_direction = None  # Track direction changes
    stable_start = None

    while elapsed < duration:
        fluid.update(dt)
        fluid.update_coverage_history()
        tracker.update(dt)
        coverage = fluid.get_coverage_percent()

        # Log coverage at intervals
        if elapsed - last_log >= log_interval:
            coverage_history.append({'time': elapsed, 'coverage': coverage})
            last_log = elapsed

        diff = coverage - target

        # Track time to reach target (first time within 5%)
        if time_to_reach is None and abs(diff) < 5:
            time_to_reach = elapsed

        # Track stability (within 2% for 5 seconds)
        if abs(diff) < 2:
            if stable_start is None:
                stable_start = elapsed
            elif elapsed - stable_start >= 5.0 and time_to_stable is None:
                time_to_stable = stable_start
        else:
            stable_start = None

        # Track overshoot/undershoot
        if diff > 0:
            max_overshoot = max(max_overshoot, diff)
        else:
            max_undershoot = min(max_undershoot, diff)

        # Count oscillations (direction changes around target)
        if abs(diff) < 10:
            direction = 1 if diff > 0 else -1
            if last_direction is not None and direction != last_direction:
                oscillation_count += 1
            last_direction = direction

        # Auto-tune
        if elapsed - last_tune > tune_interval:
            action, direction = tracker.get_adjustment(params)
            if action == 'drain':
                fluid.drain_global(0.9)
            elif action and direction != 0:
                adjust_param(action, direction)
            last_tune = elapsed

        elapsed += dt

    # Final metrics
    final_coverage = fluid.get_coverage_percent()
    return {
        'target': target,
        'time_to_reach': time_to_reach,
        'time_to_stable': time_to_stable,
        'max_overshoot': max_overshoot,
        'max_undershoot': abs(max_undershoot),
        'oscillations': oscillation_count // 2,  # Each full oscillation = 2 direction changes
        'final_coverage': final_coverage,
        'final_diff': abs(final_coverage - target),
        'final_params': {
            'rain_rate': params['rain_rate']['value'],
            'damping': params['damping']['value'],
            'wave_speed': params['wave_speed']['value'],
        },
        'coverage_history': coverage_history,
    }


def run_parameter_optimization(duration_per_target: int = 90):
    """Run comprehensive parameter optimization across multiple targets.

    Tests targets from 25% to 60% in 5% increments.
    Outputs optimal defaults for gameplay based on:
    - Fastest convergence
    - Lowest oscillation
    - Best stability

    Results saved to /tmp/flux_optimization_results.json
    """
    import json
    import statistics

    targets = [25, 30, 35, 40, 45, 50, 55, 60]
    results = {}

    print("=" * 70)
    print("FLUX CONTROL PARAMETER OPTIMIZATION")
    print("=" * 70)
    print(f"Testing {len(targets)} targets, {duration_per_target}s each")
    print(f"Total estimated time: {len(targets) * duration_per_target / 60:.1f} minutes")
    print("-" * 70)

    for target in targets:
        print(f"\n>>> Target: {target}%")
        result = run_trajectory_analysis(target=target, duration=duration_per_target)
        results[target] = result

        # Print summary for this target
        reach = f"{result['time_to_reach']:.1f}s" if result['time_to_reach'] else "NEVER"
        stable = f"{result['time_to_stable']:.1f}s" if result['time_to_stable'] else "NEVER"
        print(f"    Reach target: {reach}")
        print(f"    Stabilize: {stable}")
        print(f"    Overshoot: +{result['max_overshoot']:.1f}%")
        print(f"    Undershoot: -{result['max_undershoot']:.1f}%")
        print(f"    Oscillations: {result['oscillations']}")
        print(f"    Final: {result['final_coverage']:.1f}% (diff={result['final_diff']:.1f}%)")
        print(f"    Params: rain={result['final_params']['rain_rate']:.2f}, "
              f"damp={result['final_params']['damping']:.2f}")

    # Analyze results
    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS")
    print("=" * 70)

    # Find sweet spot targets (those that stabilized)
    stable_targets = [t for t, r in results.items() if r['time_to_stable'] is not None]
    if stable_targets:
        print(f"\nStable targets: {stable_targets}")

        # Best convergence time
        best_convergence = min(stable_targets, key=lambda t: results[t]['time_to_reach'] or 999)
        print(f"Fastest convergence: {best_convergence}% "
              f"(reached in {results[best_convergence]['time_to_reach']:.1f}s)")

        # Lowest oscillation
        best_smooth = min(stable_targets, key=lambda t: results[t]['oscillations'])
        print(f"Smoothest (fewest oscillations): {best_smooth}% "
              f"({results[best_smooth]['oscillations']} oscillations)")

        # Lowest overshoot
        best_overshoot = min(stable_targets, key=lambda t: results[t]['max_overshoot'])
        print(f"Lowest overshoot: {best_overshoot}% "
              f"(+{results[best_overshoot]['max_overshoot']:.1f}%)")

        # Calculate score for each target
        print("\n--- GAMEPLAY SCORE (lower = better) ---")
        scores = {}
        for t in stable_targets:
            r = results[t]
            # Weight: convergence time (30%), oscillations (30%), overshoot (20%), stability (20%)
            reach_score = (r['time_to_reach'] or 999) / duration_per_target
            stab_score = (r['time_to_stable'] or 999) / duration_per_target
            osc_score = r['oscillations'] / 10  # Normalize
            over_score = r['max_overshoot'] / 20  # Normalize

            score = (reach_score * 0.30 + osc_score * 0.30 +
                     over_score * 0.20 + stab_score * 0.20)
            scores[t] = round(score, 3)
            print(f"  {t}%: score={scores[t]:.3f}")

        best_overall = min(scores, key=scores.get)
        print(f"\n*** RECOMMENDED DEFAULT TARGET: {best_overall}% ***")
        best_params = results[best_overall]['final_params']
        print(f"    Suggested defaults:")
        print(f"      wave_speed = {best_params['wave_speed']}")
        print(f"      damping = {best_params['damping']}")
        print(f"      rain_rate = {best_params['rain_rate']}")
    else:
        print("\nWARNING: No targets achieved stability. Try longer duration.")

    # Save results
    output_file = '/tmp/flux_optimization_results.json'
    # Convert coverage_history to prevent JSON issues
    save_results = {}
    for t, r in results.items():
        save_results[str(t)] = {
            k: v for k, v in r.items()
            if k != 'coverage_history'  # Exclude large history
        }
        save_results[str(t)]['sample_history'] = r['coverage_history'][::10]  # Every 10th point

    with open(output_file, 'w') as f:
        json.dump(save_results, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")

    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "sim":
            run_multi_simulation()
        elif sys.argv[1] == "optimize":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 90
            run_parameter_optimization(duration)
        elif sys.argv[1] == "trajectory":
            target = int(sys.argv[2]) if len(sys.argv) > 2 else 40
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 120
            result = run_trajectory_analysis(target, duration)
            print(f"Target: {target}%")
            print(f"Time to reach: {result['time_to_reach']}")
            print(f"Time to stable: {result['time_to_stable']}")
            print(f"Overshoot: +{result['max_overshoot']:.1f}%")
            print(f"Oscillations: {result['oscillations']}")
    else:
        run_flux_explorer()
