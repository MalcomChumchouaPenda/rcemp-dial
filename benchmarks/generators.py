
import os
import re
import json
import functools as fct
import random as rnd
from queue import Queue
from threading import Thread, Event

import pandas as pd
from scipy import stats

from config import DATA_DIR
from . import schema as sch


class BenchmarkGenerator:

    def __init__(self, db, filter_='%'):
        super().__init__()
        self.db = db
        self.filter = filter_
     
    def generate(self):
        raise NotImplementedError

    def clear(self):
        metadata = sch.Base.metadata
        engine = self.db.engine
        metadata.drop_all(bind=engine, checkfirst=True)
        metadata.create_all(engine)


class GeneratorThread(Thread):
    
    def __init__(self, method):
        super().__init__(daemon=True)
        self._method = method
        self._queue = Queue()
        self._problem_ids = []
        self._terminated = Event()
    
    def run(self):
        method = self._method
        queue = self._queue
        while True:
            args = queue.get()
            if args == 'stop':
                self._terminated.set()
                break
            try:
                problem_id = method(*args)
                self._problem_ids.append(problem_id)
            except Exception as e:
                print(f'\n{e}\n')
                break

    def send(self, *args):
        self._queue.put(args)
    
    def stop(self):
        self._queue.put('stop')
    
    def generated(self):
        self._terminated.wait()
        return self._problem_ids


class ArchCoud2001Generator(BenchmarkGenerator):
    
    def generate(self): 
        session =  self.db.connect()  
        uid = sch.Problem.next_uid()
        pb = sch.Problem(uid=uid, name='pb0')
        session.add(pb)
        session.commit()

        self._generate_orders(session, pb)
        self._generate_machines(session, pb)
        session.close()   
        return [uid]

    def _generate_machines(self, session, problem):   
        f1 = sch.Machine.next_uid
        f2 = sch.ProductionCompetency.next_uid

        MA = sch.Machine
        ma1 = MA(uid=f1(), name='ma1', problem=problem)
        ma2 = MA(uid=f1(), name='ma2', problem=problem)
        ma3 = MA(uid=f1(), name='ma3', problem=problem)
        session.add_all([ma1, ma2, ma3])
        session.commit()

        CM = sch.ProductionCompetency
        cm11 = CM(uid=f2(), activity='Milling', capability=1, cost=1, ressource=ma1)
        cm21 = CM(uid=f2(), activity='Turning', capability=1, cost=1.7, ressource=ma2)
        cm22 = CM(uid=f2(), activity='Cutting', capability=1, cost=1.7, ressource=ma2)
        cm31 = CM(uid=f2(), activity='Drilling', capability=1, cost=1, ressource=ma3)
        cm32 = CM(uid=f2(), activity='Turning', capability=1.5, cost=1, ressource=ma3)
        cm33 = CM(uid=f2(), activity='Cutting', capability=1.5, cost=1, ressource=ma3)
        session.add_all([cm11, cm21, cm22, cm31, cm32, cm33])
        session.commit()

    def _generate_orders(self, session, problem):
        f1 = sch.ManufacturingOrder.next_uid
        f2 = sch.Routing.next_uid
        f3 = sch.ProductionTask.next_uid

        MO = sch.ManufacturingOrder   
        mo1 = MO(uid=f1(), name='mo1', release_date=2, due_date=26, problem=problem)
        mo2 = MO(uid=f1(), name='mo2', release_date=1, max_cost=24.5, problem=problem)
        mo3 = MO(uid=f1(), name='mo3', release_date=0, due_date=9, problem=problem)
        session.add_all([mo1, mo2, mo3])
        session.commit()

        RO = sch.Routing
        ro1 = RO(uid=f2(), order=mo1)
        ro2 = RO(uid=f2(), order=mo2)
        ro3 = RO(uid=f2(), order=mo3)

        OP = sch.ProductionTask
        op11 = OP(uid=f3(), rank=1, duration=6, activity='Milling', routing=ro1)
        op12 = OP(uid=f3(), rank=2, duration=8, activity='Turning', routing=ro1)
        op13 = OP(uid=f3(), rank=3, duration=5, activity='Drilling', routing=ro1)
        op21 = OP(uid=f3(), rank=1, duration=8, activity='Turning', routing=ro2)
        op22 = OP(uid=f3(), rank=2, duration=7, activity='Cutting', routing=ro2)
        op31 = OP(uid=f3(), rank=1, duration=8.5, activity='Drilling', routing=ro3)
        session.add_all([op11, op12, op13, op21, op22, op31])
        session.commit()


