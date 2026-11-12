# Character Mod Toolkit

把角色立绘做成可编辑的三维角色，然后准备游戏的外观替换。包含一个可安装的 Codex Skill、可单独运行的脚本和逐阶段的验收方法。

| 路线 | 内容 |
|---|---|
| 从立绘到 VRM | Charakuru、ImageGen、Tripo 和 Blender。覆盖多视图、候选、贴图、拆件返工、绑定、摆动和动作验收。 |
| 《求生之路 2》 | 已验证过的 Rochelle 移植思路、Blender 预处理与绑定、SMD/QC 和 VTF/VMT、Windows StudioMDL 和 VPK 工作流。 |
| 《影之刃零》 | 成年魂默认外观的可行性研究、资源槽和构建号核对步骤。 |

## 安装

需要 Python 3.10+。将仓库克隆到本地，在仓库根目录执行：

```shell
python scripts/install_skill.py --project "/path/to/your/project"
```

在 Codex 中打开项目根目录。示例请求：

> 使用 $character-mod-toolkit，从我提供的立绘制作角色。先检查参考图阶段，完成后停在候选选择。

也可以直接阅读 [Skill](skills/character-mod-toolkit/SKILL.md) 并运行脚本。以下命令从本仓库根目录运行。macOS 上可用 `python3`，Windows 上也可用 `py -3`。

```shell
python skills/character-mod-toolkit/scripts/doctor.py --workspace "/path/to/your/project"
python skills/character-mod-toolkit/scripts/fetch_dependencies.py --workspace "/path/to/your/project" charakuru vrm-addon
```

Charakuru 需要 Node.js 22+，后续建模和贴图取决于可用的 ImageGen、Tripo 与 Blender。获取脚本按锁定的发行版本或提交下载上游归档，核对 SHA-256 后放进本地 `deps/`。Windows 编译需要 Steam 的《求生之路 2》和 Left 4 Dead 2 Authoring Tools。

## 工作入口

- [立绘、建模与 VRM](skills/character-mod-toolkit/references/charakuru.md)
- [L4D2 预处理、骨架、材质与 Windows 构建](skills/character-mod-toolkit/scripts/l4d2/README.md)
- [跨电脑交接与验收](skills/character-mod-toolkit/references/validation.md)
- [成年魂外观替换研究](skills/character-mod-toolkit/references/phantom-blade-zero.md)
- [输入素材和工作目录](skills/character-mod-toolkit/assets/README.md)
- [项目经验与已验证范围](docs/case-notes.md)

## 第三方依赖

[依赖清单](skills/character-mod-toolkit/scripts/dependencies.json) 记录本次整理使用的版本。可按需获取 Charakuru、VRM Add-on、Rochelle 社区参考或 Blender Source Tools。Blender 和 Steam 工具请从各自的发布渠道获取。依赖仍受上游条款约束，本仓库的 MIT 许可证适用于本仓库的原创内容。 [依赖来源与许可](docs/dependencies.md)
