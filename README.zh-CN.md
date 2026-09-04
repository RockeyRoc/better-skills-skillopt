# Better Skills SkillOpt（中文版）

[English README](README.md) · [未来发展计划书](ROADMAP.zh-CN.md) · [宣传网站](index.html)

*一个低门槛、本地优先、面向主流 Coding Agent 的 Skill 优化与打包工具。*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![仅使用标准库](https://img.shields.io/badge/依赖-Python%20标准库-green.svg)](https://docs.python.org/3/library/)
[![参考 Microsoft SkillOpt](https://img.shields.io/badge/参考-Microsoft%20SkillOpt-8dbb3c)](https://github.com/microsoft/SkillOpt)

> 将用户现有的 SKILL.md 与经过整理的反馈交给当前 Agent，生成可审阅的有限文本修改，并输出新的 better-技能名.zip。

## 项目简介

很多 Agent Skill 依赖手工编写或一次性重写。一次性重写容易丢失原有规则，也可能把单次失败过拟合成新的危险行为。

Better Skills SkillOpt 将 Skill 改进拆成一个可审计的本地流程：

~~~text
原始 Skill + 反馈
        ↓
Agent 进行语义反思
        ↓
生成有限 patch
        ↓
本地验证门
        ↓
输出便携 ZIP
~~~

Agent 负责理解任务和提出改进；项目内的 Python 工具只负责确定性的本地操作：应用有限 patch、执行安全检查、汇总 JSONL 反馈、生成 ZIP。工具不会调用模型服务，也不会执行候选 Skill。

## 主要特性

### 有限编辑

只接受四类 patch 操作：

- append：追加内容
- insert_after：在明确锚点后插入
- replace：替换明确文本
- delete：删除明确文本

默认最多四次编辑，并会拒绝保护区域修改、模糊锚点、危险命令模式和疑似密钥内容。

### 本地验证

验证门会检查：

- SKILL.md 基本结构与 frontmatter
- 内容是否为空或过度膨胀
- 保护标记是否被破坏
- 是否出现危险命令或疑似密钥
- ZIP 内路径是否安全

安全检查失败会停止打包。验证通过只代表结构和安全边界合格，不等同于任务效果评分。

### 跨 Agent 打包

项目会生成一个惰性的 ZIP，包含规范 Skill 和常见 Agent 目录布局：

~~~text
better-name/
|-- SKILL.md
|-- manifest.json
|-- README.md
+-- targets/
    |-- codex/.agents/skills/name/SKILL.md
    |-- claude/.claude/skills/name/SKILL.md
    |-- cursor/.cursor/skills/name/SKILL.md
    |-- devin/.devin/skills/name/SKILL.md
    +-- copilot/copilot-instructions.md
~~~

ZIP 不会自动安装，不会复制文件到任何 Agent 目录，也不会修改系统文件。用户审阅后，手动选择对应目标文件即可。

## 快速开始

环境要求：Python 3.10 或更高版本，无需安装第三方 Python 依赖。

在项目根目录执行：

~~~powershell
python scripts/skillopt_portable.py validate path\to\SKILL.md
python scripts/skillopt_portable.py summarize-feedback data\examples.jsonl
python scripts/skillopt_portable.py package --skill path\to\candidate\SKILL.md --output-dir .\dist
~~~

对经过审阅的 proposal 应用 patch：

~~~powershell
python scripts/skillopt_portable.py apply-patch --skill path\to\original\SKILL.md --patch path\to\proposal.json --output path\to\candidate\SKILL.md
~~~

运行测试：

~~~powershell
python -m unittest discover -s tests -v
~~~

最终输出：

~~~text
dist/better-技能名.zip
~~~

## 反馈数据

反馈使用 JSONL 格式，每行记录一个任务。建议保留 task、outcome、failure_type、observation 和 0 到 1 之间的 score。

请在反馈中删除密码、Token、私有提示词、原始工具 payload 和不必要的本地路径。使用汇总命令可以观察重复失败模式，再决定是否提出 Skill 修改。

## 安全边界

本项目的目标是只生成新的 Skill 文件。

- 只读取用户明确提供的输入文件。
- 不覆盖原始 Skill。
- 只写入用户指定的候选文件和输出目录。
- 不访问网络，不安装依赖，不启动外部进程。
- 不修改系统文件，不自动写入任何 Agent 配置目录。
- 拒绝危险归档路径、危险命令模式和疑似密钥。
- 输出 ZIP 是惰性的，部署前必须人工审阅。

## 项目结构

~~~text
better-skills-skillopt/
|-- SKILL.md                         # 可部署的入口 Skill
|-- agents/openai.yaml               # Agent 元数据
|-- data/examples.jsonl              # 反馈示例
|-- references/                      # 方法与安全契约
|-- scripts/skillopt_portable.py     # CLI
|-- skillopt/portable.py             # 标准库实现
+-- tests/test_portable.py           # 测试
~~~

## 方法来源

项目设计借鉴 Yang 等人的 [SkillOpt 论文](https://arxiv.org/abs/2605.23904) 和 [Microsoft SkillOpt 项目](https://github.com/microsoft/SkillOpt)，但本仓库是一个更轻量的部署层，不替代完整的研究框架、训练后端或基准测试系统。

- [返回英文 README](README.md)
- [打开项目宣传页](index.html)
- [SkillOpt 论文](https://arxiv.org/abs/2605.23904)
- [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt)
