# 依赖来源与许可

| 依赖 | 用途与获取方式 |
|---|---|
| [Charakuru](https://github.com/nanocle/Charakuru/releases/tag/v1.1.1) | 用获取脚本下载上游 v1.1.1 发布 ZIP。沿用其 source-available 许可，保留上游许可文件。 |
| [VRM Add-on for Blender](https://github.com/saturday06/VRM-Addon-for-Blender/releases/tag/v4.10.4) | 获取脚本保留上游 v4.10.4 Extension ZIP，在 Blender 中按上游文档安装。 |
| [HedyL Rochelle 模板](https://github.com/hedyl2/qctemplate-l4d2/tree/ada329298ecc5319a166279b3ad6397ea2249fed) | 获取脚本按提交取得 Rochelle 参考及 GPL-3.0 许可。社区模板包含 Valve 参考材料，用于在本机对齐姿势和生成编译输入。游戏资产的权利归相应权利人。 |
| [Blender Source Tools](https://github.com/Artfunkel/BlenderSourceTools/tree/3d5fd9bf681547d86fa369715a0e8dd6013edcb7) | 可选，用于 Source 格式回读和检查。获取脚本保存上游插件目录。 |
| [Blender](https://www.blender.org/download/)、[Node.js](https://nodejs.org/en/download) | 从官方渠道准备。 |
| [Steam 版 L4D2](https://store.steampowered.com/app/550/Left_4_Dead_2/) 与 [制作工具配置](https://sites.google.com/view/zeqmacawstidbits/tutorials/modding-a-left-4-dead-2-survivor/setting-up-tools-for-modding/setting-up-tools-found-on-steam) | 从 Steam 库安装游戏和 Left 4 Dead 2 Authoring Tools。Windows 脚本使用该游戏版本配套的 StudioMDL 和 VPK 工具。 |
| [Tripo Studio](https://studio.tripo3d.ai/) | 使用自己的账号，确认本阶段操作和消耗。ImageGen 则由具备该能力的 AI 环境提供。 |

工作区里的立绘、模型、项目归档、编译结果与游戏参考属于本地输入和产出。公开分享前检查对应资产的来源与使用许可。

归档可用 GitHub CLI 或 curl 获取。离线使用时可传 `--archive-dir <目录>`，目录内使用锁定表的 `filename` 或对应的上游发布文件名。GitHub 重新生成提交归档时可能改变 ZIP 的字节表示，遇到 SHA-256 不匹配时应重新核对上游提交和归档内容。
