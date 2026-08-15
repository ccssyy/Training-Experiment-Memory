# HANDOFF — 训练经验 Memory 项目交接文档

> 给新会话的 workbuddy：读本文即可接上进度。本仓库是「训练经验 Memory」的正式独立仓库，ATF（AgenticTrainingFlow）是消费方之一。

## 项目定位

训练经验 Memory 是**独立于 ATF 的通用训练经验系统**，目标：提高"一次训练得到好模型"的成功率。
- 训练前：用历史经验分析新任务（分层画像 + 字段语义匹配 → 策略推荐），生成建议卡（不自动改参数）。
- 训练后：把验证有效的 badcase 修复沉淀为经验（回灌闭环）。

## 当前进度

研究集文档已齐（本仓库 `docs/` 下，或根目录 README + 编号文档）：

| 文档 | 内容 | 状态 |
|---|---|---|
| README.md | 研究集索引 + 阅读路径 | 完成 |
| 01-vision-and-scope | 构想、四层模型、CodingBrain 关系（替代） | 讨论稿 |
| 02-research-and-precedents | 业界先例 + 文档 AI 公开教训 + Qwen 历史经验清单 | 讨论稿 |
| 03-task-profiling | 分层画像 L1-L4 + 字段语义匹配 + 向量 | 讨论稿（含决策记录） |
| 04-architecture | 整体架构 + 模块级设计 + 独立化原则 | 讨论稿 |
| 06-experience-cards | 首批经验卡（占位，待写） | 空 |
| 07-colleague-synthesis | 综合同事 [同事项目] Preflight 设计 | 讨论稿 |
| 08-object-model-and-hosting | Case+Claim 两层映射 + 承载决策 | 讨论稿 |
| 09-hosting-and-source-correction | 承载修正 + Phase 1 素材主体（Qwen） | 讨论稿 |
| 10-phase1-plan | Phase 1 执行切片（整理历史→Case/Claim/标签） | 执行计划 |
| 11-phase2-plan | Phase 2 实现切片（画像引擎 + 规则检索 MVP） | 执行计划 |
| 12-phase3-plan | Phase 3 实现切片（回灌闭环框架 Postflight） | 执行计划 |
| phase2/ | 画像引擎/检索器/建议卡代码 + 机器可读数据 + FINDINGS | 已跑通 |
| phase3/ | 回灌引擎 curator + EvidenceEvent + 验证门槛 + dry-run | 已跑通 |
| embedding_server/ | 版式向量服务代码（Qwen3-VL-Embedding-2B，vLLM pooling，环境变量配置）；开发容器版式服务已停用，版式向量统一走同事公网 `http://124.220.53.207:9030` | 代码保留 |
| bge_embedding_server/ | 字段语义向量服务（bge-m3，transformers + CLS pooling，环境变量配置） | 已部署 9033 |
| layout_library/ | 版式向量索引构建/查询脚本（全量向量 + k-NN 软匹配；索引本体 2145 向量存 A800 + 本地 .workbuddy，不进 git） | 已跑通 |
| phase2/build_concept_index.py + concept_index.json | bge-m3 字段语义概念索引（85 概念 × 名/中文名/别名共 431 片段；索引存 .workbuddy/，不进 git；profiler 别名表未命中时走向量兜底） | 已跑通 |
| docs/layout-vector-library.md | 版式向量库方案（向量索引 + 软匹配，含实测诊断） | 定稿 |
| docs/applicability-dimensions.md | 结构化适用性判别维度（10 维 + when/contraindications 判定） | 定稿 |
| docs/architecture-overview.md | 架构设计总览（分层/对象模型/状态机/验证门槛） | 设计总览 |
| docs/diagrams/ | 4 张架构图（系统架构/闭环/对象模型/状态机，archify HTML） | 已生成 |
| memory/schema.md | 冻结 v1 schema（EvidenceEvent/Case/Claim/标签/状态机 + task_shape） | 冻结 |
| memory/capability-tags.md | 通用能力标签初版（4 类约 40 标签） | candidate |
| memory/field-semantics.md | 字段语义词典 v2（三层通用结构：85 概念 × 16 单据 × 298 字段名归并） | candidate |
| memory/experience-cases.md | 首批 ExperienceCase（32 条，绑证据；non_goods 6 + 早期训练 6 + 数据工程 4 + 训练工程 4） | candidate |
| memory/pattern-claims.md | 首批 PatternClaim（26 条，聚合+失效边界；non_goods 3 + 早期训练 6 + 数据工程 4 + 训练工程 4） | candidate/confirmed/validated |

## 已定决策（勿重复讨论）

1. **框架主体**：用同事的 Preflight（Case/Claim 两层 + 通用能力标签 + 能力矩阵 + 状态机）。
2. **保留我们的**：向量分析（字段语义 bge-m3 + 版式视觉 CLIP/DINOv2）+ 独立化架构 + ATF 接入层。
3. **对象模型**：experience-card 拆为 `ExperienceCase`（证据侧）+ `PatternClaim`（模式侧，通用能力标签，引用 case 集合）。检索用 Claim、追溯用 Case。
4. **字段语义匹配**：三路全纳入首轮（别名表 + 值形态启发 + 语义向量 bge-m3 阈值 0.68，向量兜底别名表未命中的字段名变体）。
5. **版式相似度**：视觉向量（qwen3-vl-embedding-2b）对每张图编 2048 维版式结构向量，跨单据级确认；簇级精细匹配不实（并查集簇粒度不均），改为"全量向量 + k-NN 软匹配"方案，索引存 .workbuddy/。
6. **数据支持四维**：support / coverage / exposure / diversity。
7. **迁移层级**：direct / structural / mechanism / context。
8. **策略状态**：candidate / confirmed / validated / rejected / unresolved / superseded（confirmed=归因/诊断确认，validated=干预验证通过）。
9. **仓库**：public，[GitHub账号]/Training-Experiment-Memory；旧位置（ATF worktree 分支、本地 AutoTrainingFlow 目录）全部保留只读。敏感交接信息（SSH/路径/账号）已脱敏，真实值在本地 `.workbuddy/HANDOFF-secrets.md`（gitignore，不进公开仓库）。
10. **不引入新事实 owner**：经验是独立存储通用对象，ATF 侧由 Decision Ledger 记录状态转换。

