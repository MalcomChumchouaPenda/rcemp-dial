
import os
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
    dbms_id = input('> DBMS name: ')
    choices = cst.DATABASES
    keys = list(choices.keys())
    while dbms_id not in keys:
        print(f'Error! Choose among following DBMS:\n{keys}')
        dbms_id = input('> DBMS name: ')
    dbcls = choices[dbms_id]

    # read verbose param
    verbose = input('> Display progress details? (O/N):')
    verbose = verbose.lower().strip() == 'o'

    # check output dir
    output_dir = os.path.join(DATA_DIR, 'raw', benchmark_id)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # connect to db
    db = dbcls(benchmark_id, verbose=verbose)
    with db.engine.connect() as conn:
        # visit all tables
        tables = Base.metadata.tables
        for table in tqdm(tables.values()):
            columns = table.c
            statement = select(table)
            records = conn.execute(statement).fetchall()
            df = pd.DataFrame(records, columns=columns)
            filename = os.path.join(output_dir, "%s.csv" % table)
            df.to_csv(filename, index=False, encoding='utf-8')

if __name__ == '__main__':
    export()