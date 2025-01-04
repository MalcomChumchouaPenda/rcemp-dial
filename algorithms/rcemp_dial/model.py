
from ..rcemp.model import RCEMPModel
from .agents import DialRegulatorAgent


class RCEMPDIALModel(RCEMPModel):
    
    ALGORITHM_NAME = 'RCEMP-DIAL'
    REGULATOR_CLASS = DialRegulatorAgent
