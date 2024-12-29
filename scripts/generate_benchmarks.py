
from benchmarks import databases as dbs
from benchmarks import generators as gen


def generate():
    print('type following parameters:')
    _, dbcls = _ask_dbms_id_and_cls()
    benchmark_id, generatorcls = _ask_generator_id_and_cls()
    verbose = _ask_verbose()
    replace = _ask_replace()
    filter_ = _ask_filter()
    db = dbcls(benchmark_id, verbose)
    generator = generatorcls(db, filter_=filter_)
    if replace:
        generator.clear()
    generator.generate()
    print('\nGeneration terminated !!!')

def _ask_dbms_id_and_cls():
    dbms_id = input('> DBMS name: ')
    try:
        dbcls = getattr(dbs, f'{dbms_id}Db')
    except AttributeError:
        choices = dbs.Db.listing()
        keys = list(choices.keys())
        while dbms_id not in keys:
            print(f'Error! Choose among following DBMS:\n{keys}')
            dbms_id = input('> DBMS name: ')
        dbcls = choices[dbms_id]
    return dbms_id, dbcls

def _ask_generator_id_and_cls():
    benchmark_id = input('> Benchmark ID: ')
    try:
        generatorcls = getattr(gen, f'{benchmark_id}Generator')
    except AttributeError:
        choices = gen.BenchmarkGenerator.listing()
        keys = list(choices.keys())
        while benchmark_id not in keys:
            print(f'Error! Choose among following Benchmarks:\n{keys}')
            benchmark_id = input('> Benchmark ID: ')
        generatorcls = choices[benchmark_id]
    return benchmark_id, generatorcls

def _ask_verbose():
    verbose = input('> Display progress details? (O/N):')
    return verbose.lower().strip() == 'o'

def _ask_replace():
    replace = input('> Replace old data? (O/N):')
    return replace.lower().strip() == 'o'

def _ask_filter():
    filter_ = input('> Any Filter? :')
    if len(filter_.strip()) == 0:
        filter_ = None
    return filter_


if __name__ == '__main__':
    generate()