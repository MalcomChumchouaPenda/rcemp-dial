
from utils import constants as cst


def generate():
    # welcome message
    print('type following parameters:')

    # read dbms id and class
    dbms_id = input('> DBMS name: ')
    choices = cst.DATABASES
    keys = list(choices.keys())
    while dbms_id not in keys:
        print(f'Error! Choose among following DBMS:\n{keys}')
        dbms_id = input('> DBMS name: ')
    dbcls = choices[dbms_id]

    # read benchmark id and get generator class
    benchmark_id = input('> Benchmark ID: ')
    choices = cst.GENERATORS
    keys = list(choices.keys())
    while benchmark_id not in keys:
        print(f'Error! Choose among following Benchmarks:\n{keys}')
        benchmark_id = input('> Benchmark ID: ')
    generatorcls = choices[benchmark_id]

    # read verbose params
    verbose = input('> Display progress details? (O/N):')
    verbose = verbose.lower().strip() == 'o'

    # read replace params
    replace = input('> Replace old data? (O/N):')
    replace = replace.lower().strip() == 'o'

    # read filter params
    filter_ = input('> Any Filter? :')
    if len(filter_.strip()) == 0:
        filter_ = None
        
    # create generator and use it
    db = dbcls(benchmark_id, verbose)
    generator = generatorcls(db, filter_=filter_)
    if replace:
        generator.clear()
    generator.generate()
    print('\nGeneration terminated !!!')


if __name__ == '__main__':
    generate()
