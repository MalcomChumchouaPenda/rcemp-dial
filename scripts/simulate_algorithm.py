
from pprint import pprint
from mesa import batch_run
from benchmarks import schema as sch
from utils import constants as cst


def simulate():
    # welcome message
    print('type following parameters:')

    # read algorithm name and choose model class
    algo_name = input('> Algorithm or Model name: ')
    choices = cst.MODELS
    keys = list(choices.keys())
    while algo_name not in keys:
        print(f'Error! Choose among following algorithms:\n{keys}')
        algo_name = input('> Algorithm or Model name: ')
    modelcls = choices[algo_name]
    
    # read benchmark and dbms ids
    benchmark_id = input('> Benchmark ID: ')
    db_type = input('> DB type: ')
    choices = cst.DATABASES
    keys = list(choices.keys())
    while db_type not in keys:
        print(f'Error! Choose among following DBMS:\n{keys}')
        db_type = input('> DB type: ')
    dbcls = choices[db_type]

    # read any filter
    filter_ = input('> Any Filter? :')
    if len(filter_.strip()) == 0:
        filter_ = None

    # read verbose or seed params
    verbose = input('> Display progress details? (O/N):')
    verbose = verbose.lower().strip() == 'o'
    try:
        seed = input('> Specify seed? (default=None): ')
        seed = int(seed.strip())
    except ValueError:
        seed = None

    # read number of process
    num_proc = input('> Number of process? (default=1): ')
    try:
        num_proc = int(num_proc.strip())
    except ValueError:
        num_proc = 1

    # create db connection
    db = dbcls(benchmark_id, verbose)
    session = db.connect()

    # find all problems
    Pb = sch.Problem
    query = session.query(Pb)
    if filter_:
        query = query.filter(Pb.name.like(filter_))
    problem_ids = [p.uid for p in query.all()]
    # pprint(problem_ids)

    # clear previous experiments with the same algorithm
    Exp = sch.Experiment
    query = session.query(Exp)
    query = query.filter(Exp.problem_id.in_(problem_ids))
    query = query.filter(Exp.model_name==algo_name)
    for exp in query.all():
        session.delete(exp)
    session.commit()

    # create new experiments
    model_name = algo_name
    Uid = Exp.next_uid
    experiment_ids = {}
    for problem_id in problem_ids:
        uid = Uid()
        experiment = Exp(uid=uid, problem_id=problem_id, model_name=model_name)
        # print('\t', experiment)
        session.add(experiment)
        experiment_ids[problem_id] = uid
    session.commit()

    # run experiments
    display = not verbose
    params = {'db_type':db_type, 'benchmark_id':benchmark_id, 'problem_id':problem_ids, 'verbose':verbose, 'seed':seed}
    results = batch_run(modelcls, params, number_processes=num_proc, display_progress=display)

    # save results
    metadata = ['RunId', 'iteration',  'benchmark_id', 'problem_id', 'db_type', 'verbose', 'seed']
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
    
    # close db connection
    session.close()
    db.disconnect()


if __name__ == '__main__':
    simulate()
