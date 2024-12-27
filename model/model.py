
from .schemas import MaintenanceTask
from .base import BasicModel
from .agents import RegulatorAgent
from .env import Env


class RCEMPModel(BasicModel):

    def __init__(self, benchmark_id, problem_id, verbose=None, seed=None):
        super().__init__(benchmark_id, problem_id, verbose=verbose, seed=seed)
        self.env = Env(self)
        
        problem = self.experiment.problem
        regulator = RegulatorAgent('r0', self, problem)
        self.schedule.add(regulator)
        self.regulator = regulator
    
    def model_reporters(self):
        return {'s':satisfaction, 'Es':'elapsed_time',
                'nC':cycle_number, 'nTM':maintenance_number,
                'nR':late_job_number, 'R':total_tardiness,
                'Cmax':max_completion_time, 'Abar':unavailability}


def satisfaction(model):
    return model.regulator.satisfied

def cycle_number(model):
    return model.schedule.steps

def maintenance_number(model):
    return len([obj for obj in model.env.values() 
                    if isinstance(obj.task, MaintenanceTask)])

def late_job_number(model):
    return model.regulator.late_job_number

def total_tardiness(model):
    return model.regulator.total_tardiness

def max_completion_time(model):
    return model.regulator.max_completion_time

def unavailability(model):
    return model.regulator.unavailability

