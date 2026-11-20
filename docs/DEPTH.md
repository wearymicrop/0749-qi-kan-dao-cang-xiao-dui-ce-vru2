# 深度登记

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 订购规则 | 生成订阅链年度卷号及应到期位 | `GET /api/orders/dirty` | `app/modules/m1_orders/service.py` | `tests/test_orders.py` |
| M2 来刊采信 | 判定验收号重放、改写冲突及坏行 | `GET /api/receipts/dirty` | `app/modules/m2_receipts/service.py` | `tests/test_receipts.py` |
| M3 卷期解析 | 核对卷期原值、规范化及无效期号 | `GET /api/numbering/dirty` | `app/modules/m3_numbering/parser.py` | `tests/test_numbering.py` |
| M4 合期展期 | 展开本卷合期并单列增刊 | `GET /api/combined/dirty` | `app/modules/m4_combined/claims.py` | `tests/test_combined.py` |
| M5 刊名沿革 | 按出版年度追溯刊名所属订阅链 | `GET /api/titles/dirty` | `app/modules/m5_titles/service.py` | `tests/test_titles.py` |
| M6 缺刊勾稽 | 比对期位与来刊行的分区账目 | `GET /api/balance/dirty` | `app/modules/m6_balance/service.py` | `tests/test_balance.py` |
| M7 证据寄送 | 按输入与规则摘要封存并重跑证据 | `POST /api/runs` | `app/modules/m7_dispatch/service.py` `app/store.py` | `tests/test_dispatch.py` |

## 陷阱登记

| TRAP | 现象 | 朴素实现结果 | 处理 | 位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-01 | 新年度期号复位 | 两年第 1 期被当成同一期 | 年份与卷号关联，逐年期号从 1 起 | `app/modules/m1_orders/service.py` | `tests/test_orders.py::test_yearly_resets_when_volume_increments` |
| TRAP-02 | 同链规则生效年重叠 | 同一期位重复开单 | 阻断整份订购规则 | `app/modules/m1_orders/service.py` | `tests/test_orders.py::test_overlapping_rule_versions_are_rejected` |
| TRAP-03 | 验收表重复回传 | 一件来刊变成两件冲突 | 保留首行并记录重放行 | `app/modules/m2_receipts/service.py` | `tests/test_receipts.py::test_replay_is_counted_once` |
| TRAP-04 | 同验收号指向不同期 | 后写遮住另一条原件 | 并列保存两个候选 | `app/modules/m2_receipts/service.py` | `tests/test_receipts.py::test_disagreeing_accession_preserves_both_originals` |
| TRAP-05 | 空行和残缺记录混入 | 坏行阻断全部来刊 | 分开归因并保留原始位置 | `app/modules/m2_receipts/service.py` | `tests/test_receipts.py::test_empty_and_truncated_records_have_distinct_reasons` |
| TRAP-06 | 卷期含前导零 | 与规则的整数期位匹配失败 | 解析为整数，证据保留字面值 | `app/modules/m3_numbering/parser.py` | `tests/test_numbering.py::test_normalizes_padded_volume_and_issue_preserving_raw` |
| TRAP-07 | 合期起止逆序 | 错把空范围采信为成功 | 保留带原因码的隔离行 | `app/modules/m3_numbering/parser.py` | `tests/test_numbering.py::test_reversed_range_is_rejected` |
| TRAP-08 | 合期有一端越卷 | 越界记录部分补齐缺刊 | 整个合期进入待复查 | `app/modules/m4_combined/claims.py` | `tests/test_combined.py::test_out_of_volume_range_never_partially_applied` |
| TRAP-09 | 增刊号等于正刊号 | 增刊填补期位或引发重复 | 增刊独立于应到期位 | `app/modules/m4_combined/claims.py` | `tests/test_combined.py::test_supplement_same_number_stays_separate` |
| TRAP-10 | 改刊名后继续订阅 | 同一订阅被拆为两条链 | 按出版年度解析新旧刊名 | `app/modules/m5_titles/service.py` | `tests/test_titles.py::test_title_change_keeps_chain` |
| TRAP-11 | 合期与单期部分重叠 | 两个期位全部进入争议 | 只标记重叠期位 | `app/modules/m6_balance/slots.py` | `tests/test_balance.py::test_overlap_only_disputes_shared_slot` |
| TRAP-12 | 同份数据重跑 | 生成第二份档案并覆盖时间 | 使用版本与输入摘要定位首份归档 | `app/store.py` | `tests/test_dispatch.py::test_archive_and_rerun_keep_digest_and_first_result` |

## 对账规则

应到期位 = 已覆盖 + 缺刊 + 争议。来刊行 = 正刊候选 + 增刊 + 重复回传 + 隔离。两个差额均为零时返回 `MATCHED`，缺刊和争议仍需处理。
