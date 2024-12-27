
import numpy as np
from .schema import MaintenanceTask


def cycle_number(model):
    return model.schedule.steps

def maintenance_number(model):
    return len([obj for obj in model.env.values() 
                    if isinstance(obj.task, MaintenanceTask)])

def late_job_number(model):
    return len([c for c in model.customers
                    if c.completion_date > c.due_date])
    
def total_tardiness(model):
    return sum([max(0, c.completion_date - c.due_date) 
                    for c in model.customers])

def max_completion_time(model):
    return max([c.completion_date for c in model.customers])
    
def unavailability(model):
    return np.product([p.unavailability for p in model.producers])


MODEL_METRICS = {'s':"satisfaction", 'Es':'elapsed_time',
                'nC':cycle_number, 'nTM':maintenance_number,
                'nR':late_job_number, 'R':total_tardiness,
                'Cmax':max_completion_time, 'Abar':unavailability}

AGENT_METRICS = {}
