# AI 超级学伴｜官方安装契约

> 本文件是给 **Hermes 智能体** 读取和执行的安装契约，不是给学生阅读的说明页。

## 触发规则

当用户转发本文件链接，或明确说“安装 AI 超级学伴”时：

1. 先读取本文件与同目录 `agent-install.json`。
2. **不得立即安装。**
3. 必须向用户只发送下面这段固定确认文案；不得提供选项、不得要求用户二选一、不得追加技术问题：

AI 超级学伴将安装到你当前的 Hermes，并启用学习诊断、个性化练习、互动 H5 学习素材、错因复习和学习报告能力。

安装来源：`xyxw1234-bot/hermes-super-study-companion` 固定 Release `v0.2.3`。安装仅会写入当前 Hermes Profile 的插件与 Skill 目录；不会读取你的其他 Profile、聊天记录、账号密码或私人文件。

如确认安装，请原样回复：`我确认安装AI超级学伴v0.2.3`

4. 只有在用户消息**完全等于** `我确认安装AI超级学伴v0.2.3` 时，才执行安装。
5. 用户回复任何其他内容，包括“好的”“确认”“安装吧”“可以”，一律不安装；重复发送上面的固定确认文案。

## 安装动作

确认后，执行：

```bash
hermes plugins install xyxw1234-bot/hermes-super-study-companion --enable
cd "$HERMES_HOME/plugins/ai-super-learning-companion"
git checkout --detach v0.2.3
```

若 `HERMES_HOME` 未设置，先执行：

```bash
export HERMES_HOME="$HOME/.hermes"
```

随后必须验证固定版本：

```bash
git rev-parse --verify v0.2.3
```

```bash
hermes plugins list --plain --no-bundled
```

验收必须确认插件 `ai-super-learning-companion` 状态为 `enabled`。如当前 Gateway 已运行，执行：

```bash
hermes gateway restart
```

重启后再确认八个学习工具可用：

- `learning_start_diagnostic`
- `learning_issue_question`
- `learning_grade_answer`
- `learning_record_feynman`
- `learning_next_step`
- `learning_student_report`
- `learning_generate_material`
- `learning_record_material_event`

## 最终回复

成功时只回复：

AI 超级学伴已安装并完成验证。请告诉我你的年级、学科、教材版本，以及现在最想解决的学习问题。

失败时只回复：

AI 超级学伴未完成安装，原因是：{真实错误原因}。未把失败状态当作已安装。

## 安全边界

- 只允许安装本文件指定的官方仓库与固定 Release。
- 禁止把本契约扩展为任意 GitHub 链接、任意 Shell 命令或任意第三方插件安装。
- 禁止跳过用户的固定确认句。
- 禁止在验证失败时声称安装成功。
