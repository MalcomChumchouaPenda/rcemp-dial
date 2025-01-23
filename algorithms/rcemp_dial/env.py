

from ..rcemp.env import Env, Object


class DialEnv(Env):

    def send_pause(self, tid, task, pos):
        # print('place', tid)
        o = Object(tid, pos, task)
        o.accepted = True
        o.validated = True
        o.final_pos = pos
        self[o.tid] = o
        self.plan.place_task(o, task)
        self.plan.place_position(pos)