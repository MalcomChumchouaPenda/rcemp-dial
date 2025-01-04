
from benchmarks import databases as dbs
from benchmarks import generators as gen
from algorithms.rcemp.model import RCEMPModel
from algorithms.rcemp_dial.model import RCEMPDIALModel


DATABASES = {'Sqlite':dbs.SqliteDb,
             'MySql':dbs.MySqlDb}

GENERATORS = {'BencheikhAl2022':gen.BencheikhAl2022Generator,
              'ArchCoud2001':gen.ArchCoud2001Generator,
              'Dialysis2021':gen.Dialysis2021Generator}

MODELS = {'RCEMP':RCEMPModel,
          'RCEMP-DIAL':RCEMPDIALModel}
