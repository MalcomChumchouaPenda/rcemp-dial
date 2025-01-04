
import numpy as np
from collections import OrderedDict
from benchmarks import schema as sch
from ..base import BasicAgent, TaskID, RessourceID
from .env import Position, Proposal


class RessourceUser:

    def calc_fp(self, wp, PL, plast=None, forced=None):
        '''fonction de calcul de la position optimal'''
        PL.sort(key=lambda pr:pr.effective)
        if plast is not None:
            PL = [pr for pr in PL if pr.effective.start >= plast.end]
        best_1 = [ep for ep, pp in PL if ep==pp]
        if len(best_1) > 0:
            fp = best_1[0]
            return fp
            # choices = [p for p in best_1 if p == fp]
            # return self.model.random.choice(choices)
        best_2 = [ep for ep, pp in PL if wp <= ep and wp <= pp and not pp <= ep]
        if len(best_2) > 0:
            fp = best_2[0]
            return fp
            # choices = [p for p in best_2 if p == fp]
            # return self.model.random.choice(choices)
        # if forced and len(PL) > 0:
        #     return min([ep for ep, _ in PL])
        if len(PL) > 0:
            fp = min([ep for ep, _ in PL])
            return fp
            # choices = [p for p, _ in PL if p == fp]
            # return self.model.random.choice(choices)


class RessourceWrapper:

    def priorities(self, wishes):
        return wishes
    
    def calc_ep(self, wp, cap, Pcf):
        '''fonction de calcul de la proposal effective'''
        de = (wp.end - wp.start) * cap
        ri = wp.start
        if len(Pcf) > 0:
            plast = max(Pcf)
            ri = max(plast.end, ri)
        di = ri + de
        ep = wp.clone(start=ri, end=di, rid=self.rid)
        return ep
        
    def calc_pp(self, wp, cap, Pcfo):
        '''fonction de calcul de la proposal potentielle'''
        de = (wp.end - wp.start) * cap
        ri = wp.start
        if len(Pcfo) > 0:
            plast = max(Pcfo)
            ri = max(plast.end, ri)
        di = ri + de
        pp = wp.clone(start=ri, end=di, rid=self.rid)
        return pp


class CustomerAgent(RessourceUser, BasicAgent):
    
    def __init__(self, model, order):
        super().__init__(order.name, model)
        self.plan = OrderedDict()    # scheduled position
        self.order = order 
        self.feasible = {}
        self.due_date = order.due_date
        self.completion_date = 0

    def initialize(self):
        time = self.time
        aid = self.unique_id
        order = self.order
        env = self.env
        plan = self.plan   
        if len(plan) == 0:
            ri = order.release_date
            R, D = ri, order.due_date
            key = lambda TF: TF.rank
            OF = sorted(order.routing.tasks, key=key)  # task to schedule
            Pj = [TF.duration for TF in OF]                   
            Rj, Dj = self.calc_wp(R, D, Pj)

            log_info = self.log_info
            feasible = self.feasible
            send_task = env.send_task
            for TF, pj, rj, dj in zip(OF, Pj, Rj, Dj):
                di = ri + pj
                rank = TF.rank
                sid = TF.activity
                tid = TaskID(aid, rank, sid, TF.uid)
                wp = Position(tid, start=ri, end=di)
                send_task(tid, TF, wp)
                ri = di
                plan[tid] = wp
                feasible[tid] = rj, dj
                log_info(f'at {time}:: {self} create task: {wp} for {tid}')

    def calc_wp(self, R, D, Pj):
        '''calcul des fenetres de temps realisables'''
        Rj, r = [], R
        for pj in Pj:
            rmin, r = r, r + pj
            Rj.append(rmin)
        Dj, d = [], D
        for pj in reversed(Pj):
            dmax, d = d, r - pj
            Dj.append(dmax)
        return Rj, reversed(Dj)
                        
    def accept(self, forced=None):
        time = self.time
        env = self.env
        plan = self.plan
        unplanned = sorted([(tid, p) for tid, p in plan.items() if p.rid==0])
        planned = sorted([p for p in plan.values() if p.rid!=0])

        # progressive validation
        index = 0
        plast = None if len(planned) == 0 else planned[-1]
        PL = env.read_proposals(self.unique_id) 
        
        log_info = self.log_info
        calc_fp = self.calc_fp
        accept_proposal = env.accept_proposal
        
        for tid, wp in unplanned: 
            fp = calc_fp(wp, PL[tid], plast, forced=forced)
            if fp is None:
                msg = f'at {time}:: {self} got no valid proposal for {tid} with:'
                msg += f'\n\tplast: {plast}\n\twish: {wp}\n\tproposals: {PL[tid]}'
                log_info(msg)
                break
            accept_proposal(tid, fp)
            planned.append(fp)
            plan[tid] = fp
            plast = fp
            index += 1
            log_info(f'at {time}:: {self} accept {fp} for {tid} with wish {wp}') 

        # store individual statistic on completion time
        if plast is not None:
            self.completion_date = plast.end

        # reschedule task
        reject_proposals = env.reject_proposals
        for tid, wp in unplanned[index:]:
            if plast is not None:
                pj = wp.end - wp.start
                wp.start = plast.end
                wp.end = plast.end + pj
            reject_proposals(tid, wp=wp)
            plan[tid] = wp
            plast = wp
            log_info(f'{self} reject proposals for {tid} with new wish {wp}')          

    def validate(self):
        env = self.env
        plan = self.plan
        time = self.time
        log_info = self.log_info
        planned = sorted([tid for tid, p in plan.items() if p.rid!=0])
        validate_proposal = env.validate_proposal
        read_penality = env.read_penality
        
        for tid in planned:
            fp = plan[tid]
            penality = read_penality(tid)
            # correct positions         
            if penality > 0:
                move = penality
                fp.start -= move
                fp.end -= move
                plan[tid] = fp 
                validate_proposal(tid, fp)
                log_info(f'at {time}:: {self} correct {tid} with {fp}')
            else:
                plan[tid] = fp 
                validate_proposal(tid, fp)
                log_info(f'at {time}:: {self} validate {fp} for {tid}')


