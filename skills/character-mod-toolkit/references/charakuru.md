# 从立绘做到可编辑角色和 VRM

这一阶段在 Charakuru 里管理角色工程，由 AI 分批执行图像生成、Tripo 与 Blender 操作。交接给游戏移植的是**带网格、UV、贴图与权重的 Blender 母版**。VRM 供角色动作和摆动验收。每次给 AI 一个阶段任务，连同本次要改的部位和验收方式一起交代。

## 环境和工程

1. 从工具包获取官方发行物。运行 `python "<SKILL_DIR>/scripts/fetch_dependencies.py" --workspace "<WORKSPACE>" charakuru vrm-addon`。当前工作流对应 Charakuru 1.1.1，应用位于工作目录 `deps/charakuru/`。也可直接使用 [Charakuru 官方 Releases](https://github.com/nanocle/Charakuru/releases) 的专用发行 ZIP。解压 GitHub 自动生成的源码 ZIP 无法代替该套件。
2. 确认 Node.js 22 或更高版本、能运行套件所需插件的 Blender、VRM Add-on，以及能执行图片生成和浏览器操作的 AI 环境。套件的本地 Blender 工作流可借助 Blender MCP。Tripo 使用用户授权的登录会话。用 `python "<SKILL_DIR>/scripts/doctor.py" --workspace "<WORKSPACE>"` 了解本机可用工具。不要根据安装包已下载就判断插件已启用。
3. 在套件目录执行 `npm start`，使用终端实际打印的本地地址。在应用里载入有权使用的全身参考图。PNG、JPEG、WebP 的套件上限为 20 MB。确定最终目标、角色特征和需要独立的配饰。保存项目目录，保留 `.charakit` 及关联的 `work/` 和 `exports/`。

如果当前环境只能执行本地脚本，先交付检查清单及确切缺少的能力，例如无法控制已登录的 Tripo 标签页。已完成的阶段可在能访问同一工程的电脑上续接。

## 应用请求与 AI 的交接

- 在当前阶段复制应用生成的请求，再发给 AI。请求包含当前任务编号、应用地址和本机命令。让发出请求的标签页保持打开。AI 使用请求里的 `scripts/agent-session.mjs begin`，等输出出现 `saved: true`，从同一响应读取工作目录和项目路径。失效请求重新从应用复制。换机后使用新电脑生成的请求。
- 需要时为当前请求调用 `status`、`progress`、`complete` 或 `fail`。按照当前任务产物决定何时登记与完成。生成服务的页面显示完成，仍需确认对应文件实际下载、可打开且已登记进当前项目。
- 候选生成、重贴图、重新绑骨可能消耗积分。按已获授权的阶段和额度执行，超出范围的尝试先说明预估。下载被浏览器、OS 或执行审批阻止时，先确认合法的手动保存路径或用户端设置。遇到权限拒绝，保留原进度和确切错误，避免切换凭据或反复提交。

例子：

```text
执行应用刚复制的这一个阶段请求。保留参考图里的发型、衣服和独立饰品。
本阶段结束后，给我正面和斜侧预览，标出需要我决定的地方。
下一阶段的积分支出等我确认后再开始。
```

## 阶段与验收

| 阶段 | AI 怎么做 | 应看到什么 |
| --- | --- | --- |
| 多视图 | 按图片请求，用 ImageGen 或等价工具制作带完整头发的无颈头部，以及穿衣、带颈的 T 姿势身体。各做正面、背面和角色自身左右侧。另用正、右侧、背面全身图对照比例。 | 头、身各四张图；左右定义统一；接缝、轮廓、颜色和配饰一致。原图没展示的区域，给用户确认推断出的细节。 |
| 候选模型 | 用通过的视图提交 Tripo，再把头、身候选分别登记到应用。1.1.1 的上游默认是 Smart Mesh P2.0，头和身各四候选、各 25,000 四边面，实际界面与额度以本次授权为准。 | 至少看正面、斜侧与背面。核对脸、发量、肢体和服装造型。用户分别选定头和身，再开始组装。 |
| 分件、UV、纹理 | 把外观分组和摆动分组分开记录。上游纹理组包括头发、头部、上身、下身和配饰，缺失部位可省略。用已确认的分件图和 Smart UV 做材质；组装时核对回传模型的组、方向、UV 和透明度。 | 正侧背都有材质，头颈接缝和位置对齐。导入和组装后保留可编辑材质，使用 MToon 的工作流检查其设置。裙摆可独立摆动，同时复用下身的服装材质。 |
| 比例和返工 | 在模型编辑里对照全身参考。以用户点名的局部问题返工。纹理完成后需要换候选时，用应用的项目副本流程保留原分支。 | 看头、身比例和接缝。确认修复范围与用户意图，再确认用于绑定的姿势和模型。 |
| 骨架和权重 | 按绑定请求向 Tripo 提交摆好位置的头、身。按上游流程暂时排除头发，回传时用骨位作为绑定依据，继续使用确认过的网格、UV 和材质。在 Blender 里检查姿势、手指及权重。 | 编辑版有 Armature、可靠的骨映射和蒙皮。正侧面检查肩、肘、髋、膝、踝。手、脚和装备接触点在游戏移植时还需重新对照目标骨架。 |
| VRM 物理与动作 | 恢复头发，为实际需要摆动的头发、裙摆等建立链和碰撞体。独立硬配饰可随头骨或指定亲本固定。保存工作 Blend，用应用的绑定完成流程生成动作确认 VRM。 | 开关物理核对部位的响应，比较摆动范围、碰撞和穿模。验证应打开的部件确实摆动，应固定的部件跟随亲本。完成动作确认再在应用中导出。 |

如果发夹和头发已融合，先做去除发夹的头部参考图，重新选出无残留的头模，再以独立网格重建发夹。给用户分别看关闭发夹时的刘海，以及装回后同角度的正面和斜侧。需要改表情时使用套件的 `avatar-expression-authoring` 工作流，为表情保留单独验收点。

对齐比例时先核对视角、缩放和脚底基准。叠图有重影时，分别单独显示参考和模型，再开启叠图对齐头顶、肩、袖口、裙边和鞋底。侧面再确认头颈与躯干的前后位置。

## 应用内脚本位置

以下相对路径在获取后的 Charakuru 目录中。调用参数与文件名以应用当前请求和对应的上游 Skill 为准。

| 操作 | 上游入口 |
| --- | --- |
| 保存应用状态与更新阶段进度 | `scripts/agent-session.mjs` |
| 登记四向部件图、全身比例参考、Tripo 资源 | `scripts/update-images.mjs`、`scripts/update-three-views.mjs`、`scripts/tripo-project.mjs` |
| 导入骨位、传递权重和配置摆动 | `scripts/import-bones.mjs`、`scripts/run-local-job.mjs`、`scripts/transfer-weights.py`、`scripts/spring-setup.py` |
| MToon、登记 Blend 和评审模型、物理校验 | `scripts/mtoon-export.py`、`scripts/update-model.mjs`、`scripts/verify-springs.mjs` |

## 本地检查与输出交接

绑定工作文件通常是 `work/character.blend`，动作确认版 `work/review.vrm`。正式导出后，上游在 `exports/` 下保存 `avatar.blend` 和 `avatar.vrm`。记下哪一版实际通过验收。游戏移植从完整的已验证 Blend 或中性骨架 FBX 工作副本开始。手动检查贴图可从原目录载入或已打包在 Blend 中，再交给 Windows 或另一台电脑。VRM 的 MToon 和 SpringBone 设置需要按目标游戏的着色与物理系统适配。

可用 [inspect_project.py](../scripts/charakuru/inspect_project.py) 调用官方解包器检查本地归档。它在临时目录验证并解包，随后删除临时副本。大项目需要相应的临时空间。先获取官方套件再执行，替换三个路径占位符：

```text
python "<SKILL_DIR>/scripts/charakuru/inspect_project.py" --kit-root "<WORKSPACE>/deps/charakuru" "<PROJECT>/project.charakit"
```

交接时可加 `--require-review` 来确认归档里已经登记匹配的 Blend、VRM 和摆动检验记录。该命令检查文件与已存结果的对应关系，外观和游戏内表现仍应实际查看。要对导出的正式 VRM 重新运行物理检查，使用套件的 `scripts/verify-springs.mjs` 与当前项目真实的 `spring-plan.json`。不要拿旧模型的固定骨名和参数套新角色。

本次案例曾验证一份完成了摆动设置的工程，记录了 55 个导入的骨位及 10 条摆动链。这些是一个角色的记录，其他角色的骨数与物理分组按实际模型确定。

## 上游入口

- [Charakuru 中文教程](https://github.com/nanocle/Charakuru/blob/main/docs/tutorial.zh-CN.md)与[浏览器操作说明](https://github.com/nanocle/Charakuru/blob/main/docs/browser-use.zh-CN.md)。本地以已锁定发行包的 `docs/`、`AGENTS.md` 为准。
- 套件内 `skills/character-parts-images/`、`skills/character-three-views/` 与 `skills/character-material-brushup/` 说明图像素材和验收。
- 套件内 `skills/tripo-agent-workflow/`、`skills/tripo-studio-download/` 与 `skills/charakit-project/` 说明候选、组装、合法下载与登记。
- 套件内 `skills/avatar-weight-transfer/`、`skills/avatar-spring-setup/` 与 [VRM Add-on 官方发布](https://github.com/saturday06/VRM-Addon-for-Blender/releases) 说明 Blender 权重、摆动、验证和导出。
