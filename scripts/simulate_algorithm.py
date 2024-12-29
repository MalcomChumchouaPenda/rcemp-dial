
from pprint import pprint
from mesa import batch_run
from algorithms import base
from benchmarks import schema as sch
from . import _shared_variables as vars


def simulate():
    print('type following parameters:')
    model_id, modelcls = _ask_model_id_and_cls()
    db_id, dbcls = _ask_db_id_and_cls()
    benchmark_id = _ask_benchmark_id()
    seed = _ask_seed()
    verbose = _ask_verbose()
    filter_ = _ask_filter()
    num_proc = _ask_num_process()
    db = dbcls(benchmark_id, verbose)
    problem_ids = _find_problems(db, filter_)
    _clear_previous(db, problem_ids)
    exp_ids = _create_experiments(db, model_id, problem_ids)
    display = not verbose
    params = {'db_id':db_id, 'benchmark_id':benchmark_id, 'problem_id':problem_ids, 'verbose':verbose, 'seed':seed}
    results = batch_run(modelcls, params, number_processes=num_proc, display_progress=display)
    _save_results(db, exp_ids, results)
    db.disconnect()

def _ask_db_id_and_cls():
    db_id = input('> DBMS name: ')
    choices = vars.DATABASES
    keys = list(choices.keys())
    while db_id not in keys:
        print(f'Error! Choose among following DBMS:\n{keys}')
        db_id = input('> DBMS name: ')
    dbcls = choices[db_id]
    return db_id, dbcls

def _ask_benchmark_id():
    benchmark_id = input('> Benchmark ID: ')
    return benchmark_id

def _ask_model_id_and_cls():
    model_id = input('> Algorithm or Model name: ')
    choices = vars.MODELS
    keys = list(choices.keys())
    while model_id not in keys:
        print(f'Error! Choose among following models:\n{keys}')
        model_id = input('> Algorithm or Model name: ')
    modelcls = choices[model_id]
    return model_id, modelcls

def _ask_verbose():
    verbose = input('> Display progress details? (O/N):')
    return verbose.lower().strip() == 'o'

def _ask_filter():
    filter_ = input('> Any Filter? :')
    if len(filter_.strip()) == 0:
        filter_ = None
    return filter_

def _ask_num_process():
    num_proc = input('> Number of process? (default=1): ')
    try:
        return int(num_proc.strip())
    except ValueError:
        return 1
    
def _ask_seed():
    seed = input('> Specify seed? (default=None): ')
    try:
        return int(seed.strip())
    except ValueError:
        return
    

def _find_problems(db, filter_):
    session = db.connect()
    Pb = sch.Problem
    query = session.query(Pb)
    if filter_:
        query = query.filter(Pb.name.like(filter_))
    pb_ids = [p.uid for p in query.all()]
    session.close()
    return pb_ids

def _clear_previous(db, problem_ids):
    session = db.connect()
    Exp = sch.Experiment
    query = session.query(Exp)
    query = query.filter(Exp.problem_id.in_(problem_ids))
    for exp in query.all():
        session.delete(exp)
    session.commit()
    session.close()

def _create_experiments(db, model_id, problem_ids):
    if model_id.endswith('Model'):
        model_name = model_id
    else:
        model_name = model_id + 'Model'
    session = db.connect()
    Exp = sch.Experiment    
    Uid = Exp.next_uid
    exp_ids = {}
    for problem_id in problem_ids:
        uid = Uid()
        experiment = Exp(uid=uid, problem_id=problem_id, model_name=model_name)
        session.add(experiment)
        exp_ids[problem_id] = uid
    session.commit()
    session.close()
    return exp_ids

def _save_results(db, experiment_ids, results):
    session = db.connect()
    metadata = ['RunId', 'iteration', 'benchmark_id',  'problem_id', 
                'db_id', 'verbose', 'seed']
    Stat = sch.Statistic
    # pprint(results)
    for result in results:
        problem_id = result['problem_id']
        exp_id = experiment_ids[problem_id]
        stats = [Stat(exp_id=exp_id, name=k, value=v) 
                 for k,v in result.items() 
                 if k not in metadata]
        session.add_all(stats)
        session.commit()
    session.close()


if __name__ == '__main__':
    simulate()

