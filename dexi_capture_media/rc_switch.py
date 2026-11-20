"""Edge detection on a PX4 ManualControlSetpoint aux channel.

Same convention as tag_nav's engage switch: aux_index 1..6 picks aux1..aux6,
0 turns the switch off, and a value above the threshold counts as high.
"""


class AuxSwitch:
    def __init__(self, aux_index, threshold=0.5):
        self.index = int(aux_index)
        self.threshold = float(threshold)
        self.high = None   # unknown until the first sample, so boot state is not an edge

    @property
    def enabled(self):
        return 1 <= self.index <= 6

    def update(self, msg):
        """Feed one ManualControlSetpoint. Returns 'rising', 'falling' or None."""
        if not self.enabled:
            return None
        value = [msg.aux1, msg.aux2, msg.aux3, msg.aux4, msg.aux5, msg.aux6][self.index - 1]
        high = value > self.threshold
        prev, self.high = self.high, high
        if prev is None or prev == high:
            return None
        return 'rising' if high else 'falling'


class HoldButton:
    """A momentary button that does two things: tap or hold.

    update() returns 'tap' when the button is released before hold_s, and
    'hold' once it has been held for hold_s (only once per press; releasing
    afterwards returns nothing). With hold_s <= 0 there is no hold: 'tap' fires
    on the press itself.
    """

    def __init__(self, aux_index, threshold=0.5, hold_s=3.0):
        self.switch = AuxSwitch(aux_index, threshold)
        self.hold_s = float(hold_s)
        self.pressed_at = None
        self.held = False

    @property
    def enabled(self):
        return self.switch.enabled

    @property
    def index(self):
        return self.switch.index

    def update(self, msg, now):
        """Feed one ManualControlSetpoint and the current time (s). Returns 'tap', 'hold' or None."""
        edge = self.switch.update(msg)
        if self.hold_s <= 0:
            return 'tap' if edge == 'rising' else None
        if edge == 'rising':
            self.pressed_at, self.held = now, False
            return None
        if edge == 'falling':
            tapped = self.pressed_at is not None and not self.held
            self.pressed_at = None
            return 'tap' if tapped else None
        if self.pressed_at is not None and not self.held and now - self.pressed_at >= self.hold_s:
            self.held = True
            return 'hold'
        return None
