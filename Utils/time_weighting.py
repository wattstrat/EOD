import numpy as np
import random as rdm
import datetime
from dateutil.tz import tzutc

from Utils.Numpy import div0
from Utils.maths_functions import sigmoid
import Config.config as config


def time_weight(time_scope, current_date):
    if time_scope['simu_type'] == 'compare':
        return 1
    else:
        numerator = get_hours_number_between_dates(time_scope["start"], current_date)
        denominator = get_hours_number_between_dates(time_scope["start"], time_scope["end"])
        return numerator / denominator


def get_hypothesis_from_milestones(current_date, global_time_scope):

    index = None

    for ind, milestone in enumerate(global_time_scope['milestones']):
        if milestone >= current_date:
            # Return (index of previous milestone, index of current milestone, timescope)
            return (index, ind, create_sliced_milestone_timescope(ind, global_time_scope))
        index = ind

    raise Exception("Milestone missing for date %s : we have milestones %s" % (current_date, milestones))


# Timescope milestone is a timescope to calculate state of the world at milestone T
# Calculation is done between REF_DATE and milestone
def create_milestone_timescope(milestone_index, global_ts):
    milestones = global_ts['milestones']
    return {
        'start': config.REF_DATE, 'end': milestones[milestone_index],
        'real_start': global_ts['real_start'], 'real_end': global_ts['real_end'],
        'simu_type': global_ts['simu_type']
    }


# Timescope sliced milestone is a timescope to calculate state inside 2 milestone (T-1, T)
# same as above except start
def create_sliced_milestone_timescope(milestone_index, global_ts):
    milestones = global_ts['milestones']
    if milestone_index - 1 < 0:
        start = config.REF_DATE
    else:
        start = milestones[milestone_index - 1]

    ret = create_milestone_timescope(milestone_index, global_ts)
    ret['start'] = start

    return ret


def milestones_timeweighted_hypo_fullyear(calculus, global_time_scope, year, funEnd, ini=None, funIni=None,
                                          milestonesHypotheses={}, others={}, shape=None, **kwargs):
    start = datetime.datetime(year, 1, 1, 0, tzinfo=tzutc())
    end = datetime.datetime(year, 12, 31, 23, tzinfo=tzutc())
    ret = {start: milestones_timeweighted_hypo(calculus, global_time_scope, start, funEnd, ini=ini, funIni=funIni,
                                               milestonesHypotheses=milestonesHypotheses, others=others,
                                               shape=shape, **kwargs),
           end: milestones_timeweighted_hypo(calculus, global_time_scope, end, funEnd, ini=ini, funIni=funIni,
                                             milestonesHypotheses=milestonesHypotheses, others=others,
                                             shape=shape, **kwargs)}
    for milestone in global_time_scope['milestones']:
        if milestone > start and milestone < end:
            ret[milestone] = milestones_timeweighted_hypo(calculus, global_time_scope, milestone, funEnd, ini=ini,
                                                          funIni=funIni, milestonesHypotheses=milestonesHypotheses,
                                                          others=others, shape=shape, **kwargs)
    return ret


def milestones_map(milestones, year, **kwargs):
    type_interpo = kwargs.pop('type_interpo', 'linear')
    simu_type = kwargs.pop('simutype', None)
    # geometric cannot be computed without using hypothesis, which makes it too cumbersome
    if type_interpo == 'geometric':
        type_interpo = 'linear'
    maxmilestone = max(milestones.keys())
    minmilestone = min(milestones.keys())
    if maxmilestone < datetime.datetime(year + 1, 1, 1, 0, tzinfo=tzutc()):
        milestones[datetime.datetime(year + 1, 1, 1, 0, tzinfo=tzutc())] = milestones[maxmilestone]
    if minmilestone > datetime.datetime(year + 1, 1, 1, 0, tzinfo=tzutc()):
        milestones[datetime.datetime(year, 1, 1, 0, tzinfo=tzutc())] = milestones[minmilestone]
    list_starts_ends = build_ymw(year)
    ret = []
    for one_se in list_starts_ends:
        if simu_type == 'compare':
            ret.append(milestones[maxmilestone])
        else:
            ret.append(compute_weighted_hypos(one_se[0], one_se[1], milestones, type_interpo, **kwargs))
    return np.array(ret)