class BencheikhAl2022Generator(BenchmarkGenerator):

    def generate(self):
        f = self._generate_problem
        threads = []
        for _ in range(4):
            thread = GeneratorThread(f)
            thread.start()
            threads.append(thread)

        filter_ = self.filter.replace('%', '.*')
        filter_ = filter_.replace('_', '\S')
        filter_ += '$'
        x, y = 0, len(threads)
        for i, k_max in enumerate([100, 50]):
            k = rnd.uniform(0, k_max)
            for n_mo in range(10, 101, 10):
                for j in range(10):
                    name = f'k{i+1}_{n_mo}_{j}'
                    if filter_ is None or re.match(filter_, name):
                        thread = threads[x % y]
                        thread.send(name, k, n_mo)
                        x += 1
        
        uids = []
        for thread in threads:
            thread.stop()
            uids.extend(thread.generated())
        return uids

    def _generate_problem(self, name, k, n_mo):
        session = self.db.connect()
        uid = sch.Problem.next_uid()
        pb = sch.Problem(uid=uid, name=name)
        session.add(pb)
        session.commit()
        self._generate_machines(session, pb)
        self._generate_maintenances(session, pb)
        self._generate_orders(session, pb, k, n_mo)
        session.close()
        return uid

    def _generate_orders(self, session, problem, k, n_mo):
        f2 = sch.ManufacturingOrder.next_uid
        f3 = sch.Routing.next_uid
        f4 = sch.ProductionTask.next_uid

        u1 = fct.partial(rnd.uniform, 5, 10)  # routing size
        u2 = fct.partial(rnd.uniform, 1, 10)  # duration        
        u3 = fct.partial(rnd.choice, ['Comp1', 'Comp2', 'Comp3'])
        u4 = fct.partial(rnd.uniform, 0, 10*k)  # release date 

        MO = sch.ManufacturingOrder  
        RO = sch.Routing
        OP = sch.ProductionTask
        for j in range(n_mo):
            rs = int(u1())
            R = int(u4())        # release date
            D = R + 10*rs        # due date
            name = 'mo{:0>3}'.format(j+1)
            mo = MO(uid=f2(), name=name, release_date=R, due_date=D)
            ro = RO(uid=f3(), order=mo)
            problem.orders.append(mo)
            for rank in range(rs):
                op = OP(uid=f4(), 
                        rank=rank, 
                        duration=int(u2()), 
                        activity=u3(), 
                        routing=ro)
                session.add(op)
        session.commit()
    
    def _generate_maintenances(self, session, problem):
        f1 = sch.MaintenanceRessource.next_uid
        f2 = sch.MaintenanceCompetency.next_uid

        MR = sch.MaintenanceRessource
        mr1 = MR(uid=f1(), name='mr1', problem=problem)
        mr2 = MR(uid=f1(), name='mr2', problem=problem)
        session.add_all([mr1, mr2])
        # session.commit()

        CM = sch.MaintenanceCompetency
        cm1 = CM(uid=f2(), ressource=mr1, capability=1, activity='R1')
        cm2 = CM(uid=f2(), ressource=mr2, capability=1, activity='R2')
        session.add_all([cm1, cm2])
        session.commit()

    def _generate_machines(self, session, problem):   
        f1 = sch.Machine.next_uid
        f2 = sch.ProductionCompetency.next_uid
        f3 = sch.Function.next_uid
        f4 = sch.Device.next_uid
        f5 = sch.PHMModule.next_uid

        MA = sch.Machine
        ma1 = MA(uid=f1(), name='ma1', problem=problem)
        ma2 = MA(uid=f1(), name='ma2', problem=problem)
        ma3 = MA(uid=f1(), name='ma3', problem=problem)
        session.add_all([ma1, ma2, ma3])
        # session.commit()

        CM = sch.ProductionCompetency
        cm11 = CM(uid=f2(), activity='Comp1', capability=1.5, ressource=ma1)
        cm12 = CM(uid=f2(), activity='Comp2', capability=1, ressource=ma1)
        cm23 = CM(uid=f2(), activity='Comp3', capability=1.5, ressource=ma2)
        cm31 = CM(uid=f2(), activity='Comp1', capability=1, ressource=ma3)
        cm33 = CM(uid=f2(), activity='Comp3', capability=1, ressource=ma3)
        session.add_all([cm11, cm12, cm23, cm31, cm33])
        # session.commit()

        FN, RFN = sch.Function, fct.partial(sch.Function, redundant=True)
        f11 = FN(uid=f3(), name='F1', competency=cm11, machine=ma1)
        f12 = RFN(uid=f3(), name='F2', competency=cm12, machine=ma1)
        f21 = FN(uid=f3(), name='F1', competency=cm23, machine=ma2)
        f31 = FN(uid=f3(), name='F1', competency=cm31, machine=ma3)
        f32 = FN(uid=f3(), name='F2', competency=cm33, machine=ma3)

        f111 = FN(uid=f3(), name='f1')
        f122 = FN(uid=f3(), name='f2')     
        f211 = FN(uid=f3(), name='f1')
        f212 = RFN(uid=f3(), name='f2')     
        f311 = FN(uid=f3(), name='f1')
        f322 = RFN(uid=f3(), name='f2')
        f11.children.append(f111)
        f12.children.extend([f111, f122])
        f21.children.extend([f211, f212])
        f31.children.append(f311)
        f32.children.append(f322)
        session.add_all([f11, f12, f21, f31, f32])
        # session.commit()

        lambda_m = 100
        lambda_s = lambda_m
        sigma_s = lambda_m / 10
        sigma_p = sigma_s / 5
        Lambda_p = fct.partial(stats.norm.rvs, loc=lambda_s, scale=sigma_s)
        law0 = lambda:json.dumps({'name':'norm', 'params':{'loc':lambda_s, 'scale':sigma_s}})
        law1 = lambda:json.dumps({'name':'norm', 'params':{'loc':Lambda_p(), 'scale':sigma_p}})

        phm = sch.PHMModule(uid=f5())
        session.add(phm)
        # session.commit()

        Dev, kwargs = sch.Device, dict(phm_module=phm, risk_threshold=0.01, repair_time=5)
        dev11 = Dev(uid=f4(), name='Dv1', repair_skill='R1', machine=ma1, json_law=law1(), **kwargs)
        dev12 = Dev(uid=f4(), name='Dv2', repair_skill='R2', machine=ma1, json_law=law0(), **kwargs)
        dev13 = Dev(uid=f4(), name='Dv3', repair_skill='R1', machine=ma1, json_law=law1(), **kwargs)
        dev14 = Dev(uid=f4(), name='Dv4', repair_skill='R2', machine=ma1, json_law=law0(), **kwargs)
        dev21 = Dev(uid=f4(), name='Dv1', repair_skill='R1', machine=ma2, json_law=law0(), **kwargs)
        dev22 = Dev(uid=f4(), name='Dv2', repair_skill='R2', machine=ma2, json_law=law1(), **kwargs)
        dev23 = Dev(uid=f4(), name='Dv3', repair_skill='R1', machine=ma2, json_law=law0(), **kwargs)
        dev24 = Dev(uid=f4(), name='Dv4', repair_skill='R2', machine=ma2, json_law=law1(), **kwargs)
        dev31 = Dev(uid=f4(), name='Dv1', repair_skill='R1', machine=ma3, json_law=law0(), **kwargs)
        dev32 = Dev(uid=f4(), name='Dv2', repair_skill='R2', machine=ma3, json_law=law1(), **kwargs)
        dev33 = Dev(uid=f4(), name='Dv3', repair_skill='R1', machine=ma3, json_law=law0(), **kwargs)
        f111.devices.extend([dev11, dev12, dev13])
        f122.devices.append(dev14)
        f211.devices.extend([dev21, dev22])
        f212.devices.extend([dev23, dev24])
        f311.devices.extend([dev31, dev32])
        f322.devices.extend([dev32, dev33])
        session.add_all([dev11, dev12, dev13, dev14,
                         dev21, dev22, dev23, dev24,
                         dev31, dev32, dev33])
        session.commit()


