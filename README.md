# AI 超级学伴 · Hermes 插件

面向 Hermes 与飞书节点引擎的真实学习内核：诊断、知识点地图、BKT 掌握度、题目答案隔离、错因证据、费曼检查、间隔复习、互动 H5 素材与学习报告。

## 安装

在用户明确授权后执行：

```bash
hermes plugins install xyxw1234-bot/hermes-super-study-companion --enable
hermes gateway restart
```

重启后，Hermes 会获得 `study_companion` 工具集。安装后发送“开始学习”即可由 AI 导师建立诊断路径。

## 安全边界

- 标准答案只保存于学习内核，绝不回传到对话中。
- 模型不能自行宣告“已掌握”；掌握度由 BKT、练习证据和费曼检查共同决定。
- 学习数据默认保存在 `~/.hermes/study-companion`；可通过 `HERMES_STUDY_DATA_DIR` 指向节点引擎受控存储卷。
- 互动 H5 默认生成到 `~/.hermes/study-materials`；可通过 `HERMES_STUDY_MATERIAL_DIR` 指向受控的静态文件卷。宿主页面应接收 H5 的 `postMessage` 并调用 `learning_record_material_event` 回写事件。
- 只使用明确授权的教材、教辅、题目和用户上传材料。

## 来源与许可证

本项目参考了 DeepTutor 的掌握式学习状态机设计与 OATutor 的 BKT、自适应选题、分层提示理念；本项目代码为独立实现。DeepTutor 为 Apache-2.0，OATutor 为 MIT。详见 NOTICE。
