
from collections import defaultdict
from ..rcemp.agents import RegulatorAgent, CustomerAgent
from ..rcemp.agents import ProducerAgent, MaintenerAgent
from ..rcemp.env import Position
from ..base import TaskID




class DialCustomerAgent(CustomerAgent):
    pass


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
        self.priority_rank = 0
        self.priority_base = 1
        self.place_ts(machine, self.planned_tfs)
    
    def priorities(self, wishes):
        keys = defaultdict(lambda:-1)
        i = self.priority_rank
        j = self.priority_base
        for p in wishes:
            key = p.start, p.end
            keys[key] += 1
            p.priority = abs((keys[key] % j)-i)
        return list(sorted(wishes, key=lambda p:p.priority))

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
        self.priority_rank = 0
        self.priority_base = 1
        self.place_ts(ressource, self.planned_tms)

    def priorities(self, wishes):
        keys = defaultdict(lambda:-1)
        i = self.priority_rank
        j = self.priority_base
        for p in wishes:
            key = p.start, p.end
            keys[key] += 1
            p.priority = abs((keys[key] % j)-i)
        return list(sorted(wishes, key=lambda p:p.priority))
    
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
        priority_base = len(self.producers)
        for i, producer in enumerate(self.producers):
            producer.priority_rank += i
            producer.priority_base = priority_base
        priority_base = len(self.mainteners)
        for i, maintener in enumerate(self.mainteners):
            maintener.priority_rank += i
            maintener.priority_base = priority_base
    
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
        


