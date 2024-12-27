
# from argparse import ArgumentParser
# from mesa import batch_run
# from tools import benchmarks
# from model import model
# from model import schemas
# from tools import databases

def simulate():
    print('simulating...')

# progname = 'Simulator'
# description='Simulation with benchmarks'
# parser = ArgumentParser(prog=progname, description=description)
# parser.add_argument('-b', '--benchmark', required=True)
# parser.add_argument('-v', '--verbose', action='store_true')
# parser.add_argument('-p', '--process', type=int, default=1)
# parser.add_argument('-s', '--seed', type=float)
# parser.add_argument('-f', '--filter', default='%')


# def find_problems(db, filter_):
#     session = db.connect()
#     Pb = schemas.Problem
#     query = session.query(Pb)
#     if filter_:
#         query = query.filter(Pb.name.like(filter_))
#     pb_ids = [p.uid for p in query.all()]
#     session.close()
#     return pb_ids

# def clear_previous(db, problem_ids):
#     session = db.connect()
#     Exp = schemas.Experiment
#     query = session.query(Exp)
#     query = query.filter(Exp.problem_id.in_(problem_ids))
#     for exp in query.all():
#         session.delete(exp)
#     session.commit()
#     session.close()

# def create_experiments(db, problem_ids):
#     session = db.connect()
#     Exp = schemas.Experiment    
#     Uid = Exp.next_uid
#     exp_ids = {}
#     for pid in problem_ids:
#         uid = Uid()
#         experiment = Exp(uid=uid, problem_id=pid, model_name="RCEMP")
#         session.add(experiment)
#         exp_ids[pid] = uid
#     session.commit()
#     session.close()
#     return exp_ids

# def save_results(db, experiment_ids, results):
#     session = db.connect()
#     metadata = ['RunId', 'iteration', 'benchmark_id', 
#                 'problem_id', 'verbose', 'seed']
#     Stat = schemas.Statistic
#     for result in results:
#         problem_id = result['problem_id']
#         exp_id = experiment_ids[problem_id]
#         stats = [Stat(exp_id=exp_id, name=k, value=v) 
#                  for k,v in result.items() 
#                  if k not in metadata]
#         session.add_all(stats)
#         session.commit()
#     session.close()

# def main(bn_id, filter_, verbose, seed=None, nprc=1):
#     db = databases.SqliteDb(bn_id, verbose=verbose)
#     pb_ids = find_problems(db, filter_)
#     print('\t', pb_ids)
#     clear_previous(db, pb_ids)
#     exp_ids = create_experiments(db, pb_ids)

#     display = not verbose
#     modelcls = model.RCEMPModel
#     params = {'benchmark_id':bn_id, 'problem_id':pb_ids, 'verbose':verbose, 'seed':seed}
#     results = batch_run(modelcls, params, number_processes=nprc, display_progress=display)
#     save_results(db, exp_ids, results)
#     db.disconnect()


# if __name__ == '__main__':
#     args = parser.parse_args()
#     filt = args.filter
#     verb = args.verbose
#     bn_id = args.benchmark
#     nprc = args.process
#     seed = args.seed
#     main(bn_id, filt, verb, seed=seed, nprc=nprc)

