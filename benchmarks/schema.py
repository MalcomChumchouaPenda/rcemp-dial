
import json
from uuid import uuid4
from functools import cached_property
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import Table
from scipy import stats


Base = declarative_base()
CASCADE = "all, delete-orphan"


# ABSTRACT CLASSES    

class Identifiable:

    def __repr__(self):
        clsname = self.__class__.__qualname__
        return '%s(%s)' % (clsname, self.uid)
    
    @classmethod
    def next_uid(cls):
        prefix = cls.__prefix__
        uid = uuid4().hex
        return f'{prefix}:{uid}' 
    

class Competency(Identifiable, Base):

    __prefix__ = 'comp'
    __tablename__ = 'competencies'
    uid = Column(String(100), primary_key=True)
    activity = Column(String(200), nullable=False)
    capability = Column(Float, nullable=False)
    cost = Column(Float, default=0)
    type = Column(String(200))
    ressource_id = Column(String(100), ForeignKey('ressources.uid'))

    __mapper_args__ = {
        "polymorphic_identity": "competencies",
        "polymorphic_on": "type",
    }
    
    def __repr__(self):
        ac = self.activity
        ca = self.capability
        co = self.cost
        return f'comp({ac}, {ca}, {co})'
    

class Ressource(Identifiable, Base):

    __tablename__ = 'ressources'
    uid = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    planning = relationship('Position', cascade=CASCADE, backref='ressource')
    competencies = relationship('Competency', cascade=CASCADE, backref='ressource', lazy=False)
    pauses= relationship('Pause', cascade=CASCADE, backref='ressource', lazy=False)
    type = Column(String(200))

    __mapper_args__ = {
        "polymorphic_identity": "ressources",
        "polymorphic_on": "type",
    }

    def __repr__(self):
        return self.name
    
    @cached_property
    def capabilities(self):
        return {c.activity:c.capability for c in self.competencies}

    @cached_property
    def costs(self):
        return {c.activity:c.cost for c in self.competencies}
    

class Task(Identifiable, Base):

    __tablename__ = 'tasks'
    uid = Column(String(100), primary_key=True)    
    rank = Column(Integer, nullable=False)
    activity = Column(String(100), nullable=False)
    positions = relationship('Position', cascade=CASCADE, backref='task', lazy=False)
    type = Column(String(200))

    __mapper_args__ = {
        "polymorphic_identity": "tasks",
        "polymorphic_on": "type",
    }


# CUSTOMER CLASSES

class ManufacturingOrder(Identifiable, Base):

    __prefix__ = 'mo'
    __tablename__ = 'manufacturing_orders'
    uid = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    release_date = Column(Integer, nullable=False)
    due_date = Column(Integer, nullable=True)
    max_cost = Column(Float, nullable=True)
    problem_id = Column(String(100), ForeignKey('problems.uid'))
    routing = relationship('Routing', uselist=False, cascade=CASCADE, 
                           backref='order', lazy=False)

    def count_task(self):
        return self.routing.count_task()

    
class Routing(Identifiable, Base):

    __prefix__ = 'ro'
    __tablename__ = 'routings'
    uid = Column(String(100), primary_key=True)
    order_id = Column(String(100), ForeignKey('manufacturing_orders.uid'))
    tasks = relationship('ProductionTask', cascade=CASCADE, backref='routing',
                         order_by='ProductionTask.rank', lazy=False)

    def count_task(self):
        return len(self.tasks)


class ProductionTask(Task):

    __prefix__ = 'tf'
    __tablename__ = 'production_tasks'
    __mapper_args__ = {"polymorphic_identity": "production_tasks"}
    uid = Column(String(100), ForeignKey('tasks.uid'), primary_key=True)
    duration = Column(Float, nullable=False)
    routing_id = Column(String(100), ForeignKey('routings.uid'))
    

# PRODUCTION CLASSES

class Machine(Ressource):

    __prefix__ = 'ma'
    __tablename__ = 'machines'
    __mapper_args__ = {"polymorphic_identity": "machines"}
    uid = Column(String(100), ForeignKey('ressources.uid'), primary_key=True)
    rule = Column(String(100), default='FIFO')
    problem_id = Column(String(100), ForeignKey('problems.uid'))
    functions = relationship('Function', cascade=CASCADE, backref='machine', lazy=False)
    devices = relationship('Device', cascade=CASCADE, backref='machine', lazy=False)
    
    def count_task(self):
        return sum([c.count_task() for c in self.functions])


