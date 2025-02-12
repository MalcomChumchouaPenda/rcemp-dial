SELECT m.name, x.start_time, x.end_time, p.name, 
       o.name, o.release_date, o.due_date
FROM positions as x, experiments as e, problems as p,
     production_tasks as t, routings as r, manufacturing_orders as o,
     ressources as m
WHERE x.exp_id = e.uid
AND e.problem_id = p.uid
AND x.task_id = t.uid
AND t.routing_id = r.uid
AND r.order_id = o.uid
AND x.ressource_id = m.uid
AND X.end_time > o.due_date
ORDER BY p.name, o.release_date, x.start_time
;