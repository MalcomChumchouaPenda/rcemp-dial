SELECT count(m.uid) as nb_mo, m.release_date, m.due_date, p.name 
FROM manufacturing_orders as m, problems as p
WHERE m.problem_id = p.uid
AND p.name like '%21'
GROUP BY m.release_date, m.due_date, p.name
ORDER BY p.name, m.release_date;