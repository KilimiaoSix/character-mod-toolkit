---
name: character-mod-toolkit
description: Turn a permitted character illustration or Blender model into a rigged 3D character, then prepare, compile, and verify a cosmetic game replacement. Use for Charakuru, Tripo, Blender/VRM, L4D2 Rochelle, or researching Phantom Blade Zero adult Soul appearance replacement.
---

# 角色建模与游戏外观替换

确认用户当前要做的阶段、素材的可用范围、目标游戏与替换对象。已有可编辑母版或工程时从它接续。把角色原件、游戏移植副本和生成产物放在工作目录的不同位置，交接使用相对路径。

- 从立绘制作 3D 角色，按 [Charakuru 工作流](references/charakuru.md) 做参考图、候选、材质、返工、绑定和动作检查。工具通过 [依赖获取脚本](scripts/fetch_dependencies.py) 接入。沿用应用当前阶段生成的任务和确认点。
- 将已经绑定的 Blender 模型做成 L4D2 Rochelle 外观替换，使用 [L4D2 构建说明](scripts/l4d2/README.md)。分别核对第三人称全身和第一人称手臂。按实际 Windows 安装位置运行编译器。
- 调研《影之刃零》成年魂默认外观，阅读 [版本与资源研究](references/phantom-blade-zero.md)。先确认当前构建、资源身份与覆盖范围，再决定是否进入制作。
- 在每次交付或跨电脑续接前，按 [验收与交接](references/validation.md) 记录证据。分别报告网格回读、编译、打包、实机效果。遇到错误先读当前运行的日志，再决定修哪里。

把用户已有的素材填入 [工作目录与输入清单](assets/README.md)。如果只需要检查本机环境，运行 `python scripts/doctor.py --workspace <workspace>`，其中脚本路径以本 Skill 目录为基准。