class ProductionCompetency(Competency):

    __tablename__ = 'production_competencies'
    __mapper_args__ = {"polymorphic_identity": "production_competencies"}
    uid = Column(String(100), ForeignKey('competencies.uid'), primary_key=True)
    function = relationship('Function', uselist=False, backref='competency')
    quality = Column(Float, nullable=True)


association0 = Table('functions_functions', Base.metadata,
                     Column('parent_id', String(100), ForeignKey('functions.uid')),
                     Column('child_id', String(100), ForeignKey('functions.uid')))

association1 = Table('functions_devices', Base.metadata,
                     Column('function_id', String(100), ForeignKey('functions.uid', ondelete='CASCADE')),
                     Column('device_id', String(100), ForeignKey('devices.uid', ondelete='CASCADE')))


class Function(Identifiable, Base):

    __prefix__ = 'fn'
    __tablename__ = 'functions'
    uid = Column(String(100), primary_key=True)
    name = Column(String(50), nullable=False)
    redundant = Column(Boolean, default=False)
    machine_id = Column(String(100), ForeignKey('machines.uid'))
    competency_id = Column(String(100), ForeignKey('production_competencies.uid'))
    devices = relationship('Device', secondary=association1, lazy=False)

    parents = relationship('Function', secondary=association0,
                            primaryjoin=uid==association0.c.child_id,
                            secondaryjoin=uid==association0.c.parent_id,
                            back_populates='children', lazy=False)
    children = relationship('Function', secondary=association0,
                            primaryjoin=uid==association0.c.parent_id,
                            secondaryjoin=uid==association0.c.child_id,
                            back_populates='parents', lazy=False)

    def __repr__(self):
        return self.name

    def rul(self):
        if self.redundant:
            pdf = 0
            for device in self.devices:
                pdf += device.rul()
            for child in self.children:
                pdf += child.rul()
        else:
            pdf = 1
            for device in self.devices:
                pdf *= device.rul()
            for child in self.children:
                pdf *= child.rul()
        return pdf
    
    def count_task(self):
        sum_a = sum([c.count_task() for c in self.children])
        sum_b = sum([d.count_task() for d in self.devices])
        return sum_a + sum_b
    
    def check_status(self, duration):
        failures0 = []
        if not self.redundant:
            status = True
            for device in self.devices:
                test = device.check_status(duration)
                if not test:
                    failures0.append(device)
                status = status and test
                # print(device, status, test)
            for child in self.children:
                test, failures1 = child.check_status(duration)
                failures0.extend(failures1)
                status = status and test
                # print(child, status, test)
        else:
            status = False
            key = lambda item: item.rul()
            devices = list(sorted(self.devices, key=key))
            if len(devices) > 0:
                device = devices[0]
                test = device.check_status(duration)
                if not test:
                    failures0.append(device)
                status = status or test
            else:
                children = list(sorted(self.children, key=key))
                if len(children) > 0:
                    child = children[0]
                    test, failures1 = child.check_status(duration)
                    failures0.extend(failures1)
                    status = status or test
        return status, failures0
    
    def use(self, duration):
        if not self.redundant:
            for device in self.devices:
                device.use(duration)
            for child in self.children:
                child.use(duration)
        else:
            key = lambda item: item.rul()
            devices = list(sorted(self.devices, key=key))
            if len(devices) > 0:
                devices[0].use(duration)
            else:
                children = list(sorted(self.children, key=key))
                if len(children) > 0:
                    children[0].use(duration)
        

class Device(Identifiable, Base):

    __prefix__ = 'dev'
    __tablename__ = 'devices'
    uid = Column(String(100), primary_key=True)
    name = Column(String(50), nullable=False)
    risk_threshold = Column(Float, nullable=False)
    repair_time = Column(Float, nullable=False)
    use_duration = Column(Integer, default=0)
    initial_duration = Column(Integer, default=0)
    next_duration = Column(Integer, default=0)
    repair_skill = Column(String(200), nullable=False)
    json_law = Column(Text(4294000000), nullable=False)
    machine_id = Column(String(100), ForeignKey('machines.uid'))
    phm_module_id = Column(String(100), ForeignKey('phm_modules.uid'))
    tasks = relationship('MaintenanceTask', cascade=CASCADE)

    def __repr__(self):
        return self.name
    
    @cached_property
    def law(self):
        return json.loads(self.json_law)

    def rul(self, next=True):
        return self.phm_module.rul(self, next=next)

    def count_task(self):
        return len(self.tasks)
    
    def use(self, duration):
        # if self.use_duration > 300:
        #     print(self.machine, self, 'use', duration, 'with duration:', self.use_duration)
        self.use_duration += duration
    
    def maintain(self):
        # print(self.machine, self, 'maintain with duration:', self.use_duration)
        self.use_duration = 0
    
    def check_status(self, duration):
        self.next_duration += duration
        pdf = self.rul(next=True)                          # probability of failure (probability to have failure before t)
        status = pdf < 1-self.risk_threshold
        return status

    def update_status(self, maintened=True):
        self.next_duration = 0 if maintened else self.use_duration


