"""
Panda Interaction Behavior System

AI behavior system for panda interacting with Qt widgets.
Handles detection, decision-making, animation, and programmatic widget interaction.

Features:
    - Autonomous behavior decisions
    - Widget-specific interaction animations
    - Programmatic widget clicking
    - Animation coordination with timing
    - Mischievous personality behaviors
"""

import logging

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtCore import QTimer, QPoint
    from PyQt6.QtWidgets import QPushButton, QSlider, QTabBar, QComboBox, QCheckBox
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False

import random
import math
from enum import Enum


class InteractionBehavior(Enum):
    """Types of interactions panda can perform."""
    BITE_BUTTON = "bite_button"
    JUMP_ON_BUTTON = "jump_on_button"
    TAP_SLIDER = "tap_slider"
    BITE_TAB = "bite_tab"
    PUSH_CHECKBOX = "push_checkbox"
    SPIN_COMBOBOX = "spin_combobox"
    MISCHIEVOUS_LOOK = "mischievous_look"
    WALK_AROUND = "walk_around"


class PandaInteractionBehavior:
    """
    AI system for panda widget interaction.
    
    This system:
    - Detects nearby widgets
    - Decides what interaction to perform
    - Animates panda accordingly
    - Triggers widget actions programmatically
    - Manages behavior timing and cooldowns
    """
    
    def __init__(self, panda_overlay, widget_detector):
        """
        Initialize interaction behavior system.
        
        Args:
            panda_overlay: TransparentPandaOverlay instance
            widget_detector: WidgetDetector instance
        """
        if not PYQT_AVAILABLE:
            logger.warning("PandaInteractionBehavior: PyQt6 not available; interactions disabled")
            self.overlay = panda_overlay
            self.detector = widget_detector
            return
        
        self.overlay = panda_overlay
        self.detector = widget_detector
        
        # Current state
        self.current_behavior = None
        self.target_widget = None
        self.behavior_timer = 0.0
        self.behavior_duration = 0.0
        
        # AI parameters
        self.interaction_cooldown = 0.0
        self.interaction_cooldown_max = 5.0  # Seconds between interactions
        self.detection_radius = 200  # Pixels
        
        # Animation states
        self.is_moving_to_widget = False
        self.is_performing_action = False
        self.target_position = None
        
        # Personality
        self.mischievousness = 0.7  # 0.0-1.0, how likely to interact
        self.playfulness = 0.8  # 0.0-1.0, animation exaggeration
        
        # Movement
        self.move_speed = 100.0  # Pixels per second
        
    def update(self, delta_time):
        """
        Update behavior AI every frame.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update cooldown
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= delta_time
        
        # Update current behavior timer
        if self.behavior_timer > 0:
            self.behavior_timer -= delta_time
            
            # Check if behavior finished
            if self.behavior_timer <= 0:
                self._finish_current_behavior()
                return
        
        # If not currently doing anything and cooldown expired
        if not self.current_behavior and self.interaction_cooldown <= 0:
            # Decide whether to interact
            if random.random() < self.mischievousness * delta_time:
                self._choose_and_start_interaction()
        
        # Update movement if moving to widget
        if self.is_moving_to_widget and self.target_position:
            self._update_movement(delta_time)
    
    def _choose_and_start_interaction(self):
        """Choose a widget and start an interaction."""
        # Find nearby widgets
        nearby_widgets = self._find_nearby_widgets()
        
        if not nearby_widgets:
            return
        
        # Pick a random widget
        self.target_widget = random.choice(nearby_widgets)
        
        # Determine interaction type based on widget
        behavior = self._choose_behavior_for_widget(self.target_widget)
        
        if behavior:
            self._start_behavior(behavior)
    
    def _find_nearby_widgets(self):
        """
        Find widgets near panda's current position.
        
        Returns:
            List of nearby widgets
        """
        # Get panda's screen position
        head_pos = self.overlay.get_head_position()
        
        if not head_pos:
            return []
        
        # Get all widgets
        all_widgets = self.detector.get_all_widgets()
        
        # Filter by distance
        nearby = []
        for widget in all_widgets:
            center = self.detector.get_widget_center(widget)
            if not center:
                continue
            
            # Calculate distance
            dx = center.x() - head_pos.x()
            dy = center.y() - head_pos.y()
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance <= self.detection_radius:
                nearby.append(widget)
        
        return nearby
    
    def _choose_behavior_for_widget(self, widget):
        """
        Choose appropriate behavior for widget type.
        
        Args:
            widget: The target widget
            
        Returns:
            InteractionBehavior or None
        """
        if isinstance(widget, QPushButton):
            # Random choice between bite and jump
            return random.choice([
                InteractionBehavior.BITE_BUTTON,
                InteractionBehavior.JUMP_ON_BUTTON
            ])
        
        elif isinstance(widget, QSlider):
            return InteractionBehavior.TAP_SLIDER
        
        elif isinstance(widget, QTabBar):
            return InteractionBehavior.BITE_TAB
        
        elif isinstance(widget, QCheckBox):
            return InteractionBehavior.PUSH_CHECKBOX
        
        elif isinstance(widget, QComboBox):
            return InteractionBehavior.SPIN_COMBOBOX
        
        else:
            # Unknown widget, just look at it
            return InteractionBehavior.MISCHIEVOUS_LOOK
    
    def _start_behavior(self, behavior):
        """
        Start performing a behavior.
        
        Args:
            behavior: InteractionBehavior to perform
        """
        self.current_behavior = behavior
        
        # Get target position
        widget_center = self.detector.get_widget_center(self.target_widget)
        if not widget_center:
            return
        
        self.target_position = widget_center
        
        # Start moving to widget
        self.is_moving_to_widget = True
        
        logger.info(f"Panda starting behavior: {behavior.value} on {self.target_widget.__class__.__name__}")
    
    def _update_movement(self, delta_time):
        """
        Update panda movement toward target.
        
        Args:
            delta_time: Time since last update
        """
        if not self.target_position:
            return
        
        # Get current position
        head_pos = self.overlay.get_head_position()
        if not head_pos:
            return
        
        # Calculate direction
        dx = self.target_position.x() - head_pos.x()
        dy = self.target_position.y() - head_pos.y()
        distance = (dx * dx + dy * dy) ** 0.5
        
        # Check if reached
        if distance < 10:
            self.is_moving_to_widget = False
            self._execute_interaction()
            return
        
        # Move toward target
        if distance > 0:
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Move panda (this is simplified, real implementation would update overlay position)
            move_amount = self.move_speed * delta_time
            
            # Update panda animation to walking
            self.overlay.set_animation_state('walking')
    
    def _execute_interaction(self):
        """Execute the actual interaction with the widget."""
        if not self.current_behavior or not self.target_widget:
            return
        
        behavior = self.current_behavior
        
        # Perform animation and action based on behavior
        if behavior == InteractionBehavior.BITE_BUTTON:
            self._animate_bite()
            self._trigger_widget_click_delayed(self.target_widget, 0.5)
            self.behavior_duration = 1.0
        
        elif behavior == InteractionBehavior.JUMP_ON_BUTTON:
            self._animate_jump()
            self._trigger_widget_click_delayed(self.target_widget, 0.3)
            self.behavior_duration = 0.8
        
        elif behavior == InteractionBehavior.TAP_SLIDER:
            self._animate_tap()
            self._trigger_slider_change_delayed(self.target_widget, 0.4)
            self.behavior_duration = 0.8
        
        elif behavior == InteractionBehavior.BITE_TAB:
            self._animate_bite()
            self._trigger_widget_click_delayed(self.target_widget, 0.5)
            self.behavior_duration = 1.0
        
        elif behavior == InteractionBehavior.PUSH_CHECKBOX:
            self._animate_push()
            self._trigger_widget_click_delayed(self.target_widget, 0.3)
            self.behavior_duration = 0.6
        
        elif behavior == InteractionBehavior.SPIN_COMBOBOX:
            self._animate_spin()
            self._trigger_combobox_open_delayed(self.target_widget, 0.4)
            self.behavior_duration = 0.8
        
        elif behavior == InteractionBehavior.MISCHIEVOUS_LOOK:
            self._animate_look()
            self.behavior_duration = 2.0
        
        # Set behavior timer
        self.behavior_timer = self.behavior_duration
        self.is_performing_action = True
    
    def _animate_bite(self):
        """Animate panda biting."""
        logger.debug("Panda biting!")
        self.overlay.set_animation_state('biting')
        # Open mouth wide animation would be implemented in overlay
    
    def _animate_jump(self):
        """Animate panda jumping."""
        logger.debug("Panda jumping!")
        self.overlay.set_animation_state('jumping')
        # Jump animation
    
    def _animate_tap(self):
        """Animate panda tapping."""
        logger.debug("Panda tapping!")
        self.overlay.set_animation_state('tapping')
        # Tap animation with paw
    
    def _animate_push(self):
        """Animate panda pushing."""
        logger.debug("Panda pushing!")
        self.overlay.set_animation_state('pushing')
        # Push animation
    
    def _animate_spin(self):
        """Animate panda spinning around."""
        logger.debug("Panda spinning!")
        self.overlay.set_animation_state('spinning')
        # Spin animation
    
    def _animate_look(self):
        """Animate panda looking mischievously."""
        logger.debug("Panda looking mischievous!")
        self.overlay.set_animation_state('mischievous')
        # Mischievous expression
    
    def _trigger_widget_click_delayed(self, widget, delay):
        """
        Trigger widget click after a delay (for animation).
        
        Args:
            widget: Widget to click
            delay: Delay in seconds
        """
        def do_click():
            if widget and hasattr(widget, 'click'):
                logger.debug(f"Triggering click on {widget.__class__.__name__}")
                widget.click()
                
                # Apply squash effect
                self.overlay.apply_squash_effect(0.8)
                QTimer.singleShot(100, lambda: self.overlay.apply_squash_effect(1.0))
        
        # Schedule click
        QTimer.singleShot(int(delay * 1000), do_click)
    
    def _trigger_slider_change_delayed(self, slider, delay):
        """
        Trigger slider value change after delay.
        
        Args:
            slider: QSlider to change
            delay: Delay in seconds
        """
        def do_change():
            if slider and isinstance(slider, QSlider):
                # Change to random value
                current = slider.value()
                min_val = slider.minimum()
                max_val = slider.maximum()
                
                # Move slider slightly
                new_value = random.randint(min_val, max_val)
                logger.debug(f"Changing slider from {current} to {new_value}")
                slider.setValue(new_value)
                
                # Apply squash effect
                self.overlay.apply_squash_effect(0.9)
                QTimer.singleShot(100, lambda: self.overlay.apply_squash_effect(1.0))
        
        QTimer.singleShot(int(delay * 1000), do_change)
    
    def _trigger_combobox_open_delayed(self, combobox, delay):
        """
        Trigger combobox opening after delay.
        
        Args:
            combobox: QComboBox to open
            delay: Delay in seconds
        """
        def do_open():
            if combobox and isinstance(combobox, QComboBox):
                logger.debug("Opening combobox")
                combobox.showPopup()
        
        QTimer.singleShot(int(delay * 1000), do_open)
    
    def _finish_current_behavior(self):
        """Finish current behavior and reset state."""
        logger.debug(f"Finished behavior: {self.current_behavior.value if self.current_behavior else 'none'}")
        
        # Reset state
        self.current_behavior = None
        self.target_widget = None
        self.is_performing_action = False
        self.target_position = None
        
        # Set cooldown before next interaction
        self.interaction_cooldown = self.interaction_cooldown_max + random.random() * 3.0
        
        # Return to idle
        self.overlay.set_animation_state('idle')
    
    def force_interact_with_widget(self, widget, behavior=None):
        """
        Force panda to interact with a specific widget.
        
        Args:
            widget: Widget to interact with
            behavior: Optional specific behavior, or auto-choose
        """
        self.target_widget = widget
        
        if behavior is None:
            behavior = self._choose_behavior_for_widget(widget)
        
        if behavior:
            self._start_behavior(behavior)
    
    def set_mischievousness(self, level):
        """
        Set panda's mischievousness level.
        
        Args:
            level: Float 0.0-1.0, how likely to interact
        """
        self.mischievousness = max(0.0, min(1.0, level))
    
    def set_playfulness(self, level):
        """
        Set panda's playfulness level.
        
        Args:
            level: Float 0.0-1.0, animation exaggeration
        """
        self.playfulness = max(0.0, min(1.0, level))


# Convenience function
def create_interaction_behavior(panda_overlay, widget_detector):
    """
    Create panda interaction behavior system.
    
    Args:
        panda_overlay: TransparentPandaOverlay instance
        widget_detector: WidgetDetector instance
        
    Returns:
        PandaInteractionBehavior instance or None
    """
    if not PYQT_AVAILABLE:
        logger.warning("PyQt6 not available, cannot create interaction behavior")
        return None
    
    return PandaInteractionBehavior(panda_overlay, widget_detector)