class ProducerAgent(RessourceUser, RessourceWrapper, BasicAgent):

    def __init__(self, model, machine):
        super().__init__(machine.name, model)
        self.machine = machine
        self.rid = RessourceID(machine.name, machine.uid)
        for dev in machine.devices:
            dev.use_duration = 0
        self.capabilities = {c.activity:c.capability for c in machine.competencies}      # capabilities
        self.functions = {c.activity:c.function for c in machine.competencies}

        self.next_rank = 0
        self.unavailability = 0
        self.performable_tfs = OrderedDict()
        self.positionned_tfs = OrderedDict()
        self.planned_tfs = OrderedDict()
        self.planned_tms = OrderedDict()
        self.waiting_tms = []
    
    def schedule(self):
        log_info = self.log_info
        performable_tfs = self.performable_tfs
        positionned_tfs = self.positionned_tfs
        planned_tfs = self.planned_tfs
        planned_tms = self.planned_tms
        waiting_tms = self.waiting_tms
        Cap = self.capabilities
        Fn = self.functions
        time = self.time
        env = self.env

        if len(performable_tfs) == 0 and len(positionned_tfs)==0:
            for wp in self.priorities(env.read_wishes(Cap)):
                if wp.rid == 0:
                    performable_tfs[wp.tid] = wp
        
        calc_ep = self.calc_ep
        calc_pp = self.calc_pp
        duration = 0

        Pcfv = list(planned_tfs.values())
        Pcfv.extend([fp for fp, _ in planned_tms.values()])
        Pcfu = list([ep for ep, _ in positionned_tfs.values()])
        for tid, wp in list(performable_tfs.items()):
            sid = tid.sid
            pp = calc_pp(wp, Cap[sid], Pcfv)
            ep = calc_ep(wp, Cap[sid], Pcfv + Pcfu)

            duration += pp.end - pp.start
            status, Dev = Fn[sid].check_status(duration)
            if not status:
                planned_dev = [dev for wp, dev in planned_tms.values() if wp.end >= ep.start]
                missing_tms = [dev for dev in Dev if dev not in planned_dev]
                if len(missing_tms) > 0:
                    send_task = env.send_task
                    aid = self.unique_id
                    Uid = sch.MaintenanceTask.next_uid
                    TM = sch.MaintenanceTask

                    ri = ep.start
                    for dev in missing_tms:
                        di = ri + dev.repair_time
                        uid = Uid()
                        rank = self.next_rank
                        sid = dev.repair_skill
                        tid = TaskID(aid, rank, sid, uid)
                        task = TM(uid=uid, rank=rank, need_date=ri, activity=sid)
                        wp = Position(tid, start=ri, end=di)
                        send_task(tid, task, wp)
                        ri = di

                        self.next_rank += 1
                        planned_tms[tid] = wp, dev
                        waiting_tms.append(tid)
                        dev.tasks.append(task)
                        log_info(f'at {time}:: {self} create task: {wp} for {tid} with dev {Dev} and duration {duration}')
                    return
            
            Pcfu.append(ep)
            planned_tfs[tid] = ep
            performable_tfs.pop(tid)
            positionned_tfs[tid] = ep, pp
            log_info(f'at {time}:: {self} plan {ep} for {tid}')    

    def propose(self):
        time = self.time
        log_info = self.log_info
        # send production proposals
        send_proposals = self.env.send_proposals
        for tid, proposal in self.positionned_tfs.items():
            send_proposals(tid, Proposal(*proposal))
            log_info(f'at {time}:: {self} propose {proposal} for {tid}')

    def accept(self):
        time = self.time
        env = self.env
        aid = self.unique_id
        planned_tms = self.planned_tms
        
        # check maintenance proposals
        log_info = self.log_info
        calc_fp = self.calc_fp
        accept = env.accept_proposal
        reject = env.reject_proposals
        PL = env.read_proposals(aid)
        for tid, PLi in PL.items():
            if len(PLi) == 0:
                continue

            wp, dev = planned_tms[tid]
            fp = calc_fp(wp, PLi, forced=True)
            if fp is None:
                reject(tid, wp=wp)
                log_info(f'at {time}:: {self} reject proposals for {tid} with {wp}')
            else:
                accept(tid, fp)
                planned_tms[tid] = fp, dev
                log_info(f'at {time}:: {self} accept {fp} for {tid}') 

    def validate(self):
        time = self.time
        env = self.env
        rid = self.rid

        # memorize customer validation
        Dc = []
        Fn = self.functions
        planned_tfs = self.planned_tfs
        positionned_tfs = self.positionned_tfs
        read_validation = env.read_validation
        for tid in list(positionned_tfs.keys()):
            validated, fp = read_validation(tid)
            positionned_tfs.pop(tid)
            if not validated or fp.rid != rid:
                planned_tfs.pop(tid)
            else:
                Dc.append(fp)
                planned_tfs[tid] = fp
                Fn[tid.sid].use(fp.end - fp.start) 

        # validate all waiting maintenance task 
        prev_fp = None
        log_info = self.log_info
        reject = env.reject_proposals
        planned_tms = self.planned_tms
        waiting, self.waiting_tms = self.waiting_tms, []
        for tid in waiting:
            fp, dev = planned_tms[tid]
            if fp is None:
                continue
            
            if prev_fp is None:
                prev_tfs = [x for x in Dc if x < fp]
            else:
                prev_tfs = [x for x in Dc if x > prev_fp and x < fp]
            prev_fp = fp

            if len(prev_tfs) == 0:
                reject(tid)
                planned_tms.pop(tid)
                log_info(f'at {time}:: {self} reject {fp} for {tid}')
            
            else:
                env.validate_proposal(tid, fp)
                planned_tms[tid] = fp, dev
                dev.maintain()
                log_info(f'at {time}:: {self} validate {fp} for {tid}')
        
        # correct positions
        read_penality = env.read_penality
        for tid, (fp, dev) in planned_tms.items():
            penality = read_penality(tid)
            if penality > 0:
                move = penality
                fp.start -= move
                fp.end -= move
                planned_tms[tid] = fp, dev
                env.validate_proposal(tid, fp)
                log_info(f'at {time}:: {self} correct {tid} with {fp}')

        # memorize maintenance statistics
        pdfs = [fn.rul() for fn in Fn.values()]
        self.unavailability = sum(pdfs)
        self.positionned_tfs.clear()