class Dialysis2021Generator(BenchmarkGenerator):

    FILTER_LAMBDA = 2 * 7 * 24   # 2 weeks
    GENERAL_LAMBDA = 365 * 24    # 1 year
    FILTER_SIGMA = 12
    GENERAL_SIGMA = 24
    RISK_THRESHOLD = 0.5
    REPAIR_TIME = 1

    def __init__(self, db, filter_='%', maintener_ratio=1):
        super().__init__(db, filter_=filter_)
        self.datadir = os.path.join(DATA_DIR, 'raw', 'HGD_dialysis_2018_2021')
        self.maintener_ratio = maintener_ratio
        
    def generate(self):
        f = self._generate_problem
        threads = []
        for _ in range(4):
            thread = GeneratorThread(f)
            thread.start()
            threads.append(thread)

        machines_data = self._load_machines()
        patients_data = self._load_patients()
        prod_slots, maint_slots = self._load_time_slots()
        # print(machines_data)
        # print(patients_data)
        # raise RuntimeError
        if self.filter is None:
            filter_ = '.*'
        else:
            filter_ = self.filter.replace('%', '.*')
            filter_ = filter_.replace('_', r'\S')
            filter_ += '$'
        x, y = 0, len(threads)

        for instance, patients_group in patients_data.groupby('instance'):
            machines_group = machines_data[machines_data.instance==instance]
            if filter_ is None or re.match(filter_, instance):
                thread = threads[x % y]
                thread.send(instance,
                            patients_group,
                            machines_group,
                            prod_slots,
                            maint_slots)
                x += 1
        
        uids = []
        for thread in threads:
            thread.stop()
            uids.extend(thread.generated())
        return uids    

    def _load_machines(self):
        datapath = os.path.join(self.datadir, 'echantillons_machines.csv')
        return pd.read_csv(datapath, parse_dates=[3])
    
    def _load_patients(self):
        datapath = os.path.join(self.datadir, 'echantillons_patients.csv')
        return pd.read_csv(datapath, parse_dates=[1, 7])
    
    def _load_time_slots(self):
        data1 = pd.read_csv(os.path.join(self.datadir, 'tranches_soins.csv'))
        data2 = pd.read_csv(os.path.join(self.datadir, 'tranches_maintenances.csv'))
        return data1, data2
    
    def _calc_pauses(self, data):
        cols = ['D%s' % i for i in range(1, 8)]
        available = 0
        start = end = 0
        time = 0
        pauses = []
        for col in cols:
            series = data[col]
            for _, val in series.items():
                time += 1
                if val == '--':
                    if available == 1:
                        start = time
                        available = 0
                else:
                    if available == 0:
                        end = time - 1
                        available = 1
                        pauses.append((start, end))
        if available == 0:
            end = time
            pauses.append((start, end))
        return pauses

    def _generate_problem(self, name, patients_group, machines_group, 
                          production_slots, maintenance_slots):
        session = self.db.connect()
        uid = sch.Problem.next_uid()
        pb = sch.Problem(uid=uid, name=name)
        session.add(pb)
        session.commit()
        self._generate_machines(session, pb, machines_group, production_slots)
        self._generate_maintenances(session, pb, machines_group, maintenance_slots)
        self._generate_orders(session, pb, patients_group)
        session.close()
        return uid

    def _generate_orders(self, session, problem, patients_group):
        f2 = sch.ManufacturingOrder.next_uid
        f3 = sch.Routing.next_uid
        f4 = sch.ProductionTask.next_uid     
        MO = sch.ManufacturingOrder  
        RO = sch.Routing
        OP = sch.ProductionTask
        j = 0
        for row in patients_group.itertuples():
            for _ in range(int(row.number)):
                j += 1
                R = row.release_date + (24 * (row.day - 1))     # release date
                D = row.due_date * (24 * (row.day - 1))         # due date
                name = 'PAT{:0>3}'.format(j)
                mo = MO(uid=f2(), name=name, release_date=R, due_date=D)
                ro = RO(uid=f3(), order=mo)
                problem.orders.append(mo)
                op = OP(uid=f4(), 
                        rank=0, 
                        duration=row.duration, 
                        activity='soin', 
                        routing=ro)
                session.add(op)
        session.commit()
    
    def _generate_maintenances(self, session, problem, machines_group, maintenance_slots):
        f1 = sch.MaintenanceRessource.next_uid
        f2 = sch.MaintenanceCompetency.next_uid
        pa_id = sch.Pause.next_uid

        MR = sch.MaintenanceRessource
        CM = sch.MaintenanceCompetency
        PA = sch.Pause

        pauses = self._calc_pauses(maintenance_slots)
        nb_machines = machines_group.shape[0]
        nb_mainteners = int(nb_machines * self.maintener_ratio)
        for j in range(nb_mainteners):
            mr = MR(uid=f1(), name='MAINT{:0>3}'.format(j+1), problem=problem)
            session.add(mr)
            session.commit()

            for i, (start, end) in enumerate(pauses):
                pause = PA(uid=pa_id(), start_time=start, end_time=end, 
                           ressource=mr, rank=i, activity='pause')
                session.add(pause)
            session.commit()

            cm1 = CM(uid=f2(), ressource=mr, capability=1, activity='R1')
            cm2 = CM(uid=f2(), ressource=mr, capability=1, activity='R2')
            session.add_all([cm1, cm2])
            session.commit()
            
    def _generate_machines(self, session, problem, machines_group, production_slots):   
        mn_id = sch.Machine.next_uid
        cm_id = sch.ProductionCompetency.next_uid
        fn_id = sch.Function.next_uid
        dv_id = sch.Device.next_uid
        ph_id = sch.PHMModule.next_uid
        pa_id = sch.Pause.next_uid

        PA = sch.Pause
        MA = sch.Machine
        Dev = sch.Device
        CM = sch.ProductionCompetency
        FN, RFN = sch.Function, fct.partial(sch.Function, redundant=True)

        pauses = self._calc_pauses(production_slots)
        for i in range(machines_group.shape[0]):
            row = machines_group.iloc[i]
            ma = MA(uid=mn_id(), name=row.code, problem=problem)
            session.add(ma)
            session.commit()

            for i, (start, end) in enumerate(pauses):
                pause = PA(uid=pa_id(), start_time=start, end_time=end, 
                           ressource=ma, rank=i, activity='pause')
                session.add(pause)
            session.commit()

            cm = CM(uid=cm_id(), activity='soin', capability=1, ressource=ma)
            session.add(cm)
            session.commit()

            f11 = FN(uid=fn_id(), name='f1')
            f12 = FN(uid=fn_id(), name='f2')
            f1 = FN(uid=fn_id(), name='F1', competency=cm, machine=ma)
            f1.children.extend([f11, f12])
            session.add(f1)
            session.commit()

            param_f = {'loc':self.FILTER_LAMBDA, 'scale':self.FILTER_SIGMA}
            param_g = {'loc':self.GENERAL_LAMBDA, 'scale':self.GENERAL_SIGMA}
            law_f = lambda:json.dumps({'name':'norm', 'params':param_f})
            law_g = lambda:json.dumps({'name':'norm', 'params':param_g})
            
            phm = sch.PHMModule(uid=ph_id())
            session.add(phm)
            # session.commit()

            kwargs = dict(phm_module=phm, machine=ma,
                          repair_time=self.REPAIR_TIME,
                          risk_threshold=self.RISK_THRESHOLD, 
                          initial_duration=row.use_duration)
            dev1 = Dev(uid=dv_id(), name='Dv1', repair_skill='R1', json_law=law_g(), **kwargs)
            dev2 = Dev(uid=dv_id(), name='Dv2', repair_skill='R1', json_law=law_g(), **kwargs)
            dev3 = Dev(uid=dv_id(), name='Dv3', repair_skill='R1', json_law=law_g(), **kwargs)
            dev4 = Dev(uid=dv_id(), name='Dv4', repair_skill='R1', json_law=law_g(), **kwargs)
            dev5 = Dev(uid=dv_id(), name='Dv5', repair_skill='R1', json_law=law_g(), **kwargs)
            dev6 = Dev(uid=dv_id(), name='Dv6', repair_skill='R1', json_law=law_g(), **kwargs)
            dev7 = Dev(uid=dv_id(), name='Dv7', repair_skill='R1', json_law=law_g(), **kwargs)
            dev8 = Dev(uid=dv_id(), name='Dv8', repair_skill='R1', json_law=law_g(), **kwargs)
            dev9 = Dev(uid=dv_id(), name='Dv9', repair_skill='R1', json_law=law_g(), **kwargs)
            dev10 = Dev(uid=dv_id(), name='Dv10', repair_skill='R2', json_law=law_f(), **kwargs)
            dev11 = Dev(uid=dv_id(), name='Dv11', repair_skill='R1', json_law=law_g(), **kwargs)
            dev12 = Dev(uid=dv_id(), name='Dv12', repair_skill='R1', json_law=law_g(), **kwargs)
            dev13 = Dev(uid=dv_id(), name='Dv13', repair_skill='R1', json_law=law_g(), **kwargs)
            dev14 = Dev(uid=dv_id(), name='Dv14', repair_skill='R1', json_law=law_g(), **kwargs)
            dev15 = Dev(uid=dv_id(), name='Dv15', repair_skill='R1', json_law=law_g(), **kwargs)
            f11.devices.extend([dev1, dev2, dev3, dev4, dev5, dev6])
            f12.devices.extend([dev6, dev7, dev8, dev9, dev10, dev11, dev12, dev13, dev14, dev15])
            session.add_all([dev1, dev2, dev3, dev4, dev5, dev6, dev7, dev8, dev9, dev10,
                             dev11, dev12, dev13, dev14, dev15])
            session.commit()
    