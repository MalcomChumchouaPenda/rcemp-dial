
import time
from logging import INFO
from functools import cached_property, total_ordering
from collections import OrderedDict
from typing import NamedTuple

from mesa import Agent, Model
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector

from benchmarks import schema as sch
from benchmarks import databases as dbs
# from benchmarks import Db, Experiment
from utils.logging import get_logger



# ----------------------------------------------------
# NOTATIONS
# ----------------------------------------------------
# tid = task identifier
# sid = skill identifer
# aid = agent identifer
# rid = ressource identifier
#----------------------------------------------------


class BasicAgent(Agent):

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)    
        self.satisfied = -1                      # satisfaction
        
    def __repr__(self):
        uid = self.unique_id
        name = self.__class__.__qualname__
        return f'{name}({uid})'
    
    @cached_property
    def env(self):
        '''shortcut of env'''
        return self.model.env
    
    # @cached_property
    # def db(self):
    #     '''shortcut of database'''
    #     return self.model.db
    
    @property
    def time(self):
        '''current time'''
        return self.model.schedule.time

    @cached_property
    def experiment(self):
        '''shortcut of experiment'''
        return self.model.experiment
    
    @cached_property
    def log(self):
        return self.model.log
    

class BasicModel(Model):

    ALGORITHM_NAME = ''

    def __init__(self, db_type, benchmark_id, problem_id, 
                 verbose=None, seed=None, log_level=INFO):
        super().__init__(seed=seed)
        self.verbose = verbose
        self.db_type = db_type
        self.problem_id = problem_id
        self.benchmark_id = benchmark_id

        dbcls = getattr(dbs, f'{db_type}Db')
        db = dbcls(benchmark_id, verbose=verbose)
        session = db.connect()
        self.session = session
        self.db = db

        model_name = self.ALGORITHM_NAME
        query = session.query(sch.Experiment)
        query = query.filter_by(model_name=model_name)
        query = query.filter_by(problem_id=problem_id)
        experiment = query.one()
        self.experiment = experiment

        self.customers = []
        self.producers = []
        self.mainteners = []

        self.speed = 0
        self.elapsed_time = 0
        self.log = get_logger(experiment.name, level=log_level)
        self.schedule = BaseScheduler(self)
        self.datacollector = DataCollector(model_reporters=self.model_reporters(),
                                           agent_reporters=self.agent_reporters())
    
    def model_reporters(self):
        return {'s':"satisfaction", 'Es':'elapsed_time',
                'nC':'cycle_number', 'nTM':'maintenance_number',
                'nR':'late_job_number', 'R':'total_tardiness',
                'Cmax':'max_completion_time', 'Abar':'unavailability'}

    def agent_reporters(self):
        return {}
    

    def stop(self):
        self.running = False
        self.session.commit()
        self.session.close()
        self.db.disconnect()
        # self.logger.stop()
    
    def step(self):
        t0 = time.time()
        self.schedule.step()

        t1 = time.time()
        self.speed = t1 - t0
        self.elapsed_time += self.speed
        self.datacollector.collect(self)
        # self.session.flush()
        # self.session.commit()
    
    
class BasicEnv(OrderedDict):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.plan = Plan(model.session, model.experiment)

    def __repr__(self):
        return self.__class__.__qualname__
    
    @cached_property
    def experiment(self):
        return self.model.experiment
    
    @cached_property
    def log(self):
        return self.model.log
    

class TaskID(NamedTuple):

    aid: str
    rank: int
    sid: str
    uid: str

    def __repr__(self):
        return f'({self.aid}, {self.rank}, {self.sid})'
        

class RessourceID(NamedTuple):

    aid: str
    uid: str

    def __repr__(self):
        return self.aid
    

class BasicObject:

    def __init__(self, tid):
        super().__init__()
        self.tid =  tid                           # task identifier      
        self.aid = tid.aid                        # demander identifier
        self.sid = tid.sid                        # skill identifier
        self.rank = tid.rank                      # task order
    
    def __repr__(self):
        return str(self.tid)
    
    
@total_ordering
class BasicPosition:
    
    def __init__(self, tid, start=0, end=0, rid=0):
        super().__init__()
        self.tid = tid             # task identifier
        self.start = start         # start time
        self.end = end             # end time
        self.rid = rid             # ressource identifier
    
    @property
    def valid(self):
        return self.start <= self.end
    
    def __repr__(self):
        return f'([{self.start}, {self.end}], {self.rid})'

    def __eq__(self, other):
        return self.start == other.start and self.end == other.end
        
    def __lt__(self, other):
        return self.end < other.end or (self.end == other.end and self.start > other.start)
        

    def equivalent(self, other):
        return self.end == other.end
    
    def overlap(self, other):        
        return not (self.end <= other.start or other.end <= self.start)


    def to_dict(self):
        return dict(tid=self.tid, start=self.start, end=self.end, rid=self.rid) 

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


    def to_tuple(self):
        return (self.tid, self.start, self.end, self.rid)
    
    @classmethod
    def from_tuple(cls, data):
        return cls(*data)


    def clone(self, **params):
        data = self.to_dict()
        data.update(params)
        return self.from_dict(data)
    

class Plan:

    def __init__(self, session, experiment):
        super().__init__()
        self.session = session
        self.experiment = experiment
        self._objects = {}
        self._positions = {}

    def place_task(self, obj, task):
        self._objects[obj.tid] = task
        # print('create', task)
        # self.session.add(task)

    def place_position(self, pos):
        tid = pos.tid
        task = self._objects[tid]
        real_pos = self._positions.get(tid)
        if real_pos is None:
            real_pos = sch.Position(task_id=task.uid,
                                    exp_id=self.experiment.uid,
                                    ressource_id=pos.rid.uid,
                                    start_time=pos.start,
                                    end_time=pos.end)
            task.positions.append(real_pos)
            self._positions[tid] = real_pos
        real_pos.ressource_id = pos.rid.uid
        real_pos.start_time = pos.start
        real_pos.end_time = pos.end

    def remove_task(self, obj):
        _ = self._objects.pop(obj.tid)
        # print('delete', task)
        # self.session.delete(task)
