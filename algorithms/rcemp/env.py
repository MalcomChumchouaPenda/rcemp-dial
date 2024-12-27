
from typing import NamedTuple
from ..base import BasicEnv, BasicObject, BasicPosition


# ----------------------------------------------------
# NOTATIONS
# ----------------------------------------------------
# tid = task identifier
# sid = skill identifer
# aid = agent identifer
# rid = ressource identifier
# rmin = min release date
# dmax = max due date
#------------------------------------------------------


class Env(BasicEnv):
    
    def send_task(self, tid, task, wish):
        o = Object(tid, wish, task)
        self.plan.place_task(o, task)
        self[o.tid] = o
        return o.tid
    
    def read_wishes(self, capabilities):
        return [o.wish_pos.clone() 
                    for o in self.values() 
                        if o.sid in capabilities
                            and o.final_pos is None]
    
    def send_proposals(self, tid, proposal):
        o = self[tid]
        o.proposals.append(proposal)
    
    def read_proposals(self, aid):
        return {tid: list(o.proposals) 
                    for tid, o in self.items()
                        if o.aid == aid}
    
    def accept_proposal(self, tid, ep):
        o = self[tid]
        o.accepted = True
        o.proposals.clear()
        o.final_pos = ep 
    
    # def change_proposal(self, tid, fp):
    #     o = self[tid]
    #     o.final_pos = fp

    def validate_proposal(self, tid, ep):
        o = self[tid]
        o.accepted = True
        o.proposals.clear()
        o.final_pos = ep
        if ep.rid != 0:
            o.validated = True 
            self.plan.place_position(ep)

    def reject_proposals(self, tid, wp=None):
        o = self[tid]
        o.accepted = False
        o.validated = False 
        o.proposals.clear()
        o.wish_pos = wp 
        o.final_pos = None
        if wp is None:
            self.pop(tid)
            self.plan.remove_task(o)

    def read_validation(self, tid):
        if tid in self:
            o = self[tid]
            return o.validated, o.final_pos
        return None, None
    
    # def change_validation(self, tid, fp):
    #     o = self[tid]
    #     o.final_pos = fp
    #     self.plan.edit_position(fp)

    def apply_penality(self, tid,  penality):
        self[tid].final_pos.penality = penality
    
    def read_penality(self, tid):
        return self[tid].final_pos.penality


class Object(BasicObject):
    
    def __init__(self, tid, wp, task):
        super().__init__(tid)
        self.task = task
        self.wish_pos = wp
        self.final_pos = None
        self.proposals = []               # list of proposals
        self.accepted = False
        self.validated = False


class Position(BasicPosition):
    
    def __init__(self, tid, start=0, end=0, rid=0):
        super().__init__(tid, start=start, end=end, rid=rid)
        self.penality = 0                     # cost of externalities
    

class Proposal(NamedTuple):

    effective: Position
    potential: Position

    def __repr__(self):
        return f'Proposal({self.effective}; {self.potential})'
    
