# Judge audit

Calibration dùng nhãn replay trong hai CSV công khai, với `FAIL` là lớp dương. Các ngưỡng là κ ≥ 0,60, precision ≥ 0,80 và recall ≥ 0,70.

| Tiêu chí | n | TP / FP / FN / TN | κ | Precision | Recall | Tỉ lệ lỗi quan sát → hiệu chỉnh | Quyết định |
|---|---:|---|---:|---:|---:|---|---|
| tone_ok | 100 | 24 / 4 / 6 / 66 | 0,757 | 0,857 | 0,800 | 28% → 30% | Đạt, dùng cho giọng điệu |
| helpful | 100 | 9 / 0 / 21 / 70 | 0,375 | 1,000 | 0,300 | 9% → 30% | Không đạt, loại khỏi gate |

Chạy lại từ `src/`:

```bash
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

## Audit các ca bất đồng

| Case | Judge | Nhãn người | Phân xử và bằng chứng | Thay đổi rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Người đúng. Cách xưng “em” và kết câu “nha” quá suồng sã theo chuẩn hỗ trợ của bài. | Nêu ví dụ xưng hô chấp nhận được và ví dụ thân mật quá mức. |
| H-029 | PASS | FAIL | Người đúng. “Không cần nhắn thêm” mang giọng ra lệnh dù câu mở đầu có lời lịch sự. | Đánh giá cả câu trả lời và cho ví dụ về mệnh lệnh thiếu tôn trọng. |
| H-042 | FAIL | PASS | Người đúng. Reply ngắn, lịch sự và thông báo kết quả cùng thời gian tiền về. | Không bắt buộc xin lỗi trong thông báo hoàn tiền đã xử lý. |
| H-051 | FAIL | PASS | Người đúng. Từ “refund” nằm trong cách dùng được LogiX chấp nhận theo ghi chú. | Cho phép từ nghiệp vụ quen thuộc khi cả câu vẫn dễ hiểu. |
| H-070 | PASS | FAIL | Người đúng. Emoji cười không phù hợp với ngữ cảnh khiếu nại. | Thêm ví dụ emoji không phù hợp trong phản hồi khiếu nại. |
| H-081 | FAIL | PASS | Ghi chú CSV nghiêng về judge vì người gán nhãn đã đọc nhầm ticket. Cần xem ticket gốc để xác nhận. | Yêu cầu người gán nhãn đối chiếu đúng ticket và đưa ca bất đồng sang người duyệt thứ hai. |
| HL-015 | PASS | FAIL | Người đúng. Reply báo 55.000đ trong khi ledger ghi 40.000đ. | Chuyển kiểm số tiền sang grader so reply với ledger. |
| HL-016 | PASS | FAIL | Người đúng. Reply báo 55.000đ trong khi ledger ghi 35.000đ, dù lời xin lỗi rất lịch sự. | Chấm giọng điệu riêng. Số tiền đã hoàn phải khớp ledger. |

## Kết luận

Helpful bỏ sót 21 trên 30 lỗi theo nhãn người. Precision 1,000 đến từ 9 lần báo lỗi đều đúng, trong khi recall 0,300 và κ 0,375 thấp hơn ngưỡng. Tỉ lệ hiệu chỉnh Rogan–Gladen là thống kê tổng hợp và không sửa được phán quyết sai ở từng trial.

Tone đạt cả ba ngưỡng trên bộ replay. Giữ nguyên các CSV khi tái lập kết quả. Cần đánh giá lại rubric trên một bộ held-out mới có nhãn người và quy trình phân xử bất đồng trước khi dựa vào kết quả cho dữ liệu mới. Tiền và phê duyệt được kiểm bằng code.
