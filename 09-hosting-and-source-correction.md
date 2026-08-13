# 承载与素材来源修正（v9：基于两个真实情况）

> 日期：2026-08-13 ｜ 状态：讨论稿 ｜ 修正 v8 的两处判断

## 情况一：ATF 独立 worktree 会乱 —— 确认属实，需立即独立

### 事实

- 我们的 memory worktree `training-experience-memory-v2` 基于 **8/7 的 C02 golden 14a8e8f**。
- ATF 主仓库 HEAD 停在 8/10（56f6132），但**开发在别的分支继续推进**：8/11-8/13 三天 30+ 条新提交，最新 C02 开发分支 `work/20260812-atf-c02-build-r17-outcome-evidence`（9975058，8/13 03:18）。
- 我们的 worktree 与 ATF 最新开发已差 **30+ 提交**，且 ATF 仓库有几十个 worktree，memory 挂在其上必然纠缠不清。

### 修正：memory 现在就从 ATF worktree 独立出去

不是"Phase 2 前再独立"，而是**现在**。理由：
1. 我们只产出了 8 份**文档**，还没写代码，迁移成本极低——正是独立的最佳时机。
2. memory 定位是"独立系统 + ATF 消费方"，本就不该与 ATF 同仓库。
3. 继续在落后 30+ 提交的旧 worktree 上写，后面 merge/rebase 会非常痛苦。

**承载方案（修正 v8 决策 3）**：
- 首选：**独立 git 仓库**（本地 `git init` 立即可做，托管 remote 由你定 GitHub/公司 git）。
- 过渡：至少先把文档迁到一个**独立目录**（如 `[本仓库]/`），不再挂在 ATF worktree 下。
- ATF 侧：只保留一个"接入点"引用（未来 ATF 通过接口依赖 memory，而非同仓库）。

## 情况二：Phase 1 素材主体是 Qwen，不是同事 —— 确认属实

### 事实

Qwen2.5-VL-main 才是历史训练记录的**真正主体**：
- `runs/`：**104 个**训练实验运行（4 月至今，8/12 仍在新增 `eight_docs_goods_prompt_aligned_r4`）
- `docs/performance/`：21 份实验报告
- `.codex/session-digests/`：69 个会话摘要
- `analysis_outputs/`：50 个分析输出
- `docs/data|workflow|superpowers`：7+3+7
- `[知识库]/04_Registries/`：11 个 Registry（Experiment/Training Run/Metric/Dataset/Issue/Decision/Feature/Model/Release/Requirement/Code Pattern）

同事的 `non_goods_round3_analysis` 只是其中一块补充（且同事刚加入训练）。

### 修正 Phase 1 素材优先级

```
主体（Qwen2.5-VL-main）：
  1. docs/performance/ 21 份报告（策略与指标结论，PatternClaim 的直接来源）
  2. runs/ 104 个目录（manifest/指标/checkpoint，ExperienceCase 的证据来源）
  3. session-digests/ 69 个（失败机制、踩坑、迭代决策）
  4. analysis_outputs/ 50 个（badcase 分析、字段合同审计）
  5. coding-brain 11 Registry（已结构化的历史索引，可直接转 Case）
补充（同事）：non_goods_round3_analysis 分析包（non-goods 字段合同 + split + checkpoint-342）
```

## 修订后的结论

1. **承载**：memory **现在**从 ATF worktree 独立为独立 git 仓库（或独立目录），不再与 ATF 开发纠缠。
2. **素材**：Phase 1 以 Qwen 历史归档为主体（104 run / 21 报告 / 69 摘要 / 50 分析 / 11 Registry），同事素材为补充。
3. 框架、向量、独立化、对象模型（Case/Claim）等 v7/v8 决策不变。

## 下一步行动（建议顺序）

1. 你定托管位置（GitHub 仓库名 / 公司 git / 先本地独立目录）→ 我立即把 8 份文档迁移出去，与 ATF worktree 解耦。
2. 起草 Phase 1 执行切片：以 Qwen 历史归档为输入，产出首批 ExperienceCase + PatternClaim + 通用能力标签初版。