class MaintenerAgent(RessourceWrapper, BasicAgent):

    def __init__(self, model, ressource):
        super().__init__(ressource.name, model)
        self.ressource = ressource
        self.rid = RessourceID(ressource.name, ressource.uid)
        self.positionned_tms = OrderedDict()
        self.planned_tms = OrderedDict()
        self.capabilities = {c.activity:c.capability for c in ressource.competencies}

    def schedule(self):
        time = self.time
        env = self.env
        Cap = self.capabilities
        performable = [wp for wp in self.priorities(env.read_wishes(Cap))]
        positionned_tms = self.positionned_tms
        planned_tms = self.planned_tms
        
        log_info = self.log_info
        calc_ep = self.calc_ep
        calc_pp = self.calc_pp
        Pcfv = list(planned_tms.values())
        Pcfv.extend([ep for ep in positionned_tms.values()])
        Pcfu = []
        for wp in sorted(performable):
            tid = wp.tid
            sid = tid.sid
            pp = calc_pp(wp, Cap[sid], Pcfv)
            ep = calc_ep(wp, Cap[sid], Pcfv + Pcfu)
            env.send_proposals(tid, Proposal(ep, pp))
            positionned_tms[tid] = ep            
            Pcfu.append(ep)
            log_info(f'at {time}:: {self} place proposal for {tid}: {ep} - {pp}')

    def validate(self):
        rid = self.rid
        planned_tms = self.planned_tms
        positionned_tms = self.positionned_tms
        read_validation = self.env.read_validation
        for tid in positionned_tms.keys():
            validated, fp = read_validation(tid)
            if validated and fp.rid == rid:
                planned_tms[tid] = fp


