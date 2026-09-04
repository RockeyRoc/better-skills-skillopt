# Better Skills SkillOpt 未来发展计划书

> 版本：v0.1  ·  规划日期：2026-08-28  ·  规划周期：未来 12 个月

[English README](README.md) · [中文版 README](README.zh-CN.md) · [项目宣传页](https://rockeyroc.github.io/better-skills-skillopt/)

## 一、执行摘要

Better Skills SkillOpt 的目标不是再做一个大型 Agent 框架，而是成为一个低门槛、可审计、跨 Agent 的 Skill 质量与发布层：

> 用户提供原始 Skill 和任务反馈；项目帮助 Agent 生成有限修改，执行本地安全验证，并输出新的 better-技能名.zip。

未来 12 个月围绕四个结果推进：

1. **更容易使用**：从 Python 脚本升级为清晰的 CLI 与一条命令式工作流。
2. **更值得信任**：补齐格式、路径、危险模式、密钥形态和回归测试。
3. **更容易迁移**：覆盖主流 Agent 的目录约定，并提供可预览的安装适配。
4. **更容易增长**：用示例库、贡献指南、CI、版本发布和质量报告建立社区循环。

本计划参考了 GitHub 上高关注度的 Agent Skill 项目，但不复制其未经本仓库验证的功能或数据结论。

## 二、当前基线

当前仓库已经具备一个安全优先的最小闭环：

- deployable SKILL.md 入口，能指导当前 Agent 进行有限 Skill 优化；
- append、insert_after、replace、delete 四类 patch 操作；
- 默认四次编辑预算与保护区域；
- frontmatter、内容长度、危险命令、疑似密钥和 ZIP 路径检查；
- JSONL 反馈汇总；
- Codex、Claude Code、Cursor、Devin、GitHub Copilot 目标布局；
- 只生成候选文件和新的惰性 ZIP，不覆盖原始 Skill，不自动安装；
- Python 标准库 CLI 和测试套件。

当前明确不包含：

- 模型供应商调用、后台任务或自动联网；
- 自动修改用户 Agent 目录；
- 基于模型调用的 benchmark 分数承诺；
- 公共 Skill 市场、账号体系或遥测服务；
- 面向生产环境的代码执行沙箱。

## 三、参考项目与可迁移经验

以下项目按 GitHub 页面在 2026-08-28 附近显示的 Star 数做动态快照，数字会持续变化。

| 项目 | Star 快照 | 观察到的强项 | 对 Better Skills 的启示 |
|---|---:|---|---|
| obra/superpowers | 约 278.7k | 可组合 Skill、强制式开发流程、多 Agent 安装入口、测试与代码审查工作流 | 把优化流程做成明确阶段；为不同 Agent 提供清晰入口；用验证结果替代口号 |
| anthropics/skills | 约 172.1k | 每个 Skill 自包含、模板和示例齐全、插件市场入口、文档与免责声明完整 | 建立规范模板、示例库、兼容性说明和安全免责声明 |
| vercel-labs/skills | 约 29.8k | CLI 分发、支持 GitHub/URL/本地源、use 与 add 分离、跨多个 Agent、list/find/update | 降低安装门槛；把发现、预览、使用、更新拆成独立命令 |
| agentskills/agentskills | 约 24.8k | 开放格式规范、渐进式披露、跨产品复用、skills-ref 校验工具 | 兼容公开规范；把 name、description、目录结构和验证规则文档化 |
| microsoft/SkillOpt | 约 16.4k | 轨迹驱动文本优化、验证门、可部署 Skill artifact、多后端和 benchmark | 保留有限编辑、证据驱动、验证后接受的核心思想，但保持本项目轻量和本地优先 |

参考链接：

- [obra/superpowers](https://github.com/obra/superpowers)
- [anthropics/skills](https://github.com/anthropics/skills)
- [vercel-labs/skills](https://github.com/vercel-labs/skills)
- [agentskills/agentskills](https://github.com/agentskills/agentskills)
- [microsoft/SkillOpt](https://github.com/microsoft/SkillOpt)

## 四、产品定位

### 4.1 一句话定位

**Better Skills 是 Agent Skill 的质量门、迁移层和发布工具。**

### 4.2 目标用户

- 使用 Codex、Claude Code、Cursor、Devin 或 Copilot 的个人开发者；
- 正在积累团队 Skill、AGENTS.md 或项目工作流的人；
- 希望复用 Skill，但不愿运行复杂训练框架的人；
- 需要在生成新 Skill 前检查危险命令、路径和秘密泄露风险的团队。

### 4.3 明确不做的事

- 不与完整 Agent 运行时竞争；
- 不把没有 held-out 证据的文本变化宣传为性能提升；
- 不默认联网抓取、自动安装或自动修改系统配置；
- 不把用户私有反馈上传到远程服务；
- 不为了兼容某个 Agent 而牺牲规范 Skill 的可读性和安全性。

## 五、目标架构

~~~text
原始 Skill / 文件夹 / ZIP
            |
            v
输入规范化与安全读取
            |
            v
反馈汇总 + Agent 语义反思
            |
            v
有限 patch 提案
            |
            v
候选 Skill + 结构/安全/回归验证
            |
            v
manifest + 多 Agent 目标布局
            |
            v
better-技能名.zip
            |
            v
用户人工审阅后部署
~~~

架构原则：

1. 原始输入永远保留，候选输出单独落盘。
2. 语义判断由当前 Agent 完成，确定性工具负责边界和文件操作。
3. 任何安全失败都阻断打包，不允许用降低检查强度来换取成功。
4. canonical SKILL.md 与目标 Agent 适配文件分离。
5. 每个版本都应该能回答：输入是什么、改了什么、为什么接受、验证了什么。

## 六、优先级定义

- **P0**：不完成就不适合发布或扩大用户规模。
- **P1**：显著降低使用门槛或提高可迁移性。
- **P2**：提升生态、可观测性和社区增长，但不阻塞核心闭环。
## 七、12 个月路线图

| 阶段 | 时间 | 优先级 | 目标 | 主要交付 |
|---|---|---:|---|---|
| Phase 0 | 0–30 天 | P0 | 发布基础与安全基线 | 版本规范、CI、CHANGELOG、SECURITY、规范校验和可重复打包 |
| Phase 1 | 31–90 天 | P0 | 降低首次使用门槛 | 统一 CLI、inspect/diff/doctor、跨平台路径处理、清晰错误信息 |
| Phase 2 | 3–6 个月 | P1 | 建立证据驱动的质量评估 | golden tasks、held-out 回归集、差异报告、接受/拒绝记录 |
| Phase 3 | 6–9 个月 | P1 | 扩展 Agent 适配 | 适配器注册表、dry-run 安装预览、更多 Agent 目标布局 |
| Phase 4 | 9–12 个月 | P2 | 建立可持续社区生态 | 示例 Skill 库、质量徽章、贡献者流程、版本发布和可选目录 |

### Phase 0：发布基础与安全基线

验收标准：

- 所有输入、输出和安全边界写入版本化文档；
- 每个 ZIP 都带有 manifest、Skill 哈希和验证结果；
- 测试覆盖路径穿越、绝对路径、重复 Skill、超预算编辑、危险命令和疑似密钥；
- CI 在 Windows、Linux 和 macOS 上运行核心测试；
- README、中文版 README、宣传页、CHANGELOG 和 SECURITY 互相可达；
- 任何安全检查失败都不能生成可发布 ZIP。

### Phase 1：统一 CLI 与开发者体验

规划中的命令界面：

~~~powershell
better-skills inspect .\my-skill
better-skills validate .\candidate\SKILL.md
better-skills diff .\original\SKILL.md .\candidate\SKILL.md
better-skills package --skill .\candidate\SKILL.md --output-dir .\dist
better-skills package --skill .\candidate\SKILL.md --target codex --dry-run
~~~

设计要求：

- 保留现有 Python 脚本入口，避免已有用户被迫迁移；
- 支持 Skill 文件、Skill 文件夹和安全 ZIP 输入；
- 输出机器可读 JSON 与适合人阅读的摘要；
- 提供 dry-run，展示将生成的文件和目标路径，但不写入 Agent 目录；
- 错误信息明确指出输入、规则、修复建议和是否可以安全重试；
- 不为了易用性默认引入网络请求、后台服务或系统级安装器。

### Phase 2：质量评估与验证门

新增一个不依赖模型供应商的评估层：

1. 用固定任务集重放原始 Skill 和候选 Skill；
2. 记录任务、输入摘要、结果、失败类型和验证证据；
3. 使用 held-out 任务检查候选是否过拟合反馈；
4. 输出可读 diff、结构检查、风险检查和行为结果；
5. 只有在用户提供可比较证据时，才允许报告性能变化。

建议的结果状态：

- PASS：安全、结构和目标行为均达到门槛；
- REJECTED：候选有改动，但未超过当前最佳版本；
- BLOCKED：触发安全、隐私或输入完整性问题；
- UNVERIFIED：没有足够的可比较任务或评分，不能声称变好。

### Phase 3：跨 Agent 适配层

把目标路径从硬编码列表升级为显式适配器：

~~~text
adapter/
|-- codex
|-- claude-code
|-- cursor
|-- devin
|-- github-copilot
+-- community/
~~~

每个适配器应包含：

- 目标 Agent 名称和版本兼容范围；
- 规范 Skill 到目标文件的映射；
- dry-run 展示；
- 路径安全检查；
- 目标差异说明；
- 不具备自动安装能力时的手工复制指引。

未来即使增加显式安装命令，也必须采用 opt-in、dry-run、目标确认和可回滚设计；默认行为仍然只生成文件。

### Phase 4：社区与发布生态

重点不是先做大而全的市场，而是先建立可信的 Skill 供应链：

- example-skills：按开发、测试、文档、安全等场景提供小而完整的示例；
- metadata：声明 Skill 名称、版本、兼容 Agent、许可证、来源和校验哈希；
- quality badge：只展示通过的结构和安全检查，不把静态检查包装成能力评分；
- release automation：自动生成 ZIP、校验哈希、变更日志和 GitHub Release 资产；
- issue templates：分别收集兼容性、质量回归、安全问题和功能请求；
- security policy：提供私下报告安全问题的流程；
- contributor guide：说明如何新增适配器、示例和测试，而不是只提交未经验证的长提示词。
## 八、未来 90 天执行清单

### 第 1–2 周：把安全基线变成发布基线

- 建立 VERSION、CHANGELOG 和 SECURITY 文档；
- 为 manifest 定义 schema_version、skill_name、skill_hash、validation 和 targets 字段；
- 增加 ZIP 成员白名单与路径归一化测试；
- 增加原始 Skill 不变性测试；
- 建立 GitHub Actions 的 Windows、Linux、macOS 核心测试矩阵；
- 在 README 中明确当前能力、非目标和证据边界。

### 第 3–6 周：完成统一 CLI 设计

- 保留现有 scripts/skillopt_portable.py 作为兼容入口；
- 增加 inspect、diff、doctor 和 version 命令；
- 统一文件、文件夹和 ZIP 的输入发现逻辑；
- 统一文本输出、JSON 输出和退出码；
- 为每个失败场景提供可操作的修复提示；
- 编写一条从原始 Skill 到 ZIP 的端到端 fixture。

### 第 7–10 周：建立可重复评估

- 建立 20 个以上不含隐私的 golden task；
- 为常见失败类型建立最小反馈样例；
- 对原始版本、候选版本和回滚版本生成结构化结果；
- 将安全 gate 与行为评估分开记录；
- 增加候选接受、拒绝、阻断和未验证状态；
- 不发布没有 held-out 任务支持的性能数字。

### 第 11–13 周：准备第一次公开发布

- 发布一份可复制的 quickstart；
- 提供 5–10 个小型 example skills；
- 添加贡献指南、问题模板和安全报告流程；
- 发布 ZIP 示例、SHA-256 校验值和变更日志；
- 录制不包含隐私数据的端到端演示；
- 以一个小版本发布，并根据真实 issue 调整下一阶段优先级。

## 九、成功指标

下表是未来目标，不是当前项目已经达到的结果。

| 维度 | 12 个月目标 | 验证方式 |
|---|---|---|
| 首次体验 | 新用户在 5 分钟内完成一次本地 validate 和 package | 干净环境 quickstart 计时 |
| 安全性 | 安全 fixture 中 100% 阻断已知危险输入 | 自动化 negative tests |
| 可重复性 | 同一输入和版本生成内容一致、哈希可解释的 ZIP | reproducibility test |
| 兼容性 | 至少 5 个 Agent 适配器有路径和示例测试 | adapter test matrix |
| 优化质量 | 每个公开示例都有原始、候选、反馈和验证记录 | example audit |
| 社区 | 10 个以上可复用示例、持续维护的 issue 和 PR 流程 | GitHub repository data |
| 透明度 | 每个性能声明都附带任务集、评分方式和 held-out 说明 | release checklist |

禁止使用 Star 数作为唯一成功指标。Star 只能表示关注度，不能证明 Skill 质量、安全性或实际效果。

## 十、主要风险与应对

| 风险 | 表现 | 应对 |
|---|---|---|
| 反馈过拟合 | 候选只适合少数示例，泛化变差 | held-out 任务、失败类型分组、拒绝编辑记录 |
| 输入提示注入 | 原始 Skill 或反馈诱导 Agent 越权操作 | 将输入视为不可信数据，工具层执行硬安全检查 |
| Agent 规范漂移 | 不同客户端改变目录或 frontmatter 行为 | 适配器版本、兼容性矩阵、定期回归测试 |
| 功能膨胀 | 过早变成复杂 Agent 平台或市场 | P0/P1/P2 门控，优先完成本地质量闭环 |
| 许可证不清 | 示例 Skill、模板或资源来源不可追踪 | manifest 来源、许可证字段和贡献检查 |
| 安全承诺过度 | 静态检查被误解为绝对安全保证 | 文档明确 defense in depth，部署前必须人工审阅 |
| 私有数据泄露 | 反馈、日志或遥测携带敏感内容 | 默认无网络和无遥测，样例数据脱敏，明确数据边界 |

## 十一、贡献与发布规则

### 允许优先提交

- 新的安全测试和回归 fixture；
- 新的 Agent 适配器及其路径文档；
- 可复现的 example skill 和对应反馈；
- CLI 错误信息、跨平台兼容性和文档改进；
- 不包含私密数据的评估工具。

### 必须经过的检查

1. 单元测试通过；
2. 安全 negative tests 通过；
3. 原始输入不变性通过；
4. ZIP 内容和路径检查通过；
5. README、变更日志和 manifest 同步；
6. 如果声称效果提升，提供任务集、评分方法和 held-out 证据；
7. 如果新增目标 Agent，提供目标路径来源和兼容性说明。

### 发布节奏

- patch release：安全修复、文档和兼容性修复；
- minor release：新增 CLI 能力、适配器或评估能力；
- major release：改变输入、patch 或 ZIP 合约时发布，并提供迁移说明。

## 十二、决策门

每个阶段结束时只回答三个问题：

1. 用户是否能更快完成一次安全的 Skill 打包？
2. 候选 Skill 是否比原始版本更容易验证，而不是更难理解？
3. 新功能是否扩大了安全边界、兼容性或维护成本？

如果第 1 或第 2 个问题没有明确的测试证据，功能进入继续实验状态，不进入默认路径。如果第 3 个问题带来新的写入、联网、执行或隐私风险，必须先补充用户确认、dry-run、回滚和安全测试。

## 十三、最终愿景

Better Skills SkillOpt 的终点不是替用户自动决定什么是好 Skill，而是让 Skill 的改进过程变得：

- **可复用**：一次整理，多种 Agent 使用；
- **可验证**：每次修改都有明确边界和证据；
- **可回滚**：原始 Skill 永远保留；
- **可发布**：输出是清晰、惰性、可审阅的 ZIP；
- **可持续**：社区贡献的是测试过的能力，而不是未经验证的长提示词。

在这个定位下，Better Skills 可以成为 Agent Skill 生态中连接规范、质量、安全和分发的轻量基础设施。
