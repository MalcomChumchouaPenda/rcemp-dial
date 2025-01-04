
import os
import functools as fct
from operator import itemgetter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colormaps as cmp
from matplotlib.patches import Patch
import graphviz as gviz
from scipy import stats

from config import RESULT_DIR
from utils import constants as cst
from benchmarks.databases import Db
# from benchmarks import schemas as sch


# CUR_DIR = os.path.dirname(os.path.abspath(__file__))
# LIB_DIR = os.path.dirname(CUR_DIR)
# ROOT_DIR = os.path.dirname(LIB_DIR)
# print(ROOT_DIR)
# FIG_DIR = os.path.join(LIB_DIR, 'figures')
# TBL_DIR = os.path.join(LIB_DIR, 'tables')
FIG_DIR = TBL_DIR = RESULT_DIR


class View:
    
    def __init__(self, benchmark_id, db_type, echo=False):
        super().__init__()
        dbcls = cst.DATABASES[db_type]
        self.db = dbcls(benchmark_id, verbose=echo)
        
    def load_results(self, sql):
        engine = self.db.engine
        connection = engine.connect()
        return pd.read_sql(sql, connection)
    
    
class GanttView(View):

    GANTT_WIDTH = 12
    GANTT_UNIT_HEIGHT = 0.15
    GANT_MIN_HEIGHT = 2
    GANTT_TF_THEME = 'winter'
    GANTT_TM_THEME = 'autumn'

    COLOR_COMPETENCIES = 0
    COLOR_TASKS = 1
    COLOR_JOBS = 2

    # _TASK_COLORS = {'TF':'C0', 'TD':'C1', 'TM':'C2'}
    # _C = cmp.get_cmap('Pastel2')
    # _TASK_COLORS = {'TF':_C(0), 'TD':'#d671b1', 'TM':'#71bf6e'}
    # _TASK_LABELS = {'Production task':'#658cb5', 'Tardy Task':'#d671b1', 'Maintenance Task':'#71bf6e'}
    _TASK_LABELS = (('Production task','TF'), ('Tardy Task','TD'), ('Maintenance Task','TM'))


    def plot(self, problem_filter, model_filter, title_format=None, time_window=None, saveas=None):
        fig, axes, exps = self._build_figure(problem_filter, model_filter)
        if fig is None:
            return 'No figure'
        for ax, exp in zip(axes, exps):
            data = self._build_data(exp, time_window=time_window)
            if data.shape[0] == 0:
                continue
            self._build_gantt(data, ax, exp, title_format=title_format, time_window=time_window)
        self._render_view(fig, saveas=saveas)
    
    def _build_figure(self, problem_filter, model_filter):
        sql = f"""
                select exp.uid as exp_id, pb.uid as pb_id,
                pb.name as problem_name, exp.model_name,
                count(res.uid) as count_ressource
                from problems pb, experiments as exp,
                (select ma.uid, ma.problem_id
                from machines as ma
                union select mr.uid, mr.problem_id
                from maintenance_ressources as mr) as res
                where pb.uid = exp.problem_id
                and exp.problem_id = res.problem_id
                and pb.name like '{problem_filter}'
                and exp.model_name like '{model_filter}'
                group by exp.uid, pb.uid, pb.name, exp.model_name
                order by pb.name, exp.model_name desc, exp.uid"""
        experiments = self.load_results(sql).to_dict('records')
        experiments.sort(key=itemgetter('problem_name'))
        count_experiment = len(experiments)
        count_ressources = max([r['count_ressource'] for r in experiments])
        if count_experiment == 0:
            return None, None, None
        elif count_experiment == 1:
            width = self.GANTT_WIDTH
            height = int(self.GANTT_UNIT_HEIGHT * count_ressources)
            height = max(height, self.GANT_MIN_HEIGHT)
            fig, ax = plt.subplots(1, 1, figsize=(width, height))
            return fig, [ax], experiments
        else:
            width = self.GANTT_WIDTH
            height = int(self.GANTT_UNIT_HEIGHT * count_ressources * count_experiment)
            height = max(height, self.GANT_MIN_HEIGHT * count_experiment)
            fig, axes = plt.subplots(count_experiment, 1, figsize=(width, height))
            return fig, axes, experiments

    def _build_data(self, experiment, time_window=None):
        date_filter = ''
        if time_window:
            date_filter = f'''and (pos.start_time <= {time_window[1]}
                and pos.end_time >= {time_window[0]})
                '''
        sql1 = f"""select mo.name as jname, pos.start_time as sdate, 
                pos.end_time as edate, ma.name as rname, 'TF' as flag
                from experiments as exp, positions as pos,
                manufacturing_orders as mo, routings as ro,
                production_tasks as tf, ressources as ma
                where exp.uid = pos.exp_id
                and pos.task_id = tf.uid
                and tf.routing_id = ro.uid
                and ro.order_id = mo.uid
                and pos.ressource_id = ma.uid
                and pos.end_time <= mo.due_date
                and exp.uid = '{experiment['exp_id']}'
                {date_filter}
                union
                select mo.name as jname, pos.start_time as sdate, 
                pos.end_time as edate, ma.name as rname, 'TD' as flag
                from experiments as exp, positions as pos,
                manufacturing_orders as mo, routings as ro,
                production_tasks as tf, ressources as ma
                where exp.uid = pos.exp_id
                and pos.task_id = tf.uid
                and tf.routing_id = ro.uid
                and ro.order_id = mo.uid
                and pos.ressource_id = ma.uid
                and pos.end_time > mo.due_date
                and exp.uid = '{experiment['exp_id']}'
                {date_filter}
                union 
                select mr.name as jname, pos.start_time as sdate, 
                pos.end_time as edate, ma.name as rname, 'TM' as flag
                from experiments as exp, positions as pos,
                ressources as ma, devices as dv, maintenance_tasks as tm,
                ressources as mr
                where exp.uid = pos.exp_id
                and pos.task_id = tm.uid
                and tm.device_id = dv.uid
                and dv.machine_id = ma.uid
                and pos.ressource_id = mr.uid
                and exp.uid = '{experiment['exp_id']}'
                {date_filter}"""
        data = self.load_results(sql1) 
        if time_window:
            data['sdate'] = data['sdate'].apply(lambda val: max(time_window[0], val))  
            data['edate'] = data['edate'].apply(lambda val: min(time_window[1], val))      
        return data
    
    def _build_gantt(self, data, ax, experiment, title_format=None, time_window=None):
        sql1 = f"""select mo.name
                from manufacturing_orders as mo, 
                problems as pb, experiments as exp
                where mo.problem_id=pb.uid
                and exp.problem_id=pb.uid
                and exp.uid = '{experiment['exp_id']}'
                order by mo.name;"""
        sql2 = f"""select r.name
                from maintenance_ressources as mr, ressources as r, 
                problems as pb, experiments as exp
                where mr.uid=r.uid 
                and mr.problem_id=pb.uid
                and exp.problem_id=pb.uid
                and exp.uid = '{experiment['exp_id']}'
                order by r.name;"""
        sql3 = f"""select r.name
                from machines as ma, ressources as r, 
                problems as pb, experiments as exp
                where ma.uid=r.uid 
                and ma.problem_id=pb.uid
                and exp.problem_id=pb.uid
                and exp.uid = '{experiment['exp_id']}'
                order by r.name;"""
        mo_names = self.load_results(sql1)
        mo_names = list(mo_names['name'])
        mr_names = self.load_results(sql2)
        mr_names = list(mr_names['name'])
        ma_names = self.load_results(sql3)
        ma_names = list(ma_names['name'])

        # defaults
        i = data.shape[0]
        data = data.copy()
        unique_names = data['rname'].unique()
        for ma_name in ma_names:
            if ma_name not in unique_names:
                i += 1
                data.loc[i, 'rname'] = ma_name
                data.loc[i, 'sdate'] = np.nan
                data.loc[i, 'edate'] = np.nan
                data.loc[i, 'jname'] = ''

        # colors
        colormap = cmp.get_cmap('tab20')
        # mo_cmap = self._get_cmap(len(mo_names), name=self.GANTT_TF_THEME)
        # mr_cmap = self._get_cmap(len(mr_names), name=self.GANTT_TM_THEME)
        # colors = {jname:mo_cmap(i) for i,jname in enumerate(mo_names)}
        # colors.update({jname:mr_cmap(i) for i,jname in enumerate(mr_names)})
        # color = fct.partial(self._get_color, colors)
        bar_colors = {k:colormap(i) for i,(_, k) in enumerate(self._TASK_LABELS)}
        text_colors = {k:colormap(i) for i,(k, _) in enumerate(self._TASK_LABELS)}
        color = lambda flag: bar_colors.get(flag, 'w')
        data['color'] = data['flag'].apply(color)
        
        # bars
        data['duration'] = data['sdate'] - data['edate']
        data = data.sort_values('rname', ascending=False)
        ax.barh(data.rname, data.duration, left=data.edate, color=data.color)

        # limits
        if time_window is None:
            ax.set_xlim(0, max(data['edate'].fillna(0)) + 1)
        else:
            ax.set_xlim(*time_window)
        ax.set_yticks(sorted(ma_names) + [' '])
        
        # texts
        # rnames = data['rname'].unique()
        # idxp = {rname:i for i, rname in enumerate(rnames)}
        # for _ , row in data.iterrows():
        #     text = f'{row.jname}'
        #     ax.text(row.sdate+0.2, idxp[row.rname], text, va='center')
    
        # legends, title and filepath
        # labels = self._TASK_LABELS
        legends = [Patch(facecolor=color, label=label)  for  label, color in text_colors.items()]
        ax.legend(handles=legends, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        if title_format:
            title = title_format(experiment)
            ax.set_title(title)

    
    def _render_view(self, figure, saveas=None):        
        plt.tight_layout()
        if saveas:
            imgpath = os.path.join(FIG_DIR, saveas)
            figure.savefig(imgpath)
        plt.show()


    @classmethod
    def _get_cmap(cls, n, name='hsv'):
        return plt.cm.get_cmap(name, n)
    
    # @classmethod
    # def _get_color(cls, colors, jname):
    #     if jname == '':
    #         return 'w'
    #     return colors[jname]



class StatsView(View):

    def compare(self, method1, method2, stat_names, problem_filter=None, 
                instance_pattern=None, save_as=None, by_method=True):
        stat_filter = ', '.join(f"'{n}'" for n in stat_names)
        pb_filter = '' if problem_filter is None else f"and p.name like '{problem_filter}'"
        sql = f"""select p.uid, p.name as problem_name, e.model_name, 
                s.name as var_name, s.value 
                from statistics s, problems p, experiments e
                where s.exp_id = e.uid and e.problem_id = p.uid
                and e.model_name in ('{method1}', '{method2}')
                and s.name in ({stat_filter})
                {pb_filter}
                order by p.uid, p.name, s.name, s.value;"""
        data = self.load_results(sql)
        data = self._extract_instances(data, instance_pattern)
        data = self._build_statistics(data, by_method)
        self._save_data(data, save_as)
        return data

    def _extract_instances(self, data, instance_pattern):
        if instance_pattern:
            data['instance_name'] = data['problem_name'].str.findall(instance_pattern)
            data['instance_name'] = data['instance_name'].str[0]
        else:
            data['instance_name'] = data['problem_name']
        return data
    
    def _build_statistics(self, data, by_method):
        cols = ['model_name', 'var_name'] if by_method else ['var_name', 'model_name']
        data = data.pivot_table(index='instance_name', columns=cols,
                                values='value', aggfunc='mean')
        average = data.mean().reset_index()
        cols = list(average.columns)
        cols[-1] = 'average'
        average.columns = cols
        average = average.pivot_table(columns=cols[:-1], values=cols[-1])
        return pd.concat([data, average])

    def _save_data(self, data, save_as):
        if save_as:
            datapath = os.path.join(TBL_DIR, save_as)
            data.to_csv(datapath, sep=';')


    def test(self, stat_names, problem_filter=None, save_as=None):
        stat_filter = ', '.join(f"'{n}'" for n in stat_names)
        pb_filter = '' if problem_filter is None else f"and p.name like '{problem_filter}'"
        sql = f"""select p.uid, p.name as problem_name, e.model_name, 
                s.name as var_name, s.value 
                from statistics s, problems p, experiments e
                where s.exp_id = e.uid and e.problem_id = p.uid
                and s.name in ({stat_filter})
                {pb_filter}
                order by p.uid, p.name, s.name, s.value;"""
        data = self.load_results(sql)
        outputs = []
        for name, inputs in data.groupby('var_name'):
            inputs = inputs.pivot_table(index='problem_name', 
                                        columns=['model_name'], 
                                        values='value', 
                                        aggfunc='mean')
            if inputs.shape[1] < 2:
                return 'Insufficient column'
            x1 = inputs.iloc[:,0]
            x2 = inputs.iloc[:,1]
            output = stats.wilcoxon(x1, x2, alternative='two-sided')
            outputs.append(dict(var_name=name, 
                                stat_val=output.statistic,
                                p_value=output.pvalue))
        data = pd.DataFrame(outputs)
        self._save_data(data, save_as)
        return data


class MachinesView(View):
    
    def plot(self, problem, title=''):
        gp = gviz.Graph(title, strict=True)
        for machine in problem.machines:
            gm = gviz.Graph(machine.uid)
            self._plot_machine(gm, machine)
            gp.subgraph(gm)
        return gp

    def _plot_machine(self, graph, machine):
        graph.node(machine.uid, shape='oval')
        for comp in machine.competencies:
            self._plot_competency(graph, comp, machine.uid)

    def _plot_competency(self, graph, competency, parent_id):
        graph.node(competency.uid, competency.activity, shape='box')
        graph.edge(parent_id, competency.uid)
        function = competency.function
        if function is not None:
            self._plot_function(graph, function, competency.uid)
    
    def _plot_function(self, graph, function, parent_id):
        graph.node(function.uid, function.name, shape='box')
        graph.edge(parent_id, function.uid)
        decision = 'or' if function.redundant else 'and'
        j = len(function.children)
        if j == 0:
            k = len(function.devices)
            if k == 1:
                decision_id = function.uid
            else:
                decision_id = function.uid + decision
                graph.node(decision_id, decision, shape='diamond')
                graph.edge(function.uid, decision_id)
            for device in function.devices:
                self._plot_device(graph, device, decision_id)

        elif j == 1:
            child = function.children[0]
            self._plot_function(graph, child, function.uid)
            
        else:
            decision_id = function.uid + decision
            graph.node(decision_id, decision, shape='diamond')
            graph.edge(function.uid, decision_id)
            for child in function.children:
                self._plot_function(graph, child, decision_id)

    def _plot_device(self, graph, device, parent_id):
        graph.node(device.uid, device.name, shape='oval')
        graph.edge(parent_id, device.uid)

