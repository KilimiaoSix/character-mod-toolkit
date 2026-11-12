# 《影之刃零》成年魂外观替换

这是版本相关的调研路线。工具包尚无针对《影之刃零》的构建器，也没有在该游戏内验收工具包自己的模型。

## 首个可测版本

选定一个 Windows 游戏版本和一个主线成年魂存档，以默认服装下的可操控角色为目标。成年序章、少年魂、其他服装、过场面部和毛发布料物理分别立项。替换后仍使用游戏的骨骼动画、装备挂点和原有受击行为。

| 已查到的资料 | 能支持的结论 |
|---|---|
| [S-GAME 补丁公告](https://pbz.s-game.com/en-US/news/patch-notes-2026-11-03/) · [Steam 构建记录](https://steamdb.info/patchnotes/26367565/) | 补丁版本为 `1.0302256`，2026 年 11 月 4 日的 Steam 构建记录为 `26367565`。以本机实际构建号为准。 |
| [Novice Wanderer Outfit 作者页](https://www.nexusmods.com/phantombladezero/mods/894) | 作者声明替换成年魂默认身体、头脸和头发，安装说明只列资源三件套。该页面未说明对过场和其他服装的覆盖。 |
| [Berenica 作者页](https://www.nexusmods.com/phantombladezero/mods/804) | 作者报告在 Steam `26367565`、UE `5.7.4` 验证纯资源替换，使用 `.pak`、`.utoc`、`.ucas`，面部为静态。不能由此推定自己的资源路径和筛选条件。 |
| [陈千语替换作者页](https://www.nexusmods.com/phantombladezero/mods/204?tab=description) | 有指定服装的资源包加 UE4SS 先例。作者记录了原服装偶尔在过场出现。 |
| [PBZ UE4SS 社区兼容包](https://www.nexusmods.com/phantombladezero/mods/5) · [同构建运行记录](https://www.nexusmods.com/phantombladezero/mods/173?tab=files) | 作者报告在 Steam `26367565` 使用 PBZ 专用 UE4SS `1.0.3`。这条记录说明加载器组合曾工作，不能代替角色模组测试。其他商店版本单独核对。 |

## 准备骨骼网格

1. 记录发行平台、构建号和角色状态。从当前构建核对成年默认外观的身体、头脸、头发、服装与配件槽，确认哪些资源和序章、其他服装或过场共用。早期作者工作流中的 `Hun_Body_Simple` 与 `Hun_Head_New` 是待核对的线索。 [作者制作记录的资产映射段落](https://github.com/ccd775/GameModdingKnowledge/blob/main/games/phantom-blade-zero/BUILD_PIPELINE.md#L188-L196)
2. 用有权使用的当前参考骨架与参考姿势，对齐原始 Blender 模型。保留骨骼名称、父子层级、参考变换、手指、脚底和装备所需骨骼与挂点。对于多部件角色，先确认哪个网格驱动动画、哪个网格跟随姿势，再分配部件。若缺少可靠的目标参考，先报告缺失的骨架或外观槽证据。 [Epic FBX 骨骼网格流程](https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-skeletal-mesh-pipeline-in-unreal-engine?application_version=5.7) · [Epic 模块化角色](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-modular-characters-in-unreal-engine)
3. 从模型母版取网格、UV、底色图及可复用权重，在目标骨架上重绑。检查手腕、膝盖与持握姿态。独立饰品可刚性跟随头骨。首版先用普通蒙皮表现头发和裙摆。分别验证目标材质槽、透明度、色彩空间和虚拟纹理预期，再考虑 Chaos 布料或面部形变。 [Epic 骨架兼容](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletons-in-unreal-engine) · [Epic 布料工具](https://dev.epicgames.com/documentation/en-us/unreal-engine/clothing-tool-in-unreal-engine)

## 打包与实机边界

- 目标槽唯一且纯资源包能精确覆盖时，可用匹配游戏构建的 Unreal 工具烘焙自制资产并检查 IoStore 产物。已有作者案例使用同批生成的 `.pak`、`.utoc`、`.ucas`，资源放在游戏的 `ProjectPBZ/Content/Paks/~mods/`。记录三文件的来源构建和校验值。 [Epic 打包说明](https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-your-project) · [作者安装说明](https://www.nexusmods.com/phantombladezero/mods/894)
- 若资产被其他状态共用而需要运行时筛选，先验证本地玩家、成年主线状态和默认外观三个条件，再用目标版本支持的加载器与 API 完成范围控制。读档、重生、换装后重新判断，并验证原版外观能恢复。加载器不可用或目标资产无法合法取得时，记录阻塞并暂停该路径。 [UE4SS Lua API](https://docs.ue4ss.com/lua-api.html)
- 实机先只启用当前外观包，按 [通用验收清单](validation.md) 走读档、跑动、闪避、单双手持握、受击、重生和换装。分别看原版脸、发或服装是否叠出、持握是否对位、受击是否正常。只声明已在该平台及构建亲自核对的场景。
