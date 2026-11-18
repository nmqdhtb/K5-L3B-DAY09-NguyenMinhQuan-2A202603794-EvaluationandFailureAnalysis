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
