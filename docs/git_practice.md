# Tự phát triển qua Issue
Ba phần chưa triển khai: lọc người theo số ngày hoạt động tối thiểu; xuất lịch sử một người; thêm hình số lượt thử đến lần qua màn đầu. Chọn một Issue, viết tiêu chí và kiểm thử trước, giữ nguyên định nghĩa retention.
```powershell
git switch -c feature/min-active-days
git diff
python -m unittest discover -s tests -v
git add ten_file_da_sua
git commit -m "Add minimum active days filter"
git push -u origin feature/min-active-days
```
Tạo PR ghi Closes #số_issue khi đạt tiêu chí. Không commit DB, môi trường hoặc báo cáo. Các lệnh Git cần Git được cài; chạy phân tích không cần Git.
