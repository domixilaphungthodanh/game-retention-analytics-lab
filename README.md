# Game Retention Analytics Lab

Học SQL qua **người chơi, phiên và lượt thử màn GIẢ LẬP**. Repo Public, mã MIT. Menu chỉ tra cứu bộ mẫu, không tải thông tin người chơi thật.

## Bắt đầu trên Windows PowerShell

Tải ZIP ở [Releases](https://github.com/domixilaphungthodanh/game-retention-analytics-lab/releases), giải nén toàn bộ. Mở thư mục dự án trong File Explorer, gõ `powershell` trên thanh địa chỉ rồi Enter. Máy cần **Python 3.12**, mạng lần cài thư viện đầu; không cần Git. Đây chưa phải EXE độc lập.

```powershell
Get-Location
Get-ChildItem
python src/prepare_data.py
python src/analyze.py
python run_game.py --notebook
```

Phải thấy `run_game.py` và thư mục `src`. Nếu đang ở `system32` hoặc `C:\Users\...`, đổi thư mục trước bằng `cd "đường dẫn thư mục dự án"`. **Không dùng `cd /d` trong PowerShell.** Không gõ phần `PS ...>`.

Mở **notebooks/02_analysis.ipynb**, nhấn **Shift+Enter** từng ô từ trên xuống. Nếu thấy tab Running trống, chọn Files → notebooks → 02_analysis.ipynb. Giữ PowerShell mở khi học; Ctrl+C để dừng server. Launcher mở notebook trực tiếp bằng `python -m notebook`, cố định đúng thư mục gốc.

Menu đọc dữ liệu:
```powershell
python run_game.py
```
Trong menu nhập số 0–8; khi chọn người, nhập **số thứ tự kết quả**, không cần nhớ mã. `n/p` đổi trang, `q` quay lại. Có hai file nhấp đúp START_WINDOWS.cmd và START_NOTEBOOK.cmd. Môi trường Windows đặt ở đường dẫn ngắn trong LOCALAPPDATA; không cần Administrator, không yêu cầu tắt bảo mật. Sau thiết lập có thể chạy offline. Dữ liệu không tự đồng bộ giữa máy.

## Đọc gì trước?
1. [Từ điển dữ liệu](docs/data_dictionary.md): mỗi dòng đại diện cho gì?
2. [Chỉ số và mẫu số](docs/metrics.md): D7, 0% và chưa quan sát được khác nhau thế nào?
3. Notebook tổng hợp: bảng → SQL → pandas → biểu đồ → ba nhận xét.
4. Tám bài chuyên sâu trong notebooks/lessons; [20 bài tập](docs/exercises.md) trước khi mở [lời giải](docs/solutions.md).
5. [Thực hành Git](docs/git_practice.md) và [bảng tra lệnh](docs/commands.md).

## Dữ liệu học tập
Seed **42**, 3.000 người, 10 màn tuần tự, lịch sử 01/01–31/03/2026; mốc cuối 31/03/2026 23:59:59, **Asia/Ho_Chi_Minh**. Mẫu tái lập gồm **24.837 phiên, 52.274 lượt thử**, 597 phiên qua nửa đêm. Tên, tỷ lệ, tần suất và độ khó đều giả lập, không đại diện game thật.

Một người có thể nhiều phiên/ngày. Ngày hoạt động = ngày bắt đầu phiên; không cộng thêm ngày khi qua nửa đêm. Ngày chơi đầu = ngày phiên đầu. Dn là quay lại **đúng ngày** đầu+n, không phải bất kỳ ngày sau đó. Người chưa đủ n ngày không vào mẫu số. Thời lượng phiên không khẳng định toàn bộ là thời gian chơi tích cực. Chưa hoàn thành màn không có nghĩa bỏ game.

## Chọn nhóm và mốc
```powershell
python src/analyze.py --start 2026-01-01 --end 2026-01-31 --as-of 2026-03-31
python src/prepare_data.py --db database/practice.db
python run_game.py --notebook --db database/practice.db
python src/analyze.py --db database/practice.db --as-of 2026-02-28 --out outputs/february
```
`--start/--end` chọn **ngày chơi đầu**, không cắt các lần quay lại sau ngày end. `--as-of` quan sát đến cuối ngày. Mặc định start=01/01, as-of=31/03, end bằng as-of nếu bỏ trống. Chỉ nhận 01/01 ≤ start ≤ end ≤ as-of ≤ 31/03/2026. `--db` chọn SQLite; `--out` chọn nơi xuất. Phạm vi không có người vẫn xuất báo cáo, tỷ lệ trống khi mẫu số 0.

Prepare không ghi đè DB. Chạy lại kiểm tra và xuất CSV nguồn từ DB đang có; `--raw-out` đổi nơi CSV. Nhập vào DB tạm, kiểm tra xong mới công bố. Database mặc định database/game.db.

## Kết quả và cấu trúc
4 PNG: DAU, retention D1/D7/D30, heatmap nhóm D0–D30, số người thử/qua màn. 6 CSV: player_days, daily, retention, cohorts, levels, quality. report.md có ba nhận xét, kỳ, mốc, mẫu số và giới hạn. quality kiểm tra **toàn DB**; các bảng phân tích theo nhóm/mốc đã chọn. SQL và pandas tính độc lập từ bảng gốc, đếm/thời lượng giây khớp chính xác; tỷ lệ/trung vị sai số tối đa 1e-8.

```text
src/            Hai script chuẩn bị/phân tích
game_lab/       Mẫu, kiểm tra, SQL, pandas, menu, báo cáo
sql/            Schema và truy vấn mẫu
notebooks/      02_analysis.ipynb + 8 bài SQL
docs/           Sơ đồ, từ điển, chỉ số, bài tập, lời giải
tests/          Fixture nhỏ ghi rõ giả lập
data/raw/       CSV sinh ra, bỏ qua Git/ZIP
database/       SQLite, bỏ qua Git/ZIP
outputs/        Báo cáo, bỏ qua Git/ZIP
```

## Cài thủ công và kiểm thử
```powershell
python -m pip install -r requirements.txt
python -m game_lab.prepare_data
python -m game_lab.cli
python -m game_lab.analyze
python -m notebook
python -m unittest discover -s tests -v
python -m game_lab.execute_notebooks
```
Notebook phân tích mở DB chỉ đọc; bài ghi dùng SQLite tạm. Không sửa/xóa phiên qua menu. Actions chạy kiểm thử Windows/Linux; workflow thủ công tạo mẫu, phân tích và chạy 9 notebook, giữ artifact 14 ngày. ZIP không chứa DB, CSV sinh ra, môi trường hoặc notebook đã chạy. Chỉ mã/tài liệu/notebook nguồn/bộ kiểm thử được đưa lên GitHub.
