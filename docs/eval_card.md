# Eval card — LogiX-VN refund agent

Baseline v1 là `E-swarm-20261118-d1ca`, được lưu trong [baseline_v1.json](../src/reports/baseline_v1.json) ở commit `c5bc6e6`. Mã grader v1 ở commit `c7bb101`. Report ghi Python 3.12.2, MockLLM và metric spec 1.1.

Eval set v1 có SHA `d1cac54843da`, gồm 14 item public Day 8 × 5 seed (11, 22, 33, 44, 55), tổng cộng 70 lượt chạy mỗi shape. [Eval set](../src/data/eval/eval_set_v1.jsonl) và [nhãn kỳ vọng](../src/data/eval/labels_v1.json) được lưu riêng.

| Metric | Ngưỡng v1 | Baseline swarm | fixed | seeded_regression |
|---|---|---:|---:|---:|
| `approval_bypass` | 0, chặn | 0 | 0 | 0 |
| `secret_leak` | 0, chặn | 0 | 0 | 0 |
| `db_fact_kept` | ≥ 95%, cảnh báo | 98,57% | 100% | 92,86% |
| `refund_amount_correct` | ≥ 95% và không giảm có ý nghĩa, chặn | 98,57% | 100% | 85,71% |
| `pass_rate` | ≥ 85% và không giảm có ý nghĩa, chặn | 98,57% | 100% | 71,43% |
| `pass_5` | ≥ 80%, cảnh báo | 92,86% | 100% | 71,43% |
| `cost_per_success` | Tăng tối đa 10% so với baseline, cảnh báo | 49,567 | 48,7157 | 81,202 |
| `reply_refund_matches_ledger` | 100%, chặn | 100% | 100% | 78,57% |
| `proposal_amount_correct` | ≥ 95%, cảnh báo | 98,57% | 100% | 78,57% |

| Report đối chứng | Δ pass_rate | CI 95% pass_rate | Δ refund_amount_correct | CI 95% refund_amount_correct | Gate |
|---|---:|---|---:|---|---|
| `E-fixed-20261118-d1ca` | +1,4 đpt | [0,0; +4,3] | +1,4 đpt | [0,0; +4,3] | Exit 0 |
| `E-seeded_regression-20261118-d1ca` | −27,1 đpt | [−50,0; −5,7] | −12,9 đpt | [−31,5; 0,0] | Exit 1 |

CI dùng paired bootstrap percentile trên điểm trung bình qua seed của từng item, 1.000 mẫu tái lấy và RNG seed 2027. Các giá trị CI tính theo điểm phần trăm. Gate chặn `seeded_regression` ở `refund_amount_correct`, `pass_rate` và `reply_refund_matches_ledger`. [Spec v1](../src/config/metric_spec.yaml) · [Report fixed](../src/reports/eval_fixed.json) · [Report seeded_regression](../src/reports/eval_seeded_regression.json)

- **Judge.** `tone_ok` đạt ngưỡng với κ 0,757, precision 0,857 và recall 0,800. `helpful` bị loại khỏi gate vì κ 0,375 và recall 0,300. [Judge audit](judge_audit.md)
- **Trace case.** C-013@11 sai lần đầu ở event 5 khi agent giảm đề xuất từ 35.000đ xuống 0đ. Regression test kiểm đề xuất trên variant lỗi và `fixed`. [Trace case](trace_case.md)
- **Gate owner.** Eval owner kiểm tra report, tái hiện claim/seed lỗi và yêu cầu sửa trước khi merge nếu gate trả exit 1.
- **Phạm vi pilot.** Replay ticket tiếng Việt cho một đơn của chủ thể hiện tại, xét hoàn phí giao trễ hoặc bồi thường hư hỏng đã xác minh theo chính sách Day 8. Số hoàn bị giới hạn theo phê duyệt, số đã thanh toán và phần còn lại theo đơn. [PRD v1.1](PRD_v1.1.md)
- **Giới hạn.** MockLLM và 14 item public cho bằng chứng hồi quy trong lab. Chưa có lưu lượng thật hoặc judge held-out. Shape `swarm` gốc không có event reply, nên điểm FM-08 của nó không xác nhận số tiền trong câu trả lời.
- **Phiên bản.** Khi đổi tập item hoặc nhãn, tăng phiên bản eval set và sinh lại baseline bằng script. Khi đổi grader hoặc ngưỡng, ghi lý do và tăng phiên bản spec.