class PHMModule(Identifiable, Base):

    __prefix__ = 'phm'
    __tablename__ = 'phm_modules'
    uid = Column(String(100), primary_key=True)
    devices = relationship('Device', backref='phm_module', cascade=CASCADE)
    
    def rul(self, device, next=True):
        law = device.law
        law_stats = getattr(stats, law['name'])
        duration = device.next_duration if next else device.use_duration
        rul = law_stats.cdf(duration, **law['params'])
        # print(device, rul, device.use_duration, law['params'])
        return rul

    
# MAINTENANCE CLASSES

class MaintenanceTask(Task):

    __prefix__ = 'tm'
    __tablename__ = 'maintenance_tasks'
    __mapper_args__ = {"polymorphic_identity": "maintenance_tasks"}
    uid = Column(String(100), ForeignKey('tasks.uid'), primary_key=True)
    need_date = Column(Integer, nullable=False)
    device_id = Column(String(100), ForeignKey('devices.uid'))


class MaintenanceCompetency(Competency):

    __tablename__ = 'maintenance_competencies'
    __mapper_args__ = {"polymorphic_identity": "maintenance_competencies"}
    uid = Column(String(100), ForeignKey('competencies.uid'), primary_key=True)
        

class MaintenanceRessource(Ressource):

    __prefix__ = 'mr'
    __tablename__ = 'maintenance_ressources'
    __mapper_args__ = {"polymorphic_identity": "maintenance_ressources"}
    uid = Column(String(100), ForeignKey('ressources.uid'), primary_key=True)
    problem_id = Column(String(100), ForeignKey('problems.uid'))
    
    
# PAUSES CLASSES

class Pause(Task):

    __prefix__ = 'ts'
    __tablename__ = 'pauses'
    __mapper_args__ = {"polymorphic_identity": "pauses"}
    uid = Column(String(100), ForeignKey('tasks.uid'), primary_key=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    ressource_id = Column(String(100), ForeignKey('ressources.uid'))


# PROBLEM CLASSES

class Problem(Identifiable, Base):

    __prefix__ = 'pb'
    __tablename__ = 'problems'
    uid = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)

    kwargs = dict(cascade=CASCADE, backref='problem')
    experiments = relationship('Experiment', **kwargs)
    machines = relationship('Machine', order_by="Machine.name", **kwargs)
    orders = relationship('ManufacturingOrder', order_by="ManufacturingOrder.name", **kwargs)
    maintenances = relationship('MaintenanceRessource', order_by="MaintenanceRessource.name", **kwargs)

    def count_task(self):
        count = sum([o.count_task() for o in self.orders])
        count += sum([m.count_task() for m in self.machines])
        return count
    

class Experiment(Identifiable, Base):

    __prefix__ = 'exp'
    __tablename__ = 'experiments'
    uid = Column(String(50), primary_key=True)
    model_name = Column(String(100), nullable=False)
    problem_id = Column(String(50), ForeignKey('problems.uid'), nullable=False)
    statistics = relationship('Statistic', cascade=CASCADE)
    positions = relationship('Position', cascade=CASCADE)
    
    @cached_property
    def name(self):
        return f'{self.problem.name}_{self.model_name}'
    


class Statistic(Identifiable, Base):

    __tablename__ = 'statistics'
    name = Column(String(200), primary_key=True)
    exp_id = Column(String(50), ForeignKey('experiments.uid'), primary_key=True)
    value = Column(Float, nullable=False)


class Position(Identifiable, Base):

    __tablename__ = 'positions'
    task_id = Column(String(200), ForeignKey('tasks.uid'), primary_key=True)
    exp_id = Column(String(50), ForeignKey('experiments.uid'), primary_key=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    ressource_id = Column(String(200), ForeignKey('ressources.uid'))

