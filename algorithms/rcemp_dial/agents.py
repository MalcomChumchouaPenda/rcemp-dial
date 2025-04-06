
from collections import defaultdict
import numpy as np
from ..rcemp.agents import RegulatorAgent, CustomerAgent
from ..rcemp.agents import ProducerAgent, MaintenerAgent
from ..rcemp.env import Position
from ..base import TaskID


class DialCustomerAgent(CustomerAgent):
    pass
    # def __init__(self, model, order):
    #     super().__init__(model, order)
    #     self.satisfied = 0
    #     self.targeted = 1
    
    # def initialize(self):
    #     super().initialize()
    #     self.targeted = len(self.plan)
        
    # def validate(self):
    #     super().validate()
    #     self.satisfied = len([p for p in self.plan.values() if p.rid!=0])


class Priority:
    def __init__(self, agent):
        super().__init__()
        agent.priorities = self
        self.agent = agent

    def __call__(self, wishes):
        raise NotImplementedError

class FIFOPriority(Priority):
    def __call__(self, wishes):
        agent = self.agent
        agent.log.debug(f'{agent} rank task (FIFO):\n\t{[p.tid for p in wishes]}')
        return wishes
    
class EDDPriority(Priority):
    def __call__(self, wishes):
        return list(sorted(wishes, key=lambda p:p.end))
    
class WFIFOPriority(Priority):

    def __init__(self, agent, rank, base):
        super().__init__(agent)
        self.rank = rank         # hash preference of machine
        self.base = base         # number of machines

    # def __init__(self, agent, rank, base):
    #     super().__init__(agent)
    #     self.priority_rank = rank
    #     self.priority_base = base

    def __call__(self, wishes):
        A = []   # first group of priority
        B = []   # second group of priority
        C = []   # third group of priority
        i = self.rank
        m = self.base
        for j, p in enumerate(wishes):
            k = (j % m) - i
            if k == 0:
                A.append(p)
            elif k < 0:
                B.append(p)
            else:
                C.append(p)
        ranked = A + B + C
        agent = self.agent
        agent.log.debug(f'{agent} rank task (WFIFO):\n\t{[p.tid for p in ranked]}')
        return ranked
    
    # def __call__(self, wishes):
    #     i = self.priority_rank
    #     for j, p in enumerate(wishes):
    #         p.priority = (j+2) % i
    #     ranked = list(sorted(wishes, key=lambda p:p.priority))
    #     agent = self.agent
    #     agent.log.debug(f'{agent} rank task (WFIFO):\n\t{[p.tid for p in ranked]}')
    #     return ranked

    # def __call__(self, wishes):
    #     keys = defaultdict(lambda:-1)
    #     i = self.priority_rank +1
    #     j = self.priority_base +1
    #     for p in wishes:
    #         key = p.start, p.end
    #         keys[key] += 1
    #         p.priority = abs((keys[key] % j)-i)
    #     ranked = list(sorted(wishes, key=lambda p:(p.start, p.priority)))
    #     agent = self.agent
    #     agent.log.debug(f'{agent} rank task (WFIFO):\n\t{[p.tid for p in ranked]}')
    #     return ranked

class RandomPriority(Priority):
    def __call__(self, wishes):
        ranked = list(wishes)
        np.random.shuffle(ranked)
        agent = self.agent
        agent.log.debug(f'{agent} rank task (RANDOM):\n\t{[p.tid for p in ranked]}')
        return ranked
    
class RandomEDDPriority(Priority):
    def __call__(self, wishes):
        groups = defaultdict(lambda:[])
        for p in wishes:
            groups[p.end].append(p)
        ranked = []
        for key in sorted(groups.keys()):
            group = groups[key]
            np.random.shuffle(group)
            ranked.extend(group)
        agent = self.agent
        agent.log.debug(f'{agent} rank task (RANDOM+EDD):\n\t{[(p.tid, p.end) for p in ranked]}')
        return ranked

    # def __call__(self, wishes):
    #     ranked = list(wishes)
    #     np.random.shuffle(ranked)
    #     ranked = list(sorted(ranked, key=lambda p:p.end))
    #     agent = self.agent
    #     agent.log.debug(f'{agent} rank task (RANDOM+EDD):\n\t{[(p.tid, p.end) for p in ranked]}')
    #     return ranked

class TimeWatcher:

    HORIZON = 7 * 24

    def place_ts(self, ressource, planned_tr):
        '''fonction de placement des pauses'''
        aid = self.unique_id
        send_pause = self.env.send_pause
        planned_ts = []                   # pauses positions
        for pause in ressource.pauses:
            uid = pause.uid
            rank = pause.rank
            sid = pause.activity
            tid = TaskID(aid, rank, sid, uid)
            ri = pause.start_time
            di = pause.end_time
            rid = self.rid
            p = Position(tid, start=ri, end=di, rid=rid)
            send_pause(tid, pause, p)
            planned_tr[tid] = p
            planned_ts.append(p)
            self.log.debug(f'{self} place pause {tid} at {p}')
        self.planned_ts = planned_ts

    def calc_ep(self, wp, cap, Pcf):
        '''fonction de calcul de la proposal effective'''
        Ps = self.planned_ts
        Pcfn = [p for p in Pcf if p not in Ps]
        de = (wp.end - wp.start) * cap
        ri = wp.start
        if len(Pcfn) > 0:
            plast = max(Pcfn)
            ri = max(plast.end, ri)
        di = ri + de
        ep = wp.clone(start=ri, end=di, rid=self.rid)
        for sp in Ps:
            if ep.overlap(sp):
                ri = sp.end
                ep.start = ri
                ep.end = ri + de
        if ep.end > self.HORIZON:
            return None
        return ep
    

