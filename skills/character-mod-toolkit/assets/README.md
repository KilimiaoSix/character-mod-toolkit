# 工作目录与输入清单

推荐让工作目录与工具仓库相邻。用用户有权使用的输入替换示意文件名。

```text
my-character/
  input/
    character.png
    character.blend
  deps/
  01_blender/
  04_compile/
  addon/
  build/
```

- `character.png` 用于从立绘制作。准备全身图，记录左右不对称、被遮挡和需要单独建模的饰品。
- `character.blend` 用于从现成模型续接。保留原始母版、内嵌或配套贴图、UV、有效骨骼权重和部件命名。仅有 VRM 时先在 Blender 导入并回读关键结构。
- 保存选定的参考图、模型候选、各阶段输出与最终可编辑文件。检查角色实际骨架、目标参考姿势和材质映射，再填 L4D2 配置。
- `deps/` 存第三方上游工具和参考。目录由 [获取脚本](../scripts/fetch_dependencies.py) 在本地建立。
- L4D2 的可编辑文件、QC/SMD、VTF/VMT、编译日志和产物按 [构建说明](../scripts/l4d2/README.md) 使用。游戏原文件、外部工具与账号资料留在各自原位置。
