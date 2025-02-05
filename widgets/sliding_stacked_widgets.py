from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class SlidingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super(SlidingStackedWidget, self).__init__(parent)

        # Initialize parameters
        self.m_direction = Qt.Horizontal
        self.m_speed = 500
        self.m_animationtype = QEasingCurve.OutCubic
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = QPoint(0, 0)
        self.m_active = False

        # Animation queue management
        self.animation_queue = []
        self.current_animation = None

    @pyqtSlot()
    def slideInNext(self):
        now = self.currentIndex()
        if self.m_wrap or now < (self.count() - 1):
            self.slideInIdx(now + 1)

    @pyqtSlot()
    def slideInPrev(self):
        now = self.currentIndex()
        if self.m_wrap or now > 0:
            self.slideInIdx(now - 1)

    def slideInIdx(self, idx):
        if idx > (self.count() - 1):
            idx = idx % self.count()
        elif idx < 0:
            idx = (idx + self.count()) % self.count()
        self.slideInWgt(self.widget(idx))

    def slideInWgt(self, newwidget):
        _now = self.currentIndex()
        _next = self.indexOf(newwidget)

        if _now == _next:
            return

        # Create new transition animation
        transition = {
            'now': _now,
            'next': _next,
            'positions': {},
            'widgets': {
                'now': self.widget(_now),
                'next': self.widget(_next)
            }
        }

        # Save current page positions
        transition['positions']['now'] = self.widget(_now).pos()
        transition['positions']['next'] = self.widget(_next).pos()

        # Start new animation if no animation is running
        if not self.m_active:
            self._startAnimation(transition)
        else:
            # Clear existing queue and jump directly to the last requested page
            self.animation_queue.clear()
            # Create transition from current animation target to final destination
            new_transition = {
                'now': self.current_animation['next'],
                'next': _next,
                'positions': {},
                'widgets': {
                    'now': self.widget(self.current_animation['next']),
                    'next': self.widget(_next)
                }
            }
            self.animation_queue.append(new_transition)

            # Ensure all relevant pages are visible
            for i in range(self.count()):
                widget = self.widget(i)
                if i in [self.m_now, self.m_next, _next]:
                    widget.show()
                else:
                    widget.hide()

    def _startAnimation(self, transition):
        """Start a new transition animation"""
        # Save current state
        self.m_next = transition['next']
        self.m_now = transition['now']
        self.m_active = True

        # Set initial layout
        offsetx, offsety = self.frameRect().width(), self.frameRect().height()
        transition['widgets']['next'].setGeometry(self.frameRect())

        # Calculate offset
        if not self.m_direction == Qt.Horizontal:
            if self.m_now < self.m_next:
                offsetx, offsety = 0, -offsety
            else:
                offsetx = 0
        else:
            if self.m_now < self.m_next:
                offsetx, offsety = -offsetx, 0
            else:
                offsety = 0

        # Update and save latest page positions
        current_frame = self.frameRect()
        transition['positions']['next'] = current_frame.topLeft()

        # Set current page position (if transitioning from queue)
        if hasattr(self, 'current_animation') and self.current_animation:
            transition['positions']['now'] = self.current_animation['widgets']['next'].pos()
        else:
            transition['positions']['now'] = current_frame.topLeft()

        # Calculate offset position
        offset = QPoint(offsetx, offsety)

        # Set initial page states
        transition['widgets']['now'].raise_()
        transition['widgets']['next'].setGeometry(current_frame)
        transition['widgets']['next'].move(transition['positions']['next'] - offset)

        # Ensure all relevant pages are visible and in correct positions
        for i in range(self.count()):
            widget = self.widget(i)
            if widget in [transition['widgets']['now'], transition['widgets']['next']]:
                widget.show()
            else:
                widget.hide()
                widget.move(current_frame.topLeft())

        # Create animation group
        anim_group = QParallelAnimationGroup(self)
        anim_group.finished.connect(self.animationDoneSlot)
        self.current_animation = transition

        # Add page animations
        animations = [
            (
                transition['widgets']['now'],
                transition['positions']['now'],
                transition['positions']['now'] + offset
            ),
            (
                transition['widgets']['next'],
                transition['positions']['next'] - offset,
                transition['positions']['next']
            )
        ]

        for widget, start, end in animations:
            animation = QPropertyAnimation(
                widget,
                b"pos",
                duration=self.m_speed,
                easingCurve=self.m_animationtype,
                startValue=start,
                endValue=end,
            )
            anim_group.addAnimation(animation)

        # Start animation
        anim_group.start(QAbstractAnimation.DeleteWhenStopped)

    @pyqtSlot()
    def animationDoneSlot(self):
        """Handle animation completion and process queue"""
        if not self.current_animation:
            return

        # Set current page to target page
        completed_transition = self.current_animation
        self.setCurrentIndex(completed_transition['next'])

        # Reset completed animation page positions
        completed_transition['widgets']['now'].move(completed_transition['positions']['now'])
        completed_transition['widgets']['next'].move(completed_transition['positions']['next'])

        # Set page visibility
        completed_transition['widgets']['now'].hide()
        completed_transition['widgets']['next'].show()
        completed_transition['widgets']['next'].raise_()

        # Clean up current animation
        self.current_animation = None

        # Check for next animation in queue
        if self.animation_queue:
            # Get next animation
            next_transition = self.animation_queue.pop(0)
            # Start next animation
            self._startAnimation(next_transition)
        else:
            # Reset state if no more animations
            self.m_active = False

            # Ensure all pages are in correct state
            for i in range(self.count()):
                widget = self.widget(i)
                if i == self.m_next:
                    widget.show()
                    widget.raise_()
                else:
                    widget.hide()

    def setDirection(self, direction):
        self.m_direction = direction

    def setSpeed(self, speed):
        self.m_speed = speed

    def setAnimation(self, animationtype):
        self.m_animationtype = animationtype

    def setWrap(self, wrap):
        self.m_wrap = wrap