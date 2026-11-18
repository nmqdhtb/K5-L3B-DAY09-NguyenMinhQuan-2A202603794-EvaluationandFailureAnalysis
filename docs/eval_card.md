# Eval card — LogiX-VN refund agent

Card này đi kèm mỗi báo cáo và được dùng lại ở Day 10.

- **Run ID / eval set SHA:**
- **Phiên bản:** code (commit) … · eval set v1 (sha …) · metric_spec … · grader (commit) … · seeds 11/22/33/44/55
- **Eval set:** v1, 14 item × 5 seed, nguồn lab8_public; nhãn: labels_v1.json
- **Metric & ngưỡng:** (trích metric_spec.yaml)
- **Kết quả baseline vs PR:** bảng + paired CI
- **Judge:** tone_ok κ=…, P=…, R=…; helpful bị loại vì …
- **Trace case:** link `docs/trace_case.md`, bước sai đầu tiên, regression test
- **Gate owner:** ai xử lý khi gate exit 1
- **Phạm vi pilot:** …
- **Giới hạn / bằng chứng còn thiếu:** MockLLM, 14 item, judge replay; không đo trên người dùng thật
- **Khi nào tăng eval-set version:** …

## v2 — Kiểm tra slice (M5)

Eval set SHA `cd109a409671` gồm 14 claim v1 và 14 claim adversarial, chạy 5 seed cho mỗi item. Baseline là `E-swarm-20261118-cd10`.

| Lượt chạy | pass_rate toàn bộ | money_movement | adversarial | Gate |
|---|---:|---:|---:|---|
| swarm | 98,57% | 100% | 97,14% | Baseline |
| fixed | 100% | 100% | 100% | Qua |
| honest_refactor | 100% | 100% | 100% | Qua |
| slice_regression | 93,57% | 85,00% | 91,43% | Chặn tại money_movement |

`slice_regression` đạt sàn tổng 85% và CI 95% của chênh lệch tổng là [−12,1; +2,9] điểm phần trăm. Slice `money_movement` giảm từ 100% xuống 85%, dưới sàn 90%. Slice `adversarial` kiểm riêng các claim trong pack, với sàn 85%. Cả hai slice chặn nếu CI của chênh lệch so với baseline nằm hoàn toàn dưới 0. Đánh giá độ ổn định theo A/A và chọn sàn `pass_hat_5` ở M6.

## v2 — Độ ổn định theo seed (M6)

A/A chạy cùng `swarm` với hai bộ seed `11,22,33,44,55` và `66,77,88,99,110`. Tất cả metric có Δ = 0 trên hai bộ này. Mỗi bộ có `pass_rate` 97,86%, `pass@5` 100% và `pass_hat_5` 89,29%. Chọn sàn chặn `pass_hat_5` = 80%, thấp hơn 9,29 điểm phần trăm so với cả hai quan sát A/A.

`flaky_regression` đạt `pass_rate` 91,43%, trên sàn tổng 85%, và `pass@5` 100%. Tuy nhiên chỉ 57,14% item đạt cả 5 lượt, nên `pass_hat_5` chặn độc lập. Trong lần chạy này, CI của `pass_rate` và slice `money_movement` cũng chặn. Scorecard v2 chặn 3/3 regression và cho qua cả hai variant đối chứng.

MockLLM tái lập được kết quả với cấu hình cố định. Hai bộ seed trên chỉ cho biết nhiễu quan sát trong phép đo này. Với LLM thật, sampling và biến động của dịch vụ có thể tạo chênh lệch A/A. Cần thêm lượt đo trước khi dùng sàn cho model thật. Năm seed không đủ để phát hiện ổn định lỗi có xác suất xuất hiện 1/3 mỗi lượt. Với giả định các lượt độc lập, xác suất cả 5 lượt bỏ sót là (2/3)^5, khoảng 13%.
