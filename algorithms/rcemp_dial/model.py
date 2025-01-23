
from ..rcemp.model import RCEMPModel
from .agents import DialRegulatorAgent
from .env import DialEnv


class RCEMPDIALModel(RCEMPModel):
    
    ALGORITHM_NAME = 'RCEMP-DIAL'
    REGULATOR_CLASS = DialRegulatorAgent
    ENV_CLASS = DialEnv
