SELECT m.name, x.start_time, x.end_time, p.name
FROM positions as x, experiments as e, problems as p,
     maintenance_tasks as t, ressources as m
WHERE x.exp_id = e.uid
AND e.problem_id = p.uid
AND x.task_id = t.uid
AND x.ressource_id = m.uid
ORDER BY p.name, x.start_time, m.name