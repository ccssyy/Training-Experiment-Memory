# 训练经验 Memory · 架构设计总览

> 日期：2026-08-13 ｜ 状态：设计总览（配套 `docs/diagrams/` 下的架构图）
> 图均自包含 HTML（含明暗主题切换 + PNG/SVG 导出），浏览器直接打开。

## 1. 系统定位

训练经验 Memory 是**独立于 ATF 的通用训练经验系统**，目标是提高"一次训练得到好模型"的成功率。核心机制是一条**自我进化闭环**：

- **训练前（Preflight）**：用历史经验分析新任务 → 画像 + 检索 → 建议卡（只建议，不自动改参数）。
- **训练后（Postflight）**：把验证有效的 badcase 修复沉淀为经验（回灌），供下次命中。

## 2. 四张架构图

| 图 | 文件 | 内容 |
|---|---|---|
| 系统架构 | `diagrams/system-architecture.html` | 消费方 → 接入层 → 核心层（画像/检索/建议/回灌）→ 独立存储；单向依赖 |
| 完整闭环 | `diagrams/feedback-loop.html` | 训练前推荐 → 训练 → 训练后回灌 → 写回记忆库 → 下次再命中 |
| 对象模型 | `diagrams/object-model.html` | EvidenceEvent → ExperienceCase → PatternClaim → Mechanism 四层 + 能力标签/字段语义概念 |
| 状态机 | `diagrams/claim-lifecycle.html` | Claim 状态转换：candidate → confirmed → validated / rejected / unresolved / superseded |

## 3. 分层架构

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  消费方 1    │   │  消费方 2    │   │   未来消费方  │
│  (ATF)      │   │  (CLI/Web)  │   │  (其他工具)   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       └─────────────────┼─────────────────┘
                         ▼
              ┌──────────────────────┐
              │   Memory 接入层       │  ← 适配接口（画像/建议/回灌）
              └──────────────────────┘
                         ▼
              ┌──────────────────────┐
              │   Memory 核心层       │
              │  · 画像引擎 profilers  │
              │  · 检索引擎 retriever  │
              │  · 建议卡 advisor      │
              │  · 回灌引擎 curator    │
              └──────────────────────┘
                         ▼
              ┌──────────────────────┐
              │   独立存储 memory.db  │  ← Case/Claim/概念/标签/Event
              └──────────────────────┘
```

**独立化原则**：核心层不 import 任何消费方代码；消费方通过适配接口**单向依赖** memory。

## 4. 对象模型四层

| 对象 | 职责 | 生命周期 |
|---|---|---|
| `EvidenceEvent` | 训练事实（badcase 结论 + 指标 + 评估） | 追加式，不可变 |
| `ExperienceCase` | 单次实验观察，绑定证据 | 不可变 |
| `PatternClaim` | 机制在某字段类型下的实例，多案例聚合 | 有状态机（见 §5） |
| `Mechanism` | 跨字段类型的稳定方案，多实例归纳 | active/merged/superseded/deprecated |

**检索/推荐用 Claim（实例）+ Mechanism（机制），追溯用 Case，回灌用 Event。**

- 单次实验结果 ≠ 通用规律：多 Case 聚合 → 可迁移 Claim。
- 多 Claim 归纳 → Mechanism：机制层只基于**稳定结构属性**（语义/基数/值形态/版式/跨页），**不碰易变的字段类型划分**（lane/标注范围）。字段类型划分是独立 Taxonomy 层，变更只动 Claim 引用，机制本体零改动。

## 5. 状态机

Claim：
```
candidate ──► confirmed ──► validated ──► superseded
     │              │
     ├──► rejected ─┴──► (负经验)
     └──► unresolved（长期难例，阻断重试）
```

Mechanism：
```
active ──► merged ──► superseded（保留旧记录）
   └──────► deprecated（被新机制取代，不再推荐）
```

- `candidate`：待验证候选，不参与正式检索。
- `confirmed`：归因/诊断确认（结论可信，但干预未验证），检索权重 +0.08。
- `validated`：干预验证通过（7 项全过），检索权重 +0.15。
- `rejected`：验证失败的负经验（contraindication 素材）。
- `unresolved`：问题确认但无解决路径，防止反复试错。

## 6. 检索链与迁移

新单据字段 → 三路匹配（别名表 / 值形态启发 / 语义向量 bge-m3）→ canonical 字段语义概念 → 打能力标签 → **命中 Mechanism（稳定结构属性）→ 定位 Claim 实例（lane/doc_types）**，含 transfer_level 迁移层级。

**两级检索**：
- **机制层**（Mechanism）：按稳定结构属性（语义/基数/值形态/版式/跨页）命中，跨字段类型。
- **实例层**（Claim）：在命中机制下按易变维度（lane/doc_types/languages）定位具体实例。
- 命中机制但无匹配实例 → 推荐机制 + 标注「当前字段类型无验证实例，谨慎」。

**关键机制**：能力标签与字段名解耦——装箱单的"行级归组数量字段"经验通过 `grouped_value + row_aligned + dense_table` 标签迁移到任何同类密集跨页表格单据，而非靠"装箱单"字段名。

## 7. 回灌验证门槛

- **写入门槛**（block）：缺证据 / delta 不对 prior-best / 口径不一致 / fake 结果。
- **validated 7 项**：目标改善 / 无未解释退化 / 保护无回归 / evaluator 有效 / runtime 完整 / ID-OOD 可解释 / 人工验收。
- **rejected 8 类**：核心不改善 / 保护回归 / 空输出增 / 重复 group / 污染 / runtime 未加载 / 成本无收益。

回灌**永远停在人工验收闸前**，不自动写库。

## 8. 实现进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 1 | 记忆数据（32 Case + 26 Claim + 5 Mechanism + 85 概念 + 标签） | ✅ |
| Phase 2 | 训练前推荐（画像 + 机制/规则检索 + 建议卡 + 版式视觉确认） | ✅ MVP |
| Phase 3 | 训练后回灌（EvidenceEvent + 验证门槛 + curator） | ✅ 框架 + dry-run |
| 向量检索 P4 | 字段语义向量 bge-m3 + 概念索引 + 别名未命中兜底 | ✅ 已闭环 |
| F1~F4 结构反馈 | 版式标签 / 值形态过滤 / 上下文类 / CTN 单位 | ✅ 全部闭环 |
| 待做 | ATF 接入 / 真实训练验证 | 后续 |

## 9. 架构图（含 PNG 导出）

| 图 | HTML（自包含浏览器） | PNG 导出 |
|---|---|---|
| 系统架构 | `diagrams/system-architecture.html` | `diagrams/system-architecture.png` |
| 完整闭环 | `diagrams/feedback-loop.html` | `diagrams/feedback-loop.png` |
| 对象模型（含 Mechanism） | `diagrams/object-model.html` | `diagrams/object-model.png` |
| 状态机 | `diagrams/claim-lifecycle.html` | `diagrams/claim-lifecycle.png` |

PNG 用 Chrome headless 截图生成（参数：--headless=new --disable-crashpad --no-sandbox --run-all-compositor-stages-before-draw），1400×1000。
