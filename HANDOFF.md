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
| 07-colleague-synthesis | 综合同事 zito-atf-dev Preflight 设计 | 讨论稿 |
| 08-object-model-and-hosting | Case+Claim 两层映射 + 承载决策 | 讨论稿 |
| 09-hosting-and-source-correction | 承载修正 + Phase 1 素材主体（Qwen） | 讨论稿 |

## 已定决策（勿重复讨论）

1. **框架主体**：用同事的 Preflight（Case/Claim 两层 + 通用能力标签 + 能力矩阵 + 状态机）。
2. **保留我们的**：向量分析（字段语义 bge-m3 + 版式视觉 CLIP/DINOv2）+ 独立化架构 + ATF 接入层。
3. **对象模型**：experience-card 拆为 `ExperienceCase`（证据侧）+ `PatternClaim`（模式侧，通用能力标签，引用 case 集合）。检索用 Claim、追溯用 Case。
4. **字段语义匹配**：三路全纳入首轮（别名表 + 值形态启发 + 语义向量 bge-m3 阈值 0.75）。
5. **版式相似度**：双路（布局结构规则 0.6 + 页面视觉向量 0.4）。
6. **数据支持四维**：support / coverage / exposure / diversity。
7. **迁移层级**：direct / structural / mechanism / context。
8. **策略状态**：validated / rejected / unresolved。
9. **仓库**：private，ccssyy/Training-Experiment-Memory；旧位置（ATF worktree 分支、本地 AutoTrainingFlow 目录）全部保留只读。
10. **不引入新事实 owner**：经验是独立存储通用对象，ATF 侧由 Decision Ledger 记录状态转换。

## 下一步：Phase 1（整理历史 → ExperienceCase/PatternClaim）

以 **Qwen2.5-VL-main 历史归档为主体**，同事 non_goods round3 为补充，产出首批 ExperienceCase + PatternClaim + 通用能力标签初版。

素材优先级：
1. `docs/performance/` 21 份报告（策略与指标结论 → PatternClaim 直接来源）
2. `runs/` 104 个目录（manifest/指标/checkpoint → ExperienceCase 证据）
3. `session-digests/` 69 个（失败机制、踩坑、迭代决策）
4. `analysis_outputs/` 50 个（badcase 分析、字段合同审计）
5. `coding-brain` 11 Registry（已结构化历史索引）
6. 补充：同事 `/data/chris/bea/repos/zito-atf-dev/tmp/non_goods_round3_analysis`

## 关键路径与账号

- **A800 开发机**（SSH host 别名 `A800_5005`）：本仓库 `/data/sam/training-experience-memory`；Qwen 历史素材 `/data/sam/Qwen2.5-VL-main`；同事设计 `/data/chris/bea/repos/zito-atf-dev`。
- **Mac 本地**：`~/Work/git/Training-Experiment-Memory`（workbuddy 开发工作区）。
- **GitHub**：`ccssyy/Training-Experiment-Memory`（private，唯一 origin）。
- A800 推 GitHub 用 `~/.ssh/id_ed25519_codingbrain`（已认证 ccssyy）；Mac 用 `~/.ssh/id_ed25519_github`。
