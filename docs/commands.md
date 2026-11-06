# Tra lệnh
| Lệnh | Nhập ở đâu / ý nghĩa |
|---|---|
| `Get-Location` | PowerShell: xem thư mục hiện tại |
| `Get-ChildItem` | PowerShell: liệt kê file, phải thấy run_game.py |
| `cd "đường dẫn"` | PowerShell: đổi thư mục; không thêm /d |
| `python -m ...` | Chạy module Python, không phải SQL |
| `python src/prepare_data.py` | Tạo mẫu nếu chưa có DB, kiểm tra, xuất CSV |
| `python src/analyze.py` | Đối chiếu và xuất báo cáo |
| `python run_game.py --notebook` | Chuẩn bị môi trường, mở đúng bài học |
| `0`–`8` | Chỉ nhập trong menu |
| `SELECT ...` | Đặt trong chuỗi Python của read_sql ở notebook |

SELECT chọn cột, FROM chọn bảng, WHERE lọc dòng, JOIN nối quan hệ, COUNT DISTINCT đếm không trùng, GROUP BY gom nhóm, HAVING lọc nhóm, ORDER BY sắp xếp. NULL là chưa có/không xác định, khác 0. CTE đặt tên bước truy vấn; ROW_NUMBER đánh số trong nhóm; MIN tìm lần đầu.
