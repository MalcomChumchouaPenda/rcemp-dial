
from benchmarks.schema import MaintenanceTask
from ..base import BasicModel
from .agents import RegulatorAgent
from .env import Env


class RCEMPModel(BasicModel):

    def __init__(self, did, bid, pid, verbose=None, seed=None):
        super().__init__(did, bid, pid, verbose=verbose, seed=seed)
        self.env = Env(self)
        
        problem = self.experiment.problem
        regulator = RegulatorAgent('r0', self, problem)
        self.schedule.add(regulator)
        self.regulator = regulator
