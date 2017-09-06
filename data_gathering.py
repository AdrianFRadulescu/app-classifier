"""
    This module handles the operations involved in gathering the necessary data for
    creating signatures for processes and applications
"""

import commands
import os
import pickle
import subprocess

import numpy
import requests
import sys
import time

import darwin_queries


def __apps():
    from os import listdir
    return set(filter(lambda n: n.endswith('.app'), listdir('/Applications')))


def __open_app(name='Safari.app'):
    proc = subprocess.Popen(['/usr/bin/open', '-n', '/Applications/' + name], stdout=subprocess.PIPE,
                            preexec_fn=os.setsid, shell=False)

    return {'name': name[:-4], 'process': proc}


def __close_app(**kwargs):
    if commands.getoutput('pgrep ' + kwargs['name']) is not '':
        os.system("osascript -e 'quit app \"{}\"'".format(kwargs['name']))
    kwargs['process'].kill()


def __prom_query(*args):
    """
        Query the given prometheus server
    :param args:
    :return:
    """
    try:
        # get the required data
        while True:
            response = requests.get('{0}/api/v1/query'.format(args[0]),
                                    params={'query': args[1]})
            result = response.json()['data']['result'][0]['value'][1]

            # make sure the result is either numerical or signed Inf
            if result != 'NaN':
                break
            else:
                time.sleep(float(args[2]))

        return numpy.float64(result) if 'Inf' not in result else np.finfo(
            numpy.float64).min if '-' in result else np.finfo(numpy.float64).max

    except requests.exceptions.ConnectionError:
        print 'Cannot connect to prometheus server'
        print 'Check that the right addres was given'

    except IndexError:
        print 'result format is not as demanded due to querying error'


def eval_state(*args):
    """
        Evaluates the present state of a machine according to the given arguments
    :param args: the list of arguments for the queries
        args[-1]: the interval of the evaluation
        args[-2]: dt(time gaps) between two consecutive evaluations
        args[0]:  a dictionary of queries to be addressed
        args[1]:  the domain
        args[2]:  the scrape time for derivatives
        args[3]:  the wait time in case of NaN values
        args[4]:  True if derivatives are to be calculated, Flase otherwise
        args[5]:  the starting position for queries
        args[6]:  the number of different types of queries(eg. simple or with different aggregated functions)
        args[-1], args[-2] are only taken into acount if the length of the args list is greater than 7
    :return:
    """

    state = []

    for cat in sorted(args[0]):
        for ql in args[0][cat]:
            for q in ql if args[4] else ql[args[5]::args[6]]:
                state.append(__prom_query(args[1], q.replace('{}', str(args[2]), 1), args[3]))

    return state


def __progress(count, total, suffix='', last=False):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '#' * filled_len + ' ' * (bar_len - filled_len)

    sys.stdout.write('\r[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))

    if not last:
        sys.stdout.flush()
    else:
        sys.stdout.write()
        print


def eval_app(**kwargs):
    """
        Evaluates a given application and returns a Signature object
    :param kargs:
    :return:
    """

    print '\nevaluating ' + kwargs['name']

    total_setps = int(kwargs['evaltime'] / kwargs['dt']) + 2
    __progress(0, total_setps, False)
    # get the values of the metrics in the initial state of the machine
    initial_state = eval_state(kwargs['queries'], kwargs['domain'], kwargs['evaltime'], kwargs['wait'], False, 0,
                               kwargs['qtypes'])
    __progress(1, total_setps, False)

    # reusable code

    def get_data(time=0, special_func=False):
        """
            executes the queries at this point in time
        :return: the list of data points on each graph at the current moment
        """

        # get the values of the metrics in the current state of the machine
        current_state = eval_state(kwargs['queries'], kwargs['domain'], kwargs['evaltime'], kwargs['wait'],
                                   special_func, 0, kwargs['qtypes'])
        __progress(time + 1, total_setps, False)
        # take the differences in the regular metrics of the states(without the derivative results)

        return map(lambda (i, c): c - i, zip(initial_state, current_state))

    # a list of lists, where each one represents the differences
    data = []
    app = __open_app(kwargs['name'])

    # evaluate the state of the machine for a given amount of time
    for t in range(1, int(kwargs['evaltime'] / kwargs['dt']) + 1):
        time.sleep(kwargs['dt'])

        while True:
            try:
                data += get_data(time=t)
                break
            except:
                continue

    # evaluate the state one more time including the derivatives

    while True:
        try:
            result = get_data(time=total_setps, special_func=True)
            data += result[0::kwargs['qtypes']]
            data += result[1::kwargs['qtypes']]
            break
        except:
            continue

    __close_app(**app)
    return data


def eval_darwin_machine(**kwargs):
    private_apps = set(
        ['PyCharm CE.app', 'Firefox.app', 'Docker.app', 'Flux.app', 'Kitematic.app', 'TorBrowser.app', 'AppCode.app', 'VPN Unlimited.app'])

    p = __prom_query('http://localhost:32775', 'scrape_interval', 5)

    try:
        data = pickle.load(open(kwargs['datafile'], 'rb'))
    except IOError, EOFError:
        data = [[], []]

    for app, i in zip(sorted(__apps() - set(sys.argv[2:]) - private_apps),
                      range(0, len(sorted(__apps() - set(sys.argv[2:]) - private_apps)))):

        app_data = eval_app(queries=darwin_queries.DARWIN_QUERIES, qtypes=darwin_queries.QUERY_TYPES,
                            domain=kwargs['domain'], name=app, evaltime=kwargs['evaltime'], wait=kwargs['wait'],
                            dt=kwargs['dt'])

        data[0] += [app_data]
        data[1] += [i]
        pickle.dump(data, open(kwargs['datafile'], 'wb'))

    print


def load_dataset(**kwargs):
    data = pickle.load(open(kwargs['filepath'], 'rb'))
    return data


if __name__ == "__main__":

    while time.strftime("%H%M%S") < sys.argv[2]:
        eval_darwin_machine(domain='http://localhost:32775', evaltime=35, wait=4, dt=7, datafile=sys.argv[1])

    from pprint import pprint

    pprint(map(lambda x: len(x), load_dataset(filepath=sys.argv[1])[0]))
    pprint(load_dataset(filepath=sys.argv[1])[1])