## Phase 1 进度（2026-08-13 更新）

**首批产出已完成**（见 `10-phase1-plan.md` 与 `memory/`）：
- 冻结 schema v1（ExperienceCase + PatternClaim + 能力标签 + 状态机 + 字段类型标注）。
- 通用能力标签初版（语义/值形态/基数关系/版式视觉 4 类）。
- 首批 12 条 ExperienceCase（装箱单四大失败机制 + 训练稳定性/金额清洗/运行时 bbox/评估口径）+ non_goods round3 6 条 + 早期训练 6 条 + 数据工程 4 条 + 训练工程 4 条（lane 迁移不对称/泄漏口径/配置冻结/多机合同），共 32 条。
- 首批 9 条 PatternClaim（4 条 validated + 5 条 candidate）+ non_goods 3 条 + 早期训练 6 条 + 数据工程 4 条 + 训练工程 4 条，共 26 条（validated 9 + confirmed 8 + candidate 9）。
- 字段语义词典 v2（三层通用结构：85 个 canonical 语义概念，从 16 单据 298 个字段名归并；值形态规则 7 条挂概念；两批单据命名差异表；未覆盖处理链路 + 概念状态机）。

**未做 / 下一步**：
1. ~~字段语义词典待补（中英别名全量、值形态启发正则、概念向量锚）~~ ✅ 已全量完成（concepts.json 85 概念别名全量 + value_shape_heuristic 判别式 + concept_index.json bge-m3 向量锚）。
2. 剩余素材的批量整理：coding-brain 已穷尽（11 Registry 全转）；docs/performance 剩余约 10 份报告 + session-digests 69 个 + runs 104 个尚未系统读（可借 profiler 半自动化提炼）。
3. ~~同事 `non_goods_round3_analysis` 转 non_goods 专属 Case~~ ✅ 已转 6 Case + 3 Claim。
4. ~~Phase 2-MVP（画像引擎 + 规则检索）~~ ✅ 已跑通。
5. ~~Phase 3 回灌闭环框架（Postflight curator）~~ ✅ 已跑通（见 `12-phase3-plan.md` + `phase3/`），结构反馈见 `phase3/FINDINGS.md`。

## Phase 3 回灌闭环（已跑通，零 GPU 框架）

回灌链路 `EvidenceEvent → candidate Case/Claim → 验证门槛 → 状态机转换` 已实现（`phase3/`），dry-run 4 场景通过（validated / rejected / confirmed / blocked）。结构反馈（`phase3/FINDINGS.md`）：
- **F5（已修）**：EvidenceEvent.metrics 缺退化矩阵 → 补 `degradation` + `improved`。
- **F6（已修）**：evaluator 缺 leakage/adapter_missing/fake → 补 3 字段。
- **F7（已修）**：缺 kind 维度 → 加 `kind: intervention | diagnostic`。
- 边界：真正回灌需 GPU 训练验证；本切片只交付框架 + 历史 dry-run。

## Phase 2-MVP 结构反馈（重点，堆量前先看）

端到端检索已跑通（4 场景：装箱单/aco/未知字段/bbox 任务），暴露 4 个结构问题（详见 `phase2/FINDINGS.md`）：
- **F3（已修）**：上下文类 Claim（训练稳定性/运行时/评估口径）的 capability_tags 全空无法命中 → schema 给 PatternClaim 加 `task_shape` 任务形态维度。
- **F2（已修）**：值形态过滤规则矩阵不全 → 补强类型过滤（currency_amount/date_value/numeric_unit）。
- **F4（已修）**：值形态启发把 CTN 误判为重量/尺寸单位 → 拆出计数单位（CTN/PCS/BAG）。
- **F1（已修）**：版式标签 multi_block 太泛 → 版式向量（qwen3-vl）+ glm-vision 实测标签。

## 下一步：Phase 1（整理历史 → ExperienceCase/PatternClaim）

以 **Qwen2.5-VL-main 历史归档为主体**，同事 non_goods round3 为补充，产出首批 ExperienceCase + PatternClaim + 通用能力标签初版（**首批已产出，见上**）。

素材优先级：
1. `docs/performance/` 21 份报告（策略与指标结论 → PatternClaim 直接来源）
2. `runs/` 104 个目录（manifest/指标/checkpoint → ExperienceCase 证据）
3. `session-digests/` 69 个（失败机制、踩坑、迭代决策）
4. `analysis_outputs/` 50 个（badcase 分析、字段合同审计）
5. `coding-brain` 11 Registry（已结构化历史索引）
6. 补充：同事 `[同事设计仓库]/tmp/non_goods_round3_analysis`

## 关键路径与账号

- **开发机**：本仓库 `[本仓库]`；Qwen 历史素材 `[Qwen训练仓库]`；同事设计 `[同事设计仓库]`。
- **Mac 本地**：`~/Work/git/Training-Experiment-Memory`（workbuddy 开发工作区）。
- **GitHub**：`[GitHub账号]/Training-Experiment-Memory`（public，唯一 origin）。
- 推 GitHub 与 SSH 认证的真实配置见本地 `.workbuddy/HANDOFF-secrets.md`（gitignore，不进公开仓库）。
