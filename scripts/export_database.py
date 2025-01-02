
import os
from datetime import datetime

import pandas as pd
from tqdm import tqdm
from sqlalchemy import select

from config import DATA_DIR
from utils import constants as cst
from benchmarks.schema import Base


def export():
    # welcome message
    print('type following parameters:')
    
    # read benchmark and dbms ids
    benchmark_id = input('> Benchmark ID: ')
    db_type = input('> DB type: ')
    choices = cst.DATABASES
    keys = list(choices.keys())
    while db_type not in keys:
        print(f'Error! Choose among following DBMS:\n{keys}')
        db_type = input('> DB type: ')
    dbcls = choices[db_type]

    # read verbose param
    verbose = input('> Display progress details? (O/N):')
    verbose = verbose.lower().strip() == 'o'

    # check output dir
    now = datetime.now().strftime('%Y-%m-%d')
    backup_name = f'{benchmark_id} {now}'
    output_dir = os.path.join(DATA_DIR, 'raw', backup_name)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # connect to db
    db = dbcls(benchmark_id, verbose=verbose)
    with db.engine.connect() as conn:

        # listing of tables
        tables = Base.metadata.tables.values()
        if not verbose:
            tables = tqdm(tables)

        # visit all tables
        for table in tables:
            statement = select(table)
            records = conn.execute(statement).fetchall()
            columns = [col.name for col in table.c]
            df = pd.DataFrame(records, columns=columns)
            filename = os.path.join(output_dir, "%s.csv" % table)
            df.to_csv(filename, index=False, encoding='utf-8')

if __name__ == '__main__':
    export()