class RegulatorAgent(BasicAgent): 

    CUSTOMER_CLASS = CustomerAgent
    PRODUCER_CLASS = ProducerAgent
    MAINTENER_CLASS = MaintenerAgent
    
    def __init__(self, name, model, problem):
        super().__init__(name, model)
        self.problem = problem
        self.satisfied = -1
        self.forced = None
        self.stationnary = False
        self.customers = [self.CUSTOMER_CLASS(model, o) for o in problem.orders]
        self.producers = [self.PRODUCER_CLASS(model, m) for m in problem.machines]
        self.mainteners = [self.MAINTENER_CLASS(model, m) for m in problem.maintenances]
        # self._maxsteps = sum([o.count_task() for o in self.problem.orders])  
        self._forced_time = self._calc_forced_time() 
        # print(f'forced time {self._forced_time}')
        # print('\n\n\t', problem, '\n\t', problem.machines)

    def step(self):      
        # print('step', self.time, 'with forced', self._forced_time)
        customers = self.customers
        producers = self.producers
        mainteners = self.mainteners
        count_tm = self._count_maintenance_tasks
        count_tf = self._count_production_tasks
        sum_pn = self._sum_penalities

        _ = [c.initialize() for c in customers]
        _ = [p.schedule() for p in producers]
        count_loop = 0
        while count_tm():
            _ = [m.schedule() for m in mainteners]
            _ = [p.accept() for p in producers]
            _ = [p.schedule() for p in producers]
            self.log_info(f'maintenance loop number {count_loop}')
            count_loop += 1
            if count_loop > 100:
                raise RuntimeError(f'too much maintenance {count_tm()}')
        
        s0 = count_tf()
        forced = False
        forced = self.time > self._forced_time
        if self._forced_time > 1500:
            msg = f'heavy forced time {self._forced_time} '
            msg += f'max release {max([c.order.release_date for c in customers])}'
            raise RuntimeError(msg)
        _ = [p.propose() for p in producers]
        _ = [c.accept(forced=forced) for c in customers]
        if not forced and s0 == count_tf():
            _ = [p.propose() for p in producers]
            _ = [c.accept(forced=True) for c in customers]

        penalize = self.penalize
        penalizable = True
        count_loop = 0
        while penalizable:
            _ = penalize()
            _ = [c.validate() for c in customers]
            _ = [p.validate() for p in producers]
            _ = [m.validate() for m in mainteners]
            penalizable = sum_pn() > 0
            count_loop += 1
            if count_loop > 1000:
                raise RuntimeError(f'too much penalities {sum_pn()}')
    
        self.validate()
        self._evaluate_system()
    
    def _calc_forced_time(self):
        customers = self.customers
        nMO = len(customers)
        H = 250              # horizon temporel fixe
        Rmax = max([c.order.release_date for c in customers])
        Dmax = min([c.order.due_date for c in customers])
        factor = H/Rmax if Rmax else H/Dmax
        forced_time = 0.45*nMO*factor
        return forced_time
    
    def _count_production_tasks(self):
        producer_ids = [p.unique_id for p in self.producers]
        return len([o for o in self.env.values() 
                      if not o.aid in producer_ids 
                         and o.final_pos is None])
    
    def _count_maintenance_tasks(self):
        producer_ids = [p.unique_id for p in self.producers]
        return len([o for o in self.env.values() 
                      if o.aid in producer_ids 
                         and o.final_pos is None])

    def _sum_penalities(self):
        return sum([o.final_pos.penality 
                    for o in self.env.values()
                    if o.final_pos is not None])

    def _evaluate_system(self):
        env = self.env
        time = self.time
        nT = len(env)                                                  # task numbers
        nTo = len([o for o in env.values() if o.final_pos is None])    # unplanned objects positions
        s0 = self.satisfied
        s1 = 1-(nTo/nT) if nT > 0 else 0
        self.stationnary = s1 == s0
        self.satisfied = s1
        self.log_info(f'at {time}:: {self} satisfied={s1}; stationnary={self.stationnary}')
        # if self.stationnary or s1==1:
        if s1==1:
            self.stop()
        if self.stationnary:
            raise RuntimeError(f'stationnarity at {time}')
            
    def stop(self):
        self.model.stop()
        self.log_info(f'at {self.time}:: {self} stopped')
    
    def penalize(self):
        env = self.env
        log_info = self.log_info

        # group positions
        wished_pos = {tid:o.wish_pos for tid, o in env.items()}
        accepted_pos = [o.final_pos for o in env.values() if o.accepted]
        mo_order = self.sort_cfp(accepted_pos)   
        ma_order = self.sort_pfp(accepted_pos)   
        mr_order = self.sort_mfp(accepted_pos)   

        # calcul idle time and externalities
        apply_penality = env.apply_penality
        for problem_id, pfp in ma_order.items():
            prev_fp = None
            penality = 0
            idle = 0
            for fp in pfp:
                tid = fp.tid
                r_list = [0]
                if prev_fp:
                    r_list.append(prev_fp.end)         
                if tid.aid == problem_id:
                    # case of TM
                    mfp = mr_order[fp.rid.aid]
                    r_list.extend([x.end for x in mfp if x.end <= fp.start])
                else:
                    # case of TF                        
                    cfp = mo_order[tid.aid]
                    r_list.extend([x.end for x in cfp if x.end <= fp.start])
                    if tid.rank == 0:
                        r_list.append(wished_pos[tid].start)
                log_info(f'{self} check order {tid} with pos:{fp} r_list:{list(sorted(r_list))}')
                idle = fp.start - max(r_list)
                penality = idle
                prev_fp = fp
                apply_penality(tid, penality)
                if penality != 0:
                    log_info(f'{self} apply penality {penality} to {tid} cause of idle {idle}')


    def sort_cfp(self, accepted_pos):
        cfp_order = {}
        for c in self.customers:
            aid = c.unique_id
            pos = [fp for fp in accepted_pos 
                        if fp.tid.aid==aid]
            cfp_order[aid] = list(sorted(pos))
        return cfp_order

    def sort_pfp(self, accepted_pos):
        pfp_order = {}
        for p in self.producers:
            aid = p.unique_id
            pos = [fp for fp in accepted_pos 
                        if fp.rid.aid==aid 
                        or fp.tid.aid==aid]
            pfp_order[aid] = list(sorted(pos))
        return pfp_order

    def sort_mfp(self, accepted_pos):
        mfp_order = {}
        for m in self.mainteners:
            aid = m.unique_id
            pos = [fp for fp in accepted_pos 
                        if fp.rid.aid==aid]
            mfp_order[aid] = list(sorted(pos))
        return mfp_order
    
    def validate(self):
        for obj in self.env.values():
            fp = obj.final_pos
            if fp:
                fp.cost = 0

    @property
    def late_job_number(self):
        return len([c for c in self.customers
                      if c.completion_date > c.due_date])
    
    @property
    def total_tardiness(self):
        return sum([max(0, c.completion_date - c.due_date) 
                        for c in self.customers])

    @property
    def max_completion_time(self):
        return max([c.completion_date for c in self.customers])
    
    @property
    def unavailability(self):
        return np.product([p.unavailability for p in self.producers])


