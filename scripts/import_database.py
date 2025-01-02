
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from config import DATA_DIR
from utils import constants as cst
from benchmarks.schema import Base


def import_():
    # welcome message
    print('type following parameters:')
    
    # read benchmark description and get generator class
    benchmark_id = input('> Benchmark ID: ')
    benchmark_date = input('> Benchmark Date (YYYY-MM-DD): ')
    choices = cst.GENERATORS
    keys = list(choices.keys())
    while benchmark_id not in keys:
        print(f'Error! Choose among following Benchmarks:\n{keys}')
        benchmark_id = input('> Benchmark ID: ')
    generatorcls = choices[benchmark_id]

    # read db params and create it
    db_type = input('> DB type target: ')
    choices = cst.DATABASES
    keys = list(choices.keys())
    while db_type not in keys:
        print(f'Error! Choose among following DBMS:\n{keys}')
        db_type = input('> DB type target: ')
    dbcls = choices[db_type]

    # read verbose param
    verbose = input('> Display progress details? (O/N):')
    verbose = verbose.lower().strip() == 'o'

    # read replace params
    replace = input('> Replace old data? (O/N):')
    replace = replace.lower().strip() == 'o'

    # check output dir
    backup_name = f'{benchmark_id} {benchmark_date}'
    output_dir = os.path.join(DATA_DIR, 'raw', backup_name)
    if not os.path.exists(output_dir):
        print(f'Error! No database of {benchmark_id} at {benchmark_date}\n')
        return

    # replace old data
    db = dbcls(benchmark_id, verbose=verbose)
    if replace:
        generator = generatorcls(db)
        generator.clear()

    # import new data
    with db.engine.connect() as conn:
        tables = Base.metadata.tables.values()
        listing = list if verbose else tqdm

        # init first loop
        todo = listing(tables)
        count_todo = len(tables)
        count_done = 0
        errors = []

        while count_done < count_todo:
            # visit all tables
            for table in todo:
                try:
                    filename = os.path.join(output_dir, "%s.csv" % table)
                    df = pd.read_csv(filename, encoding='utf-8')
                    df = df.replace({np.nan: None})
                    records = df.to_dict('records')
                    statement = insert(table)
                    for record in records:
                        conn.execute(statement, **record)
                    count_done += 1
                except IntegrityError as e:
                    orig = str(e.orig)
                    if orig.startswith('1452'):
                        errors.append(table)
                    else:
                        raise

            # init next loop
            todo = listing(errors)
            errors = []


if __name__ == '__main__':
    import_()