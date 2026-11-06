-- Bảng, dòng và khóa
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Lọc và sắp xếp
SELECT session_id,player_id,started_at,ended_at FROM sessions WHERE started_at >= '2026-02-01' AND started_at < '2026-03-01' ORDER BY started_at,session_id LIMIT 10;

-- JOIN và cấp dữ liệu
SELECT p.name,s.session_id,l.name AS level,a.result FROM level_attempts a JOIN sessions s USING(session_id) JOIN players p USING(player_id) JOIN levels l USING(level_id) LIMIT 10;

-- Đếm người khác đếm phiên
SELECT date(started_at) AS activity_date,COUNT(*) AS session_count,COUNT(DISTINCT player_id) AS active_players FROM sessions GROUP BY date(started_at) ORDER BY activity_date;

-- Ngày chơi đầu và nhóm
WITH firsts AS (SELECT player_id,MIN(date(started_at)) AS cohort_date FROM sessions GROUP BY player_id) SELECT cohort_date,COUNT(*) AS players FROM firsts GROUP BY cohort_date ORDER BY cohort_date;

-- Lần hoàn thành đầu và transaction
WITH ranked AS (SELECT s.player_id,a.level_id,a.result,ROW_NUMBER() OVER(PARTITION BY s.player_id,a.level_id ORDER BY a.started_at,a.attempt_id) AS attempt_number FROM level_attempts a JOIN sessions s USING(session_id)) SELECT player_id,level_id,MIN(CASE WHEN result='completed' THEN attempt_number END) AS attempts_to_first_complete FROM ranked GROUP BY player_id,level_id LIMIT 20;

-- pandas, biểu đồ và Git
SELECT COUNT(*) AS sessions,COUNT(DISTINCT player_id) AS players FROM sessions;