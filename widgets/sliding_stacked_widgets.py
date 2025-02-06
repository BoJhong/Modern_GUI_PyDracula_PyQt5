from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class SlidingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super(SlidingStackedWidget, self).__init__(parent)

        # Initialize parameters
        self.animation_direction = Qt.Horizontal
        self.animation_speed = 500
        self.animation_curve = QEasingCurve.OutCubic
        self.enable_wrap = False

        # State tracking
        self.current_index = 0
        self.next_index = 0
        self.is_animating = False
        self.target_index = None

        # Animation group and transition tracking
        self.animation_group = None
        self.active_transition_indices = set()

    @pyqtSlot()
    def slideInNext(self):
        now = self.currentIndex()
        if self.enable_wrap or now < (self.count() - 1):
            self.slideInIdx(now + 1)

    @pyqtSlot()
    def slideInPrev(self):
        now = self.currentIndex()
        if self.enable_wrap or now > 0:
            self.slideInIdx(now - 1)

    def slideInIdx(self, idx):
        if idx > (self.count() - 1):
            idx = idx % self.count()
        elif idx < 0:
            idx = (idx + self.count()) % self.count()
        self.slideInWgt(self.widget(idx))

    def slideInWgt(self, newwidget):
        # Get widget indices
        target_index = self.indexOf(newwidget)
        if target_index == -1:
            return

        # Skip if trying to animate to the widget that is currently being animated to
        # This prevents animation conflicts when the same target is requested multiple times
        if target_index == self.next_index:
            return

        # Store the target and ensure it's visible
        self.target_index = target_index

        # Handle ongoing animation
        if self.is_animating:
            # Wait for current animation to finish
            return

        # Start new transition
        current_idx = self.currentIndex()
        self._prepareTransition(current_idx, target_index)
        self._startAnimation()

    def _prepareTransition(self, current_idx, next_idx):
        """Prepare widgets for transition"""
        self.current_index = current_idx
        self.next_index = next_idx

        # Get widgets
        current_widget = self.widget(current_idx)
        next_widget = self.widget(next_idx)

        # Setup geometry
        rect = self.frameRect()
        next_widget.setGeometry(rect)

        # Calculate movement direction
        is_forward = current_idx < next_idx

        # Set initial widget positions
        if self.animation_direction == Qt.Horizontal:
            if is_forward:
                next_widget.move(rect.topLeft() + QPoint(rect.width(), 0))
            else:
                next_widget.move(rect.topLeft() + QPoint(-rect.width(), 0))
        else:
            if is_forward:
                next_widget.move(rect.topLeft() + QPoint(0, rect.height()))
            else:
                next_widget.move(rect.topLeft() + QPoint(0, -rect.height()))

        # Save direction for animation
        self._is_forward = is_forward

        # Update tracking
        self.active_transition_indices = {current_idx, next_idx}

        # Only update visibility for widgets involved in transition
        for i in range(self.count()):
            widget = self.widget(i)
            if i in self.active_transition_indices:
                widget.show()
                widget.raise_()
            elif i == self.target_index:
                # Keep last target visible but below current transition widgets
                widget.show()
            else:
                # Hide only widgets not involved in any way
                widget.hide()

    def _startAnimation(self):
        """Start transition animation with enhanced state management"""
        if self.animation_group is not None:
            self._cleanupAnimation()

        self.is_animating = True
        current_widget = self.widget(self.current_index)
        next_widget = self.widget(self.next_index)

        # Ensure proper stacking order before animation
        for i in range(self.count()):
            widget = self.widget(i)
            if widget == next_widget:
                widget.raise_()
            elif widget == current_widget:
                widget.raise_()
            elif i == self.target_index:
                widget.lower()

        # Create animation group
        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.finished.connect(self._onAnimationFinished)

        # Create cleanup timer to ensure animation finishes
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.setSingleShot(True)
        self._cleanup_timer.timeout.connect(self._forceFinishAnimation)

        # Save widget states for animation validation
        self.active_widgets = {current_widget, next_widget}
        if self.target_index not in [self.current_index, self.next_index]:
            last_widget = self.widget(self.target_index)
            self.active_widgets.add(last_widget)
            # Ensure last target stays visible
            last_widget.show()
            last_widget.lower()

        # Get movement direction and calculate positions
        rect = self.frameRect()
        if self.animation_direction == Qt.Horizontal:
            offset = rect.width() if self._is_forward else -rect.width()
            # Always slide in the same direction
            if self._is_forward:
                # Forward: current page slides left, new page slides in from right
                current_end = QPoint(-rect.width(), 0)
                next_start = QPoint(rect.width(), 0)
            else:
                # Backward: current page slides right, new page slides in from left
                current_end = QPoint(rect.width(), 0)
                next_start = QPoint(-rect.width(), 0)
            next_end = QPoint(0, 0)
        else:
            if self._is_forward:
                # Forward: current page slides up, new page slides in from bottom
                current_end = QPoint(0, -rect.height())
                next_start = QPoint(0, rect.height())
            else:
                # Backward: current page slides down, new page slides in from top
                current_end = QPoint(0, rect.height())
                next_start = QPoint(0, -rect.height())
            next_end = QPoint(0, 0)

        # 確保當前頁面在原點開始
        current_widget.move(rect.topLeft())

        # Create parallel group for synchronized movement
        parallel_group = QParallelAnimationGroup()

        # Create current page animation
        current_anim = QPropertyAnimation(current_widget, b"pos", self)
        current_anim.setDuration(self.animation_speed)
        current_anim.setEasingCurve(self.animation_curve)
        current_anim.setStartValue(current_widget.pos())
        current_anim.setEndValue(rect.topLeft() + current_end)

        # Create next page animation
        next_anim = QPropertyAnimation(next_widget, b"pos", self)
        next_anim.setDuration(self.animation_speed)
        next_anim.setEasingCurve(self.animation_curve)
        next_anim.setStartValue(next_start)
        next_anim.setEndValue(rect.topLeft() + next_end)

        # Add animations to group
        parallel_group.addAnimation(current_anim)
        parallel_group.addAnimation(next_anim)

        # Add state validation
        current_anim.valueChanged.connect(lambda: self._validateWidgetState(current_widget))
        next_anim.valueChanged.connect(lambda: self._validateWidgetState(next_widget))

        self.animation_group.addAnimation(parallel_group)
        self.animation_group.start()

    def _validateWidgetState(self, widget):
        """Ensure proper widget state during animation"""
        if not widget.isVisible() and widget in self.active_widgets:
            widget.show()

        # Maintain proper stacking order
        if widget == self.widget(self.next_index):
            widget.raise_()
        elif widget == self.widget(self.current_index):
            widget.raise_()
        elif widget == self.widget(self.target_index):
            widget.lower()  # Keep last target below current animation

    def _cleanupAnimation(self):
        """Clean up current animation"""
        if self.animation_group is not None:
            self.animation_group.stop()
            self.animation_group = None

        # Reset positions
        rect = self.frameRect()
        for idx in self.active_transition_indices:
            widget = self.widget(idx)
            widget.move(rect.topLeft())

    def _onAnimationFinished(self):
        """Handle animation completion"""
        # Validate animation state
        if not self.animation_group:
            return

        # Stop cleanup timer if running
        if hasattr(self, '_cleanup_timer') and self._cleanup_timer.isActive():
            self._cleanup_timer.stop()

        # Stop current animation
        self.animation_group.stop()
        self.animation_group = None

        # Get frame geometry
        rect = self.frameRect()

        # 獲取當前索引和目標
        current_target = self.next_index
        final_target = self.target_index

        # Get current and target indices
        self.current_index = current_target
        self.setCurrentIndex(current_target)

        # Reset widget positions
        for widget in self.active_widgets:
            widget.move(rect.topLeft())

        # Check if further transitions are needed
        if final_target is not None and final_target != current_target:
            # Reset animation state
            self.is_animating = False
            self.active_widgets.clear()

            # Keep related widgets visible and in proper order
            for i in range(self.count()):
                widget = self.widget(i)
                if i == current_target:
                    widget.show()
                    widget.raise_()
                else:
                    widget.hide()
                widget.move(rect.topLeft())

            # Trigger next transition
            QTimer.singleShot(0, lambda: self.slideInWgt(self.widget(final_target)))
        else:
            # Final target reached
            self.is_animating = False
            self.animation_group = None
            self.target_index = None
            self.active_widgets.clear()

            # Update final widget states
            for i in range(self.count()):
                widget = self.widget(i)
                if i == current_target:
                    widget.show()
                    widget.raise_()
                else:
                    widget.hide()
                widget.move(rect.topLeft())

    def _forceFinishAnimation(self):
        """Force finish current animation and jump to final target"""
        if self.is_animating and self.animation_group:
            self.animation_group.stop()

            # Show final target immediately
            target_widget = self.widget(self.target_index)
            target_widget.move(self.frameRect().topLeft())
            target_widget.show()
            target_widget.raise_()
            self.setCurrentIndex(self.target_index)

            # Hide all other widgets
            for i in range(self.count()):
                if i != self.target_index:
                    self.widget(i).hide()

            # Clear state
            self.is_animating = False
            self.animation_group = None

    def setDirection(self, direction):
        self.animation_direction = direction

    def setSpeed(self, speed):
        self.animation_speed = speed

    def setAnimation(self, animationtype):
        self.animation_curve = animationtype

    def setWrap(self, wrap):
        self.enable_wrap = wrap