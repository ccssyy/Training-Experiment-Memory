# 训练经验 Memory 独立研究集 · 索引

> 独立研究集：Memory 是**独立于 ATF 的通用训练经验系统**，ATF 只是第一个消费方。
> 远程镜像：`work/20260810-training-experience-memory-research` 分支 `docs/research/training-experience-memory/`

## 研究定位

提高"一次训练得到好模型"的成功率：训练前用历史经验分析新任务（分层画像 + 字段语义匹配 → 策略推荐）；训练后把验证有效的 badcase 修复沉淀为经验（回灌闭环）。系统独立设计，可被 ATF、CLI/Web、未来工具接入。

## 阅读路径（按顺序）

| 文档 | 内容 | 状态 |
|---|---|---|
| `01-vision-and-scope.md` | 构想、四层模型（Fact/Profile/Experience/Suggestion）、与 CodingBrain 关系（替代） | 讨论稿（8/8） |
| `02-research-and-precedents.md` | 业界先例（Tinker Cookbook/XAutoLM/Dual-MEM）+ 文档 AI 微调公开教训 + Qwen 历史可沉淀经验清单 | 讨论稿（8/10） |
| `03-task-profiling-v6.md` | **分层画像模型 L1-L4**：单据类别 / 版式（跨类型联合比对）/ 字段（**语义匹配 + 值形态**）/ 数据工程 | 讨论稿（8/10，最新） |
| `04-architecture.md` | 整体架构（读取/回灌双路径）+ 模块级设计（profilers/retriever/advisor/curator/store）+ 独立化原则 | 讨论稿（8/10） |
| `05-consume-integration.md` | ATF 接入适配（单向依赖，核心不 import ATF）+ 未来消费方 | 待写 |
| `06-experience-cards/` | 首批经验卡（普适 10-15 + 自有 20-30） | 待写 |

## 关键设计决策（已讨论）

1. **MVP 不引入新事实 owner**：经验卡是独立存储的通用对象，状态由消费方裁判记录（ATF 用 Decision Ledger）。
2. **完全替代 CodingBrain**：自动回灌 + 证据绑定 + 字段指纹检索，替代人工 ingest 的 wiki。
3. **分层画像，字段层为核心**：新单据即使 memory 无同类，也通过字段语义匹配从"相似语义字段"迁移经验。
4. **推荐是建议不是自动执行**：永不自动改参数；人工接受后生效。
5. **普适经验（provenance=public）与自有经验分池同 schema**：普适经验降级验证，附原始链接。

## 下一步（待拍板）

- 冻结 `experience-card/v1` + `task-profile/v1` schema
- 字段语义词典初版（别名表 + 值形态规则）
- 首批经验卡提炼