## v2 — Kiểm tra slice (M5)

Eval set SHA `cd109a409671` gồm 14 claim v1 và 14 claim adversarial, chạy 5 seed cho mỗi item. Baseline là `E-swarm-20261118-cd10`.

| Lượt chạy | pass_rate toàn bộ | money_movement | adversarial | Gate |
|---|---:|---:|---:|---|
| swarm | 98,57% | 100% | 97,14% | Baseline |
| fixed | 100% | 100% | 100% | Qua |
| honest_refactor | 100% | 100% | 100% | Qua |
| slice_regression | 93,57% | 85,00% | 91,43% | Chặn tại money_movement |

`slice_regression` đạt sàn tổng 85% và CI 95% của chênh lệch tổng là [−12,1; +2,9] điểm phần trăm. Slice `money_movement` giảm từ 100% xuống 85%, dưới sàn 90%. Slice `adversarial` kiểm riêng các claim trong pack, với sàn 85%. Cả hai slice chặn nếu CI của chênh lệch so với baseline nằm hoàn toàn dưới 0. Phần M6 ghi kết quả A/A và sàn `pass_hat_5`.

## v2 — Độ ổn định theo seed (M6)

A/A chạy cùng `swarm` với hai bộ seed `11,22,33,44,55` và `66,77,88,99,110`. Tất cả metric có Δ = 0 trên hai bộ này. Mỗi bộ có `pass_rate` 97,86%, `pass@5` 100% và `pass_hat_5` 89,29%. Chọn sàn chặn `pass_hat_5` = 80%, thấp hơn 9,29 điểm phần trăm so với cả hai quan sát A/A.

`flaky_regression` đạt `pass_rate` 91,43%, trên sàn tổng 85%, và `pass@5` 100%. Tuy nhiên chỉ 57,14% item đạt cả 5 lượt, nên `pass_hat_5` chặn độc lập. Trong lần chạy này, CI của `pass_rate` và slice `money_movement` cũng chặn. Scorecard v2 chặn 3/3 regression và cho qua cả hai variant đối chứng.

MockLLM tái lập được kết quả với cấu hình cố định. Hai bộ seed trên chỉ cho biết nhiễu quan sát trong phép đo này. Với LLM thật, sampling và biến động của dịch vụ có thể tạo chênh lệch A/A. Cần thêm lượt đo trước khi dùng sàn cho model thật. Năm seed không đủ để phát hiện ổn định lỗi có xác suất xuất hiện 1/3 mỗi lượt. Với giả định các lượt độc lập, xác suất cả 5 lượt bỏ sót là (2/3)^5, khoảng 13%.

## v2 — Tính toàn vẹn report (M7)

Gate so với baseline `E-swarm-20261118-cd10`. Baseline so với chính nó trả exit 0. Bốn report thử nghiệm công khai đều trả `exit 1 — blocked: integrity`.

| Trap | Lý do chặn |
|---|---|
| `evaluator_errors_as_nan` | Thiếu điểm grader ở các dòng lỗi |
| `dropped_failing_rows` | Thiếu dòng và thiếu cặp item–seed |
| `cherry_picked_seeds` | Tập cặp item–seed khác baseline |
| `loosened_spec` | Khi truyền `--base-spec`, gate phát hiện hạ sàn và bỏ slice trên cùng phiên bản eval set |
