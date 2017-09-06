import psutil

# the number different types of queries that can be run against a prometheus server
QUERY_TYPES = 2


def __format_query(*args):

    query_list = []

    for rep in ([''] if args[3] else []) + map(lambda n: str(n), range(args[1], args[2])):
        query_list += map(lambda q: q.replace('{}', rep, 1), args[0])

    return query_list

__CPU_QUERIES = [

    # usage
    __format_query(
        [
            'cpu_usage_ratio{core="{}"}',
            'deriv(cpu_usage_ratio{core="{}"}[{}s])'
        ],
        1,
        psutil.cpu_count() + 1,
        True
    ),

    # load average
    [
        'cpu_load_average{span="1m"}',
        'deriv(cpu_load_average{span="1m"}[{}s])'
    ],

    # times
    __format_query(
        [
            'cpu_times_ratio{core="{}", mode!="id"}',
            'deriv(cpu_times_ratio{core="{}", mode!="id"}[{}s])'
        ],
        1,
        psutil.cpu_count() + 1,
        True
    )
]

__NET_QUERIES = [
    # input
    [
        'input_packets',
        'deriv(input_packets[{}s])',
        'input_size_bytes',
        'deriv(input_size_bytes[{}s])'
    ],

    # output
    [
        'output_packets',
        'deriv(output_packets[{}s])',
        'output_size_bytes',
        'deriv(output_size_bytes[{}s])'
    ]
]

__MEM_QUERIES = [
    # active pages
    [
        'vm_active_pages',
        'deriv(vm_active_pages[{}s])'
    ],

    # free pages
    [
        'vm_free_pages',
        'deriv(vm_free_pages[{}s])'
    ],

    # speculative
    [
        'vm_speculative_pages',
        'deriv(vm_speculative_pages[{}s])'
    ],

    # wired down
    [
        'vm_wired_down_pages',
        'deriv(vm_wired_down_pages[{}s])'
    ],

    # reactive
    [
        'vm_reactive_pages',
        'deriv(vm_reactive_pages[{}s])'
    ]
]

__IO_QUERIES = [

    __format_query(
        [
            'disk{}_transfers',
            'deriv(disk{}_transfers[{}s])'
        ],
        0,
        len(psutil.disk_partitions()),
        False
    ),

    __format_query(
        [
            'disk{}_transfer_size_kilobytes',
            'deriv(disk{}_transfer_size_kilobytes[{}s])'
        ],
        0,
        len(psutil.disk_partitions()),
        False
    ),
]


DARWIN_QUERIES = {

    'CPU': __CPU_QUERIES,
    'MEM': __MEM_QUERIES,
    'NET': __NET_QUERIES,
    'IO': __IO_QUERIES
}

SCRAPE_INTERVAL_QUERY = 'scrape_interval'

if __name__ == "__main__":

    i = 0
    for cat in DARWIN_QUERIES:
        for bucket in DARWIN_QUERIES[cat]:
            for q in bucket:
                print q
                i += 1

    print i
