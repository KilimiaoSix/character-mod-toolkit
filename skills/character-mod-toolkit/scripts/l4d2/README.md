# Left 4 Dead 2 Rochelle 替换

输入是已检查动作的角色 `.blend`，包含一套 Charakuru 人形骨架、已蒙皮的网格、UV 和不透明 MToon 材质。这个流程按 Rochelle 的静置姿势重新定位和分配权重，使用原版动画模型。先在 macOS 或 Windows 上准备源文件，再用 Windows 的 Steam 工具编译。

## 准备第三人称模型

在有 Blender、已启用 [VRM Add-on for Blender](https://github.com/saturday06/VRM-Addon-for-Blender) 的电脑上运行。下列命令使用 Bash，先替换路径。`profile.json` 中的网格名和材质名必须和 Blender 一致。示例的 `decimate` 会简化身体网格，保留原有网格时设为 `{}`。`meters_per_unit` 是角色场景中每 Blender 单位对应的米数。

```bash
SKILL=/path/to/character-mod-toolkit/skills/character-mod-toolkit
WORK=/path/to/rochelle-workspace
SOURCE=/path/to/character.blend
L4D2="$SKILL/scripts/l4d2"
mkdir -p "$WORK"
cp "$L4D2/profile.example.json" "$WORK/profile.json"
# 编辑 $WORK/profile.json
python "$SKILL/scripts/fetch_dependencies.py" --workspace "$WORK" rochelle
python -m pip install -r "$L4D2/requirements.txt"

blender -b "$SOURCE" --python-exit-code 1 -P "$L4D2/prepare_model.py" -- --workspace "$WORK" --profile "$WORK/profile.json"
blender -b "$WORK/01_blender/prepared.blend" --python-exit-code 1 -P "$L4D2/bind_rochelle.py" -- --workspace "$WORK" --profile "$WORK/profile.json"
blender -b "$WORK/01_blender/prepared.blend" --python-exit-code 1 -P "$L4D2/extract_materials.py" -- --workspace "$WORK" --profile "$WORK/profile.json"
python "$L4D2/build_materials.py" --workspace "$WORK"
python "$L4D2/generate_qc.py" --workspace "$WORK" --profile "$WORK/profile.json"
python "$L4D2/check_workspace.py" --workspace "$WORK"
```

依赖脚本将外部 [HedyL 的 L4D2 QC 模板](https://github.com/hedyl2/qctemplate-l4d2) 放在 `deps/community-hedyl2/survivor_producer/`。保留这个相对路径。`01_blender/prepared.json` 记录减面的表面偏差，`01_blender/rochelle_world.blend` 用于检查 Rochelle 骨架下的摆姿，`04_compile/` 包含 QC 和 SMD。材质工具把基础色转成 VTF/VMT。透明、裁切 alpha、Source 专用高光及法线需要单独制作材质。骨骼映射依赖脚本中明确列出的 Charakuru 骨名和权重回退规则，其他骨架需要人工重绑。

## Windows 编译和打包

将整个工作目录和工具包移到 Windows。在 Steam 安装 Left 4 Dead 2 和 Left 4 Dead 2 Authoring Tools，`-GameRoot` 指向包含 `bin` 和 `left4dead2` 的安装目录。PowerShell 中运行以下命令。仅需编译时省略 `-Pack`。

```powershell
$Kit = 'C:\Modding\character-mod-toolkit'
$Work = 'C:\Modding\rochelle-workspace'
$Game = 'C:\SteamLibrary\steamapps\common\Left 4 Dead 2'
$L4D2 = Join-Path $Kit 'skills\character-mod-toolkit\scripts\l4d2'
& (Join-Path $L4D2 'Build-Rochelle.ps1') -Workspace $Work -GameRoot $Game -Pack
```

产物位于 `build/<本次构建 ID>/`，其中包含 StudioMDL 日志和 `rochelle_character.vpk`。将 VPK 放进游戏安装目录的 `left4dead2/addons/` 后，在地图内以 Rochelle 实测跑动、蹲伏和倒地姿势，并观察肩肘、裙摆及头发穿模。

## 可选第一人称手臂

第一人称使用独立的 `models/weapons/arms/v_arms_producer_new.mdl`。只编译第三人称时，玩家视角会沿用原版手臂。按原版第一人称骨架及 Source 坐标制作手臂网格 `04_compile/mesh/first_person_arms.smd` 和同骨架的静置动画 `04_compile/mesh/first_person_idle.smd`，材质使用已生成的 VTF/VMT。把 `first_person.qc.example` 复制到 `04_compile/rochelle_arms.qc`，用下面的命令同时打包。以 Rochelle 第一人称检查持枪、近战和换弹。

```powershell
$ArmsQc = Join-Path $Work '04_compile\rochelle_arms.qc'
& (Join-Path $L4D2 'Build-Rochelle.ps1') -Workspace $Work -GameRoot $Game -FirstPersonQc $ArmsQc -Pack
```

已在 macOS 用完整角色验证 Blender 处理、SMD 导出、VTF/VMT 生成和 QC 静态预检。该测试包含 7 个 SMD、76 根参考骨骼及 5 个不透明材质。PowerShell 包装脚本通过模拟编译器测试了第三人称、加入手臂及编译失败三种情况。Windows StudioMDL、VPK 打包及游戏内显示仍需实测。
