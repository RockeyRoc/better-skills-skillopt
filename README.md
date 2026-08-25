# Better Skills SkillOpt

一个面向编程型 Agent 使用者的低门槛 skill 优化器。它借鉴 Microsoft
[SkillOpt](https://github.com/microsoft/SkillOpt) 与 Yang 等人的论文方法，把
“反思、有限编辑、验证门、可复用文本 artifact”收敛成一个不依赖 Python
第三方包、无网络、无系统写入的便携项目。

## 解决的问题

原始 SkillOpt 更偏研究与基准复现：需要模型后端、数据集、训练配置和执行
harness。这个项目把部署入口简化为一个 skill：用户把原始 `SKILL.md`、skill
文件夹或 ZIP 交给当前 agent，agent 根据反馈提出小范围改进，然后用内置脚本
验证并生成新的 `better-<name>.zip`。

语义改进由当前 agent 完成；脚本只负责可审计的原子 patch、格式/安全检查和
跨 agent 打包。这使它能在 Codex、Claude Code、Cursor、Devin 兼容布局以及
GitHub Copilot 指令文件之间复用同一个 canonical skill。

## 目录

```text
better-skills-skillopt/
├── SKILL.md                         # 可部署的入口 skill
├── agents/openai.yaml               # Codex UI 元数据
├── skillopt/portable.py             # 标准库实现
├── scripts/skillopt_portable.py     # CLI
├── data/examples.jsonl              # 可复用反馈数据格式示例
└── references/                      # 方法与安全契约
```

## 快速开始

在项目根目录执行：

```powershell
python scripts/skillopt_portable.py validate path\to\SKILL.md
python scripts/skillopt_portable.py summarize-feedback data\examples.jsonl
python scripts/skillopt_portable.py package `
  --skill path\to\optimized\SKILL.md `
  --output-dir .\dist
```

运行标准库测试：

```powershell
python -m unittest discover -s tests -v
```

输出：

```text
dist/better-<skill-name>.zip
```

ZIP 是惰性的，不包含安装器，不会自动复制到任何 agent 目录。解压后按目标
选择一个文件：

- `targets/codex/.agents/skills/<name>/SKILL.md`
- `targets/claude/.claude/skills/<name>/SKILL.md`
- `targets/cursor/.cursor/skills/<name>/SKILL.md`
- `targets/devin/.devin/skills/<name>/SKILL.md`
- `targets/copilot/copilot-instructions.md`

## 从反馈生成候选

`data/examples.jsonl` 使用一行一个任务的轻量格式。真实使用时建议保留
`task`、`outcome`、`failure_type`、`observation` 和可比的 `[0,1]` `score`，
同时删除秘密、私有文本、原始工具 payload 和不必要的路径。

```powershell
python scripts/skillopt_portable.py apply-patch `
  --skill path\to\original\SKILL.md `
  --patch path\to\proposal.json `
  --output path\to\candidate\SKILL.md
```

patch 仅允许 `append`、`insert_after`、`replace`、`delete` 四种操作，并默认
最多四个编辑。它会拒绝保护区修改、模糊目标、破坏性系统命令和疑似密钥。

## 安全与边界

- 只读取用户明确提供的文件；原始 skill 永不覆盖。
- 只写用户明确指定的候选文件或 ZIP 输出目录。
- 不启动子进程，不访问网络，不安装依赖，不修改系统文件。
- 不提供自动 adoption/installer；用户必须人工审核并复制目标文件。
- 只把验证后的 target-facing `SKILL.md` 放进部署目录；反馈与 optimizer
  说明不会混入目标 skill。

详细规则见 `references/portable_contract.md`。论文方法摘要见
`references/method.md`。

## 参考

- Yang et al., [SkillOpt: Executive Strategy for Self-Evolving Agent Skills](https://arxiv.org/abs/2605.23904)
- Microsoft, [SkillOpt](https://github.com/microsoft/SkillOpt)
