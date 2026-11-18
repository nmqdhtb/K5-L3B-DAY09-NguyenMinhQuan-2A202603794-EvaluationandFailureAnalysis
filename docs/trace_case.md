# Trace case C-013@11

| Trường | Bằng chứng |
|---|---|
| Trial | `seeded_regression C-013@11`, report `E-seeded_regression-20261118-d1ca`. |
| Triệu chứng | Grader Day 8 báo `proposal_mismatch`. Reply nói đơn không đủ điều kiện hoàn và ledger ghi 0đ, đúng với kết quả kỳ vọng. Đề xuất trước khi host xử lý lại là 0đ thay vì 35.000đ. |
| Bước sai đầu tiên | Event 5 `proposal` có payload `{"amount_vnd": 0}`. Agent tự trừ khoản đã hoàn khỏi báo giá. |
| Vì sao là bước đầu tiên | Event 1 bàn giao claim, event 2 đọc đơn O-505, event 3 báo giá đúng 35.000đ và event 4 đọc lịch sử đã hoàn đúng 35.000đ. Sai lệch xuất hiện khi agent dùng lịch sử để thay đổi đề xuất. |
| Failure mode | FM-05 (`pre_deducted`). |
| Đối chứng | `fixed C-013@11`, report `E-fixed-20261118-d1ca`. Trace giữ báo giá 35.000đ ở event 3 và không sinh event giảm đề xuất. Ledger vẫn 0đ và grader Day 8 đạt. |
| Regression test | `test_pre_deduction_is_visible_even_when_ledger_is_correct` trong `src/tests/test_lab9_graders.py`. `ProposalAmountCorrect` đánh trượt variant lỗi và chấp nhận `fixed`. `RefundAmountCorrect` đạt trên variant lỗi vì ledger vẫn đúng. |
| Chưa chắc chắn | Trace này không cho biết tần suất lỗi trên model thật. |

Chạy lại từ `src/`:

```bash
python -m lab9.trace_case --shape seeded_regression --claim C-013 --seed 11
python -m lab9.trace_case --shape fixed --claim C-013 --seed 11
```
