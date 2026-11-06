# Lời giải — đọc sau khi tự làm

## 1. Xem 10 người chơi đầu

```sql
SELECT * FROM players ORDER BY player_id LIMIT 10;
```

## 2. Xem 10 phiên mới nhất

```sql
SELECT * FROM sessions ORDER BY started_at DESC,session_id DESC LIMIT 10;
```

## 3. Lọc phiên tháng 2

```sql
SELECT session_id,player_id,started_at,ended_at FROM sessions WHERE started_at >= '2026-02-01' AND started_at < '2026-03-01' ORDER BY started_at,session_id LIMIT 10;
```

## 4. Hiện tên người và màn

```sql
SELECT p.name,s.session_id,l.name AS level,a.result FROM level_attempts a JOIN sessions s USING(session_id) JOIN players p USING(player_id) JOIN levels l USING(level_id) LIMIT 10;
```

## 5. Đếm phiên và người mỗi ngày

```sql
SELECT date(started_at) AS activity_date,COUNT(*) AS session_count,COUNT(DISTINCT player_id) AS active_players FROM sessions GROUP BY date(started_at) ORDER BY activity_date;
```

## 6. Tìm người nhiều phiên/ngày

```sql
SELECT player_id,date(started_at) AS day,COUNT(*) AS sessions FROM sessions GROUP BY player_id,day HAVING COUNT(*)>1 LIMIT 10;
```

## 7. Tìm ngày chơi đầu

```sql
WITH firsts AS (SELECT player_id,MIN(date(started_at)) AS cohort_date FROM sessions GROUP BY player_id) SELECT cohort_date,COUNT(*) AS players FROM firsts GROUP BY cohort_date ORDER BY cohort_date;
```

## 8. Ngày phải quay lại để đạt D7

```sql
WITH firsts AS (SELECT player_id,MIN(date(started_at)) AS first_day FROM sessions GROUP BY player_id) SELECT player_id,first_day,date(first_day,'+7 days') AS target_d7 FROM firsts LIMIT 10;
```

## 9. Tìm người chưa từng thử màn

```sql
SELECT p.player_id,p.name FROM players p WHERE EXISTS(SELECT 1 FROM sessions s WHERE s.player_id=p.player_id) AND NOT EXISTS(SELECT 1 FROM sessions s JOIN level_attempts a USING(session_id) WHERE s.player_id=p.player_id);
```

## 10. Giữ màn chưa có người thử

```sql
SELECT l.name,COUNT(a.attempt_id) AS attempts FROM levels l LEFT JOIN level_attempts a USING(level_id) GROUP BY l.level_id ORDER BY l.level_order;
```

## 11. Tính retention D7 đúng mẫu

```sql
-- Chạy OVERALL từ game_lab.analysis, lọc day_offset=7. Đủ tuổi khi cohort_date+7 <= as_of; numerator chỉ đúng ngày đó.
```

## 12. Phân biệt 0 với chưa quan sát

```sql
-- COHORT trả NULL returned khi chưa đủ ngày; eligible=0. Đủ ngày, không ai quay lại thì returned=0 và rate=0%.
```

## 13. So tổng tỷ lệ với AVG nhóm

```sql
-- SUM(returned_players)/SUM(eligible_players)*100 trên cùng day_offset; không AVG tỷ lệ các cohort khác kích thước.
```

## 14. Người hoàn thành từng màn

```sql
SELECT l.name,COUNT(DISTINCT CASE WHEN a.result='completed' THEN s.player_id END) AS completed_players FROM levels l LEFT JOIN level_attempts a USING(level_id) LEFT JOIN sessions s USING(session_id) GROUP BY l.level_id ORDER BY l.level_order;
```

## 15. Lần thành công đầu

```sql
WITH ranked AS (SELECT s.player_id,a.level_id,a.result,ROW_NUMBER() OVER(PARTITION BY s.player_id,a.level_id ORDER BY a.started_at,a.attempt_id) AS attempt_number FROM level_attempts a JOIN sessions s USING(session_id)) SELECT player_id,level_id,MIN(CASE WHEN result='completed' THEN attempt_number END) AS attempts_to_first_complete FROM ranked GROUP BY player_id,level_id LIMIT 20;
```

## 16. Phiên qua nửa đêm

```sql
SELECT * FROM sessions WHERE date(started_at)<>date(ended_at) ORDER BY started_at LIMIT 20;
```

## 17. Thử lại sau khi qua màn

```sql
WITH done AS (SELECT s.player_id,a.level_id,MIN(a.ended_at) AS first_complete FROM level_attempts a JOIN sessions s USING(session_id) WHERE result='completed' GROUP BY s.player_id,a.level_id) SELECT a.attempt_id,s.player_id,a.level_id FROM level_attempts a JOIN sessions s USING(session_id) JOIN done d ON d.player_id=s.player_id AND d.level_id=a.level_id WHERE a.started_at>=d.first_complete LIMIT 20;
```

## 18. JOIN sai cấp có làm tăng phiên?

```sql
SELECT COUNT(*) AS joined_rows,COUNT(DISTINCT s.session_id) AS sessions FROM sessions s JOIN level_attempts a USING(session_id);
```

## 19. Đối chiếu pandas

```sql
-- compare(db) tự đọc bảng gốc, đối chiếu cả 5 bảng. Thử nhóm tháng 1 với as_of 31/03, rồi giải thích vì sao giữ hoạt động tháng 2/3.
```

## 20. Ba nhận xét

```sql
-- Mỗi nhận xét có số liệu, kỳ nhóm, mốc và mẫu số. Không dùng giả lập kết luận game thật hoặc suy nguyên nhân.
```