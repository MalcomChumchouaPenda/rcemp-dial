
from benchmarks import databases as dbs
from benchmarks import generators as gen


def generate():
    print('type following parameters:')
    _, dbcls = _get_db_id_and_cls()
    bid, generatorcls = _get_generator_id_and_cls()
    verbose = input('> Display progress details? (O/N):')
    verbose = verbose.lower().strip() == 'o'
    replace = input('> Replace old data? (O/N):')
    replace = replace.lower().strip() == 'o'
    filter_ = input('> Any Filter? :')
    db = dbcls(bid, verbose)
    generator = generatorcls(db, filter_=filter_)
    if replace:
        generator.clear()
    generator.generate()
    print('\nGeneration terminated !!!')

def _get_db_id_and_cls():
    did = input('> DBMS name: ')
    try:
        dbcls = getattr(gen, f'{did}Db')
    except AttributeError:
        choices = dbs.Db.listing()
        keys = list(choices.keys())
        while did not in keys:
            print(f'Error! Choose among following DBMS:\n{keys}')
            did = input('> DBMS name: ')
        dbcls = choices[did]
    return did, dbcls

def _get_generator_id_and_cls():
    bid = input('> Benchmark ID: ')
    try:
        generatorcls = getattr(gen, f'{bid}Generator')
    except AttributeError:
        choices = gen.BenchmarkGenerator.listing()
        keys = list(choices.keys())
        while bid not in keys:
            print(f'Error! Choose among following Benchmarks:\n{keys}')
            bid = input('> Benchmark ID: ')
        generatorcls = choices[bid]
    return bid, generatorcls


if __name__ == '__main__':
    generate()