# Định nghĩa chỉ số
## Ngày và mốc
Tất cả giờ Asia/Ho_Chi_Minh. Một ngày hoạt động theo ngày bắt đầu phiên. Phiên qua nửa đêm chỉ thuộc ngày bắt đầu. Mốc là 23:59:59 của --as-of; phiên bắt đầu sau mốc không có trong báo cáo, phiên đang diễn ra được cắt thời lượng tại mốc. Lượt thử chưa kết thúc đến mốc không dùng kết quả tương lai.

## Nhóm ngày chơi đầu
Tìm MIN(date(started_at)) trên toàn bộ phiên đã bắt đầu đến mốc, **rồi mới lọc start/end**. Giữ người trong nhóm và mọi hoạt động của họ đến mốc, không cắt hoạt động tại end. Một dòng player_days là một người/ngày dù có nhiều phiên. Không JOIN trực tiếp chi tiết lượt thử rồi đếm phiên.

## Retention đúng ngày
D7 của người chơi đầu 01/01 là hoạt động ngày 08/01. Hoạt động 09/01 không thay thế D7. Người đủ 7 ngày khi cohort_date+7 <= as_of. Tỷ lệ tổng = tổng người quay lại / tổng người đủ thời gian, không AVG tỷ lệ từng nhóm. Người mới chưa đủ thời gian không coi là không quay lại. Không có mẫu số giữ tỷ lệ NULL; đủ mẫu nhưng không quay lại = 0%. D0 = 100% cho nhóm có người. D1/D7/D30 tổng có mẫu số khác nhau; không so như thể cùng một nhóm cố định. Heatmap có ô xám/trống cho chưa quan sát, 0% vẫn là ô có dữ liệu.

## Tiến độ màn
Mỗi người/màn chỉ đếm một lần đã thử và một lần hoàn thành, nhưng giữ mọi lượt thử lặp. Xếp các lượt theo started_at/attempt_id. Trung vị attempts_to_first_complete chỉ tính người đã qua, gồm lần thành công và các lần trước nó, không cộng các lượt chơi lại sau thành công. Chưa qua không gán 0 lần hoặc kết luận bỏ game. Không có người thử thì tỷ lệ qua để trống. Không suy màn gây ra việc bỏ game.

## Chất lượng và phạm vi
Validate toàn DB trước báo cáo: FK, ngày/giờ, chồng phiên, containment, kết quả, thứ tự mở màn. Lỗi thì dừng **trước khi ghi đầu ra mới**. Metadata GIẢ LẬP bắt buộc. SQL và pandas tổng hợp độc lập cùng bảng nguồn. quality.csv toàn DB, các bảng khác theo nhóm/mốc.
