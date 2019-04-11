import datetime


class delta(object):

    def __init__(self, number, start, stop):
        self.number = number
        self.start = start
        self.stop = stop
        self.cur = None
        self.nextval = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.cur is None:
            self.cur = self.start
        elif self.nextval is None:
            raise StopIteration()
        else:
            self.cur = self.nextval

        if self.cur >= self.stop:
            raise StopIteration()

        self.nextval = self.step(self.cur)
        if self.nextval > self.stop:
            self.nextval = self.stop
        return (self.cur, self.nextval)

    def step(self, cur):
        raise NotImplemented("Step not implemented")

    @classmethod
    def to_string(cls, date):
        return date.strftime(cls.to_str)

    @classmethod
    def number_step(cls, number, start, stop):
        return int((stop - start) / (number * cls.approx_delta)) + 1

    def __str__(self):
        if self.cur is None:
            return 'None'
        return self.__class__.to_string(self.cur)


class deltaYears(delta):
    to_str = "%Y"
    approx_delta = datetime.timedelta(days=365.24419)

    def step(self, cur):
        return datetime.datetime(cur.year + self.number, 1, 1, tzinfo=cur.tzinfo)


class deltaMonths(delta):
    to_str = deltaYears.to_str + "%m"
    approx_delta = datetime.timedelta(days=30.5)

    def step(self, cur):
        months = cur.month + self.number
        return datetime.datetime(cur.year + int(months / 12), months % 12, 1, tzinfo=cur.tzinfo)


class deltaDays(delta):
    to_str = deltaMonths.to_str + "%d"
    approx_delta = datetime.timedelta(days=1)

    def __init__(self, number, start, stop):
        super().__init__(number, start, stop)
        self.td = datetime.timedelta(days=self.number)

    def step(self, cur):
        return datetime.datetime(cur.year, cur.month, cur.day, tzinfo=cur.tzinfo) + self.td


class deltaHours(delta):
    to_str = deltaDays.to_str + "%H"
    approx_delta = datetime.timedelta(hours=1)

    def __init__(self, number, start, stop):
        super().__init__(number, start, stop)
        self.td = datetime.timedelta(hours=self.number)

    def step(self, cur):
        return datetime.datetime(cur.year, cur.month, cur.day, cur.hour, tzinfo=cur.tzinfo) + self.td


class deltaMins(delta):
    to_str = deltaHours.to_str + "%M"
    approx_delta = datetime.timedelta(minutes=1)

    def __init__(self, number, start, stop):
        super().__init__(number, start, stop)
        self.td = datetime.timedelta(minutes=self.number)

    def step(self, cur):
        return datetime.datetime(cur.year, cur.month, cur.day, cur.hour, cur.minute, tzinfo=cur.tzinfo) + self.td


class deltaSecs(delta):
    to_str = deltaMins.to_str + "%S"
    approx_delta = datetime.timedelta(seconds=1)

    def __init__(self, number, start, stop):
        super().__init__(number, start, stop)
        self.td = datetime.timedelta(seconds=self.number)

    def step(self, cur):
        return datetime.datetime(cur.year, cur.month, cur.day,
                                 cur.hour, cur.minute, cur.seconds,
                                 tzinfo=cur.tzinfo) + self.td


class HourIndex(object):

    MAX = 8784

    @staticmethod
    def hour_index_from_start_year(date, year=None):
        if year is None:
            year = date.year
        # Max : 0->8783
        return min(HourIndex.MAX-1,
                   int((date - datetime.datetime(year, 1, 1, tzinfo=date.tzinfo)).total_seconds() / 3600))

    @staticmethod
    def hour_index_end_from_start_year(date, year=None):
        if year is not None and date.year != year:
            return HourIndex.MAX
        return HourIndex.hour_index_from_start_year(date, year)
