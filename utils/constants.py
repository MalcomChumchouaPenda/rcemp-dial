
from benchmarks import databases as dbs
from benchmarks import generators as gen
from algorithms.rcemp.model import RCEMPModel
from algorithms.rcemp_dial.model import RCEMPDIALModel
from algorithms.rcemp_dial.model import RCEMPDIALModel1
from algorithms.rcemp_dial.model import RCEMPDIALModel2
from algorithms.rcemp_dial.model import RCEMPDIALModel3
from algorithms.rcemp_dial.model import RCEMPDIALModel4
from algorithms.rcemp_dial.model import RCEMPDIALModel5
from algorithms.rcemp_dial.model import RCEMPDIALModel6
from algorithms.rcemp_dial.model import RCEMPDIALModel7


DATABASES = {'Sqlite':dbs.SqliteDb,
             'MySql':dbs.MySqlDb}

GENERATORS = {'BencheikhAl2022':gen.BencheikhAl2022Generator,
              'ArchCoud2001':gen.ArchCoud2001Generator,
              'Dialysis2021':gen.Dialysis2021Generator}

MODELS = (RCEMPModel, RCEMPDIALModel, RCEMPDIALModel1, 
          RCEMPDIALModel2, RCEMPDIALModel3, RCEMPDIALModel4,
          RCEMPDIALModel5, RCEMPDIALModel6, RCEMPDIALModel7)
MODELS = {modelcls.ALGORITHM_NAME:modelcls for modelcls in MODELS}

