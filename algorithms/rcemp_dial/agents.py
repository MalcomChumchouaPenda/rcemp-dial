
from collections import defaultdict
from ..rcemp.agents import RegulatorAgent, CustomerAgent, ProducerAgent


class DialCustomerAgent(CustomerAgent):
    
    def __init__(self, model, order):
        super().__init__(model, order)
        ptime = sum([t.duration for t in order.routing.tasks])
        self.max_due_date = order.due_date + ptime

    def calc_fp(self, wp, PL, plast=None, forced=None):
        max_end = self.max_due_date
        PLnew = [pr for pr in PL if pr.effective.end <= max_end]
        self.log_info(f'{self} retains {len(PLnew)} from {len(PL)} with max:{max_end}')
        return super().calc_fp(wp, PLnew, plast=plast, forced=forced)


class DialProducerAgent(ProducerAgent):

    def __init__(self, model, machine):
        super().__init__(model, machine)
        self.priority_rank = 0
        self.priority_base = 1
    
    def priorities(self, wishes):
        keys = defaultdict(lambda:-1)
        i = self.priority_rank
        j = self.priority_base
        for p in wishes:
            key = p.start, p.end
            keys[key] += 1
            p.priority = abs((keys[key] % j)-i)
        return list(sorted(wishes, key=lambda p:p.priority))


class DialRegulatorAgent(RegulatorAgent):   

    CUSTOMER_CLASS = DialCustomerAgent
    PRODUCER_CLASS = DialProducerAgent

    def __init__(self, name, model, problem):
        super().__init__(name, model, problem)
        priority_base = len(self.producers)
        for i, producer in enumerate(self.producers):
            producer.priority_rank += i
            producer.priority_base = priority_base
        