class DialProducerAgent(TimeWatcher, ProducerAgent):

    def __init__(self, model, machine):
        super().__init__(model, machine)
        self.place_ts(machine, self.planned_tfs)
    
    def plan_tf(self, tid, Fn, ep, pp):
        if ep is None:
            self.log.debug(f'{self} stop at the horizon')
            return False
        return super().plan_tf(tid, Fn, ep, pp)
    
    def create_tm(self, tid, task, ri, di, dev):
        if task.rank == 0:
            pi = di - ri
            ri = 0
            di = pi
        if ri + di > self.HORIZON:
            return None
        return super().create_tm(tid, task, ri, di, dev)
    

class DialMaintenerAgent(TimeWatcher, MaintenerAgent):
    
    HORIZON = 7 * 24

    def __init__(self, model, ressource):
        super().__init__(model, ressource)
        self.place_ts(ressource, self.planned_tms)
    
    def create_tm(self, tid, ep, pp):
        if ep is None:
            self.log.debug(f'{self} stop at the horizon')
            return False
        return super().create_tm(tid, ep, pp)
    

class DialRegulatorAgent(RegulatorAgent):   

    CUSTOMER_CLASS = DialCustomerAgent
    PRODUCER_CLASS = DialProducerAgent
    MAINTENER_CLASS = DialMaintenerAgent

    def __init__(self, name, model, problem):
        super().__init__(name, model, problem)
        rule = model.PRODUCER_DISPATCH_RULE
        if rule == 'WFIFO':
            base = len(self.producers)
            for i, producer in enumerate(self.producers):
                WFIFOPriority(producer, i, base)
        elif rule == 'FIFO':
            for producer in self.producers:
                FIFOPriority(producer)
        elif rule == 'EDD':
            for producer in self.producers:
                EDDPriority(producer)
        elif rule == 'RANDOM':
            for producer in self.producers:
                RandomPriority(producer)
        elif rule == 'RANDOM-EDD':
            for producer in self.producers:
                RandomEDDPriority(producer)
        # self.customer_satisfied = 0
                
        rule = model.MAINTENER_DISPATCH_RULE
        if rule == 'WFIFO':
            base = len(self.mainteners)
            for i, maintener in enumerate(self.mainteners):
                WFIFOPriority(maintener, i, base)
        elif rule == 'FIFO':
            for maintener in self.mainteners:
                FIFOPriority(maintener)
        elif rule == 'EDD':
            for maintener in self.mainteners:
                EDDPriority(maintener)
        # ids = [p.unique_id for p in self.producers]
        # print('unicity', [(ids.count(i),i) for i in ids], len(ids))

    def evaluate_system(self):
        try:
            return super().evaluate_system()
        except RuntimeError as e:
            if self.stationnary:
                self.stop()
                return
            raise
        
    # def sort_cfp(self, accepted_pos):
    #     cfp_order = {}
    #     for c in self.customers:
    #         aid = c.unique_id
    #         pos = [fp for fp in accepted_pos 
    #                     if fp.tid.aid==aid]
    #         cfp_order[aid] = list(sorted(pos))
    #     return cfp_order

    def sort_pfp(self, accepted_pos):
        pfp_order = super().sort_pfp(accepted_pos)
        for aid in pfp_order:
            old_order = pfp_order[aid]
            new_order = []
            j = len(old_order) 
            for i in range(j):
                fp = old_order[i]
                if fp.tid.sid == 'pause' and i not in (0, j-1):
                    prev_fp = old_order[i-1]
                    next_fp = old_order[i+1]
                    if fp.start - prev_fp.end >= next_fp.end - next_fp.start:
                        continue
                new_order.append(fp)
            pfp_order[aid] = new_order
        return pfp_order

    def sort_mfp(self, accepted_pos):
        mfp_order = super().sort_mfp(accepted_pos)
        for aid in mfp_order:
            old_order = mfp_order[aid]
            new_order = []
            j = len(old_order) 
            for i in range(j):
                fp = old_order[i]
                if fp.tid.sid == 'pause' and i not in (0, j-1):
                    prev_fp = old_order[i-1]
                    next_fp = old_order[i+1]
                    if fp.start - prev_fp.end >= next_fp.end - next_fp.start:
                        continue
                new_order.append(fp)
            mfp_order[aid] = new_order
        return mfp_order

    def calc_externality(self, problem_id, fp, prev_fp, mo_order, mr_order, wished_pos):
        tid = fp.tid  
        if fp.tid.sid == 'pause':
            # case of pause
            self.log.debug(f'{self} ignore {tid} with pos:{fp}')
            return 0        
        penality = super().calc_externality(problem_id, fp, prev_fp, mo_order, mr_order, wished_pos)
        return penality
        