def build_ymw(year):
    ret = []
    ret.append([datetime.datetime(year, 1, 1, 0, tzinfo=tzutc()), datetime.datetime(year + 1, 1, 1, 0, tzinfo=tzutc())])
    for i in range(11):
        ret.append([datetime.datetime(year, i + 1, 1, 0, tzinfo=tzutc()),
                    datetime.datetime(year, i + 2, 1, 0, tzinfo=tzutc())])
    ret.append([datetime.datetime(year, 12, 1, 0, tzinfo=tzutc()),
                datetime.datetime(year + 1, 1, 1, 0, tzinfo=tzutc())])
    ret.append([datetime.datetime(year, 1, 1, 0, tzinfo=tzutc()), iso_to_gregorian(year, 2, 0)])
    for i in range(51):
        ret.append([iso_to_gregorian(year, 2 + i, 0), iso_to_gregorian(year, 3 + i, 0)])
    ret.append([iso_to_gregorian(year, 53, 0), datetime.datetime(year + 1, 1, 1, 0, tzinfo=tzutc())])
    return ret


def iso_year_start(iso_year):
    "The gregorian calendar date of the first day of the given ISO year"
    fourth_jan = datetime.datetime(iso_year, 1, 4, tzinfo=tzutc())
    delta = datetime.timedelta(fourth_jan.isoweekday() - 1)
    return fourth_jan - delta


def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"
    year_start = iso_year_start(iso_year)
    return year_start + datetime.timedelta(days=iso_day - 1, weeks=iso_week - 1)


def compute_weighted_hypos(start, end, milestones, type_interpo, **kwargs):
    listdates = pertinent_dates(start, end, milestones)
    tempdate = start
    coeffs = {}
    while tempdate < end:
        idx = find_idx(tempdate, listdates)
        coeffs[idx] = coeffs.get(idx, [])
        coeffs[idx].append(coef_from_dates(tempdate, listdates[idx], listdates[idx + 1], type_interpo, **kwargs))
        tempdate += datetime.timedelta(hours=1)
    hypos = []
    weights = []
    for idx in coeffs:
        onec = sum(coeffs[idx]) / len(coeffs[idx])
        temph = (1 - onec) * milestones[listdates[idx]] + onec * milestones[listdates[idx + 1]]
        hypos.append(temph)
        weights.append(len(coeffs[idx]))
    return np.average(np.array(hypos), weights=np.array(weights), axis=0)


def find_idx(tempdate, listdates):
    for idx, oned in enumerate(listdates):
        if oned <= tempdate and listdates[idx + 1] > tempdate:
            return idx


def coef_from_dates(query_date, start, end, type_interpo, **kwargs):
    if type_interpo == 'linear':
        return (query_date - start) / (end - start)
    elif type_interpo == 'sigmoid':
        transition = kwargs.get('transition', 0.5)
        speed = kwargs.get('speed', 4)
        time_ratio = (query_date - start) / (end - start)
        sigmo = sigmoid(time_ratio, transition, speed)
        return sigmo
    else:
        raise


def pertinent_dates(start, end, milestones):
    listdates = []
    listbefore = []
    listafter = []
    for key in milestones:
        if key >= start and key < end:
            listdates.append(key)
        elif key < start:
            listbefore.append(key)
        else:
            listafter.append(key)
    if listbefore:
        listdates.append(max(listbefore))
    if listafter:
        listdates.append(min(listafter))
    return sorted(listdates)


