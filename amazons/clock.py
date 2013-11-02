from time import time

class Clock(object):
    """
    A game clock for the Game of the Amazons.  Includes regular fixed time,
    and 'byo-yomi': a number of periods of a set number of seconds whose
    seconds are reset if a move is completed during the period.
    There is one game clock for each player.
    """

    def __init__(self, minutes, seconds, periods, period_seconds):
        self.has_fixed_time = True if (minutes > 0 or seconds > 0) else False
        self.has_periods = True if (periods > 0) else False
        self._seconds = (minutes * 60) + seconds
        self._periods = periods
        self._period_seconds = period_seconds
        self._curr_period = period_seconds
        self.stopped = True

    def start(self):
        """Start the game clock."""
        if self.stopped:
            self.last_update_time = time()
            self.stopped = False

    def stop(self):
        """Stop the game clock (like, between moves)."""
        if not self.stopped:
            self.update()
            self.stopped = True
            # Reset current byo-yomi period.
            if self._seconds == 0 and self._periods > 0:
                self._curr_period = self._period_seconds

    def update(self):
        """
        Updates internal clock bookkeeping based on the current system time.
        External code does not need to call this - it is called automatically
        by the Clock getter properties (minutes, seconds, periods,
        period_seconds).
        """
        if not self.stopped:
            curr_time = time()
            time_passed = curr_time - self.last_update_time
            if time_passed > 0:
                self.last_update_time = curr_time
                # Decrement fixed time.
                self._seconds -= time_passed
                if (self._seconds < 0):
                    time_passed = -1 * self._seconds
                    self._seconds = 0
                    # Decrement byo-yomi.
                    self._curr_period -= time_passed
                    while (self._curr_period < 0):
                        self._periods -= 1
                        time_passed = -1 * self._curr_period
                        self._curr_period = self._period_seconds - time_passed
                    if (self._periods < 1):
                        # Time has run out.
                        self._periods = 0
                        self._curr_period = 0

    @property
    def minutes(self):
        self.update()
        return int(self._seconds / 60)

    @property
    def seconds(self):
        self.update()
        return int(self._seconds % 60)

    @property
    def periods(self):
        self.update()
        return self._periods

    @property
    def period_seconds(self):
        self.update()
        return int(self._curr_period)

    @property
    def is_over(self):
        return (self.minutes == 0 and self.seconds == 0 and
            self.periods == 0 and self.period_seconds == 0)

    def __str__(self):
        return '{:d}:{:0>2d} + {:d} x {:0>2d}'.format(self.minutes,
            self.seconds, self.periods, self.period_seconds)