def milestones_timeweighted_hypo(calculus, global_time_scope, current_date, funEnd, ini=None, funIni=None,
                                 milestonesHypotheses={}, others={}, shape=None, **kwargs):
    # Select current hypotheses
    hypo_milestone = get_hypothesis_from_milestones(current_date, global_time_scope)
    milestone_time_scope = create_milestone_timescope(hypo_milestone[1], global_time_scope)
    # Hypotheses adapted
    hypos = {k: milestonesHypotheses[k][hypo_milestone[1]] for k in milestonesHypotheses.keys()}

    # Previous milestones?
    if hypo_milestone[0] is not None:
        # Construct hypo & timescope for this milestone
        prev_milestone_time_scope = create_milestone_timescope(hypo_milestone[0], global_time_scope)
        prev_milestone_hypos = {k: milestonesHypotheses[k][hypo_milestone[0]] for k in milestonesHypotheses.keys()}

    # Get initial value depending on all params (not really needed but some Ini calculus need size of hypotheses)
    if ini is None:
        if funIni is None:
            raise Exception("Initial value is None and no way to calculate it!")

        # Calculation of initial value depending on milestone

        # Hypotheses for the start is based on milestones
        funIni._simu_specific = ["%s" % (global_time_scope['milestones'][hypo_milestone[1]])]

        ini_c = funIni(time_scope=milestone_time_scope,
                       **hypos,
                       **others)
        ini_c = calculus.get_variable(ini_c)

        # REF_DATE or previous milestone ?
        if hypo_milestone[0] is None:
            ini_p = ini_c
        else:
            # Hypotheses for the start is based on milestones
            funIni._simu_specific = ["%s" % (global_time_scope['milestones'][hypo_milestone[0]])]

            ini_p = funIni(time_scope=prev_milestone_time_scope,
                           **prev_milestone_hypos,
                           **others)
            ini_p = calculus.get_variable(ini_p)

    else:
        ini_p = calculus.get_variable(ini)
        ini_c = ini_p

    start = None
    if hypo_milestone[0] is None:
        # OK, first milestones is the initial data we have
        # In this case, ini_p == ini_c
        start = ini_p
    else:
        # Hypotheses for the start is based on milestones
        funEnd._simu_specific = ["%s" % (global_time_scope['milestones'][hypo_milestone[0]])]
        # timescope of previous milestone => ini with hypo on previous milestone if funIni
        start = funEnd(initial_value=ini_p,
                       time_scope=prev_milestone_time_scope,
                       **prev_milestone_hypos,
                       **others)
        start = calculus.get_variable(start)

    funEnd._simu_specific = ["%s" % (global_time_scope['milestones'][hypo_milestone[1]])]
    end = funEnd(initial_value=ini_c, time_scope=milestone_time_scope, **hypos, **others)
    end = calculus.get_variable(end)

    # Imposed shape
    if shape is not None:
        start = start[shape]
        end = end[shape]

    val = timeweighted_hypo(start, end, current_date, hypo_milestone[2], **kwargs)
    if kwargs.get('reoffset'):
        val = val - config.NONZERO_VAL
    return val


def get_hours_number_between_dates(date1, date2):
    return (date2 - date1).total_seconds() / 3600.0


def timeweighted_hypo(hypo_ini, hypo_end, current_date, time_scope, type_interpo='linear', **kwargs):
    if isinstance(hypo_ini, np.recarray):
        ret = []
        for name in hypo_ini.dtype.names:
            build_kwargs(name, kwargs)
            ret.append(one_d_interpo(hypo_ini[name], hypo_end[name], current_date,
                                     time_scope, type_interpo=type_interpo, **kwargs))
        return np.core.records.fromarrays(ret, names=','.join(hypo_ini.dtype.names))
    else:
        return one_d_interpo(hypo_ini, hypo_end, current_date, time_scope, type_interpo=type_interpo, **kwargs)


def build_kwargs(name, kwargs):
    if 'distrib_sigmoid' in kwargs:
        if kwargs['distrib_sigmoid']['type'] == 'unif':
            rdm.seed(name)
            mykwargs = kwargs.update({'transition': (rdm.random() - 0.5) * kwargs['distrib_sigmoid']['spread'] + 0.5})


def one_d_interpo(hypo_ini, hypo_end, current_date, time_scope, type_interpo='linear', **kwargs):
    if type_interpo == 'linear':
        return hypo_ini + time_weight(time_scope, current_date) * (hypo_end - hypo_ini)
    elif type_interpo == 'geometric':
        return hypo_ini * div0(hypo_end, hypo_ini)**(time_weight(time_scope, current_date))
    elif type_interpo == 'sigmoid':
        transition = kwargs.get('transition', 0.5)
        speed = kwargs.get('speed', 4)
        sigmo = sigmoid(time_weight(time_scope, current_date), transition, speed)
        return hypo_ini + sigmo * (hypo_end - hypo_ini)


def geometric_rate_growth(rate, current_date, time_scope):
    n_hours = get_hours_number_between_dates(time_scope["start"], current_date)
    return (1 + rate)**(n_hours / config.NORMAL_YEAR_NHOUR)
