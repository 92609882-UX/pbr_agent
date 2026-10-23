> **License**: 本文档受 MIT License 保护 (Copyright (c) 2026 渐行渐远)。
> ⚠ 本包**只含文档与脚本**，不含任何贴图图片。贴图部分受上游 mod 条款约束，详见文末「授权范围」。

# PBR 材质包制作 · 交接包

**目的**：把 `G:\PBR` 项目中与 **Minecraft LabPBR 材质包制作方法**相关的全部文档与 Agent 技能文件，
打成一个自包含的知识包，可直接交给其他人（或交给 AI 助手）接手。

**打包日期**：2026-09-11 　**适用**：Minecraft 1.21.1 NeoForge + Iris + **LabPBR 1.3**

---

## 一、先读哪份

| 顺序 | 文件 | 读它的理由 |
|---|---|---|
| **1** | `01-总纲\PBR材质包制作总纲.md` | **单一入口**。18 章覆盖完整流程：素材摸底 → 放大分区 → Designer 建图 → 蒙版进阶 → 导出 → 打包 → 验证门禁，另含通道权威速查、25 条故障字典、必须求助的决策点。**先读这份就有全貌** |
| 2 | `04-参考资料\规范\ShaderLABS-LabPBR-Material-Standard.wiki.txt` | **LabPBR 规范原文**。通道语义的**唯一权威**，总纲里所有通道取值最终都回到这份 |
| 3 | `02-权威文档\Agent约束-Designer制作流程.md` | Designer **节点级**流程纲领（`_n` / `_s` 四通道链路、金属与几何蒙版、箱型 UV 裁切）。含 19 张节点连线示意图 |
| 4 | `02-权威文档\PBR制作注意事项与Agent约束.md` | **硬性约束清单**。开工前必做、高度设计规则、验证方法、禁止事项、炼金术箱子实战复盘 |
| 5 | `03-版本与工作记录\WORKLOG-工作过程与注意点.md` | **踩坑全记录**（P1~P7）。P1「法线死平」的根因链是最值得先看的一段 |
| 6 | 其余 | 按需查：工程参数、Designer 实操、Python API、无头 CLI、版本说明 |

> **不确定时**：改**通道含义**查 `04-参考资料\规范\`；改**放大/分区/强度**查 `02-权威文档\PBR材质包制作经验与流程规范.md`。

---

## 二、包内容

```
PBR材质包制作-交接包\
├── README-交接说明.md              ← 本文档
├── LICENSE                         ← MIT（代码/文档部分）
├── 01-总纲\
│   └── PBR材质包制作总纲.md            ★ 单一入口，先读这份
├── 02-权威文档\
│   ├── Agent约束-Designer制作流程.md      Designer 节点级流程（本包核心方法）
│   ├── Agent约束-LabPBR通道备忘.md        通道语义速查与材质参考表
│   ├── PBR材质包制作经验与流程规范.md     工程参数、交付检查清单、labPBR 声明根因
│   ├── PBR制作注意事项与Agent约束.md      硬性约束清单 + 实战复盘
│   ├── Substance命令行无头流程.md          不开 GUI 跑 cook/render
│   ├── Substance 3D Designer 使用总结.md   Python API 用法、坑位清单、内外分工
│   ├── Substance 3D Designer 操作流程.md   Designer 手工实操版
│   ├── LICENSE-授权范围说明.md            ⚠ 授权边界，务必读
│   └── Pictures\                        19 张示意图（见下方说明）
├── 03-版本与工作记录\
│   ├── WORKLOG-工作过程与注意点.md
│   ├── EnchantingInfuser-PBR-v6-红毯织物优化说明.md
│   ├── V7-紫水晶立体化说明.md             （`_n` A 通道高度的具体做法）
│   ├── README-PBR-v1说明.md
│   └── README-PBR-v4说明.md
├── 04-参考资料\
│   ├── README-参考资料索引.md           外部资料全索引（含来源链接）
│   ├── 规范\      LabPBR 规范原文、实现要求、解码 GLSL、oldPBR 差异
│   ├── 中文资料\   规范中文翻译与制作笔记
│   ├── 工具\       PixelGraph / Textureslap / BumpToNormalMap 等工具文档
│   └── 光影\       Photon 等光影端的 labPBR 支持说明
├── 05-工具脚本\
│   └── sbs_cli.py                  Substance 无头流水线（cook / info / render / run）
└── 06-Skills\
    ├── pbr-texture-pipeline.md     Agent 技能文件（可直接装入 AI 助手）
    └── 安装说明.md                  怎么装、装到哪
```

### 关于 `02-权威文档\Pictures\`（19 张图）

原项目里 `Agent约束-Designer制作流程.md` 有 **20 处图片引用**（`./Pictures/1.png` 等），
但项目文档目录中**并没有 `Pictures\` 文件夹**——图只存在于 `项目素材\agent.zip` 里，所以原文档的图**全是断链**。

本包已把图从 `agent.zip` 中取出并放在 `02-权威文档\Pictures\`，**相对路径与原文档一致，打开即可正常显示**。
（`1.png`~`9.png` 是 Pixel Processor 与 Blend 节点的连线截图；`barrel_bottom*.png`、`stone_bricks*.png` 是几何蒙版示例。）

---

## 三、环境前提

方法本身与机器无关，但要**实际跑起来**需要：

| 项 | 说明 |
|---|---|
| Substance 3D Designer | 本流程基于 **14.1.2**。其他版本节点 ID / 参数名可能不同，用 `probe_*.py` 重新确认 |
| 命令行工具 | `sbscooker.exe` / `sbsrender.exe` / `sbsbaker.exe` / `sbsupdater.exe`，随 Designer 安装 |
| Python | 3.10+，含 `numpy` / `Pillow`；`cv2` 可选（用于 `GaussianBlur` 替代 scipy） |
| Minecraft 侧 | Iris + 支持 LabPBR 的光影（Complementary Reimagined / BSL / Photon 等） |
| 游戏目录 | 资源包放 `resourcepacks\`，**同一 mod 的旧版本包要关掉** |

> ⚠ **两条最容易卡住的硬事实**：
> 1. Designer 的 `sd` Python API 是**进程内 API**，外部 Python `import sd` 必然失败，脚本必须在 Designer 内运行。
> 2. **shader 配置只在游戏启动时读取**——游戏内改配置或重载资源不会生效，必须重启游戏。

`05-工具脚本\sbs_cli.py` 用 `--designer-home` 参数或 `DESIGNER_HOME` 环境变量指定 Designer 安装路径。

---

## 四、怎么用这些 Skills

`06-Skills\pbr-texture-pipeline.md` 是给 **AI 助手**用的技能文件（带 YAML frontmatter）。
装好之后，助手在涉及 Minecraft PBR / LabPBR / Designer 的任务时会自动加载这份知识。

**装到 DeepSeek Harness（DSH）**：

```powershell
Copy-Item "06-Skills\pbr-texture-pipeline.md" "$env:USERPROFILE\.dsh\skills\" -Force
```

**装到 Reasonix**：

```powershell
Copy-Item "06-Skills\pbr-texture-pipeline.md" "$env:USERPROFILE\.reasonix\skills\" -Force
```

DSH 会扫描 `~/.dsh/skills` 与 `~/.agents/skills`，**支持平铺 `.md` 文件**（不必建子目录），
且技能目录有文件监听，**拷进去即时生效、无需重启**。

> 也可以直接把 `01-总纲\PBR材质包制作总纲.md` 的内容粘进任意 AI 助手的对话或系统提示——
> 它就是为「投喂给 Agent」写的：硬约束、精确参数、可执行校验、故障→成因→处置三段式。

---

## 五、授权范围（务必先看）

本包内**文档与脚本的授权相互独立**，不能一概而论：

| 内容 | 授权 |
|---|---|
| 本包**全部 `.md` 文档**、`04-参考资料\` 下的规范原文与工具文档、`05-工具脚本\sbs_cli.py` | 本项目文档/脚本为 **MIT**（© 2026 渐行渐远）；`04-参考资料\` 是**外部公开资料的本地副本，版权归各原作者**，见其中 `README-参考资料索引.md` 的来源链接 |
| LabPBR 规范原文 | 来自 shaderLABS Wiki，版权归原作者 |

**本包不含任何贴图图片**，因此不涉及上游 mod 素材条款。

⚠ 若你另外分发**材质包成品**（含 `_n.png` / `_s.png` / 预览图），那部分**不是 MIT**：
它是 mod 官方贴图的衍生作品，受 **MPL-2.0（代码）+ © 2023-2025 @heyitsfuzs 保留一切权利（素材）** 约束，
不能以 MIT 名义重新授权或公开分发。详见 `02-权威文档\LICENSE-授权范围说明.md`。

---

## 六、本包不含什么

| 未收录 | 原因 |
|---|---|
| 材质包成品（`*PBR-128x-v7.zip` 等） | 属**交付物**而非方法文档；且含贴图，受上游条款约束（见上） |
| `参考资料\参考材质包\`（Vanilla-Normals-Renewed 等） | 第三方材质包，体积大（10M+）且为他人作品 |
| mod jar、光影包、解包 jar | 第三方二进制，需要时从原站下载 |
| 各生成脚本（`gen_pbr_*.py` / `gen_projecte_*.py` / `build_*.py`） | 与本项目**具体方块强耦合**，换目标 mod 后不可直接复用；其中的**方法与参数**已完整写进文档 |

> 需要生成脚本时：`02-权威文档\Substance 3D Designer 使用总结.md` 第六节列了脚本清单与各自作用，
> `Agent约束-Designer制作流程.md` 与总纲 §6~§8 给了完整的节点链与参数，可据此重建。

---

## 七、接手建议

1. 先读 `01-总纲` 通读一遍建立全貌，再按需跳回细节文档。
2. **动手前必须先读模型 JSON 确认 UV**——这是本方法里返工率最高的一步
   （总纲 §2.1；方块实体渲染器的 UV 是硬编码的，不看渲染器一定会错）。
3. 沿用「先做结构平台、再做细节」的高度设计顺序，不要直接把原图灰度拉伸成高度。
4. 每张图生成后**打印通道 min/max/mean** 做数值验证，不要只看成品图。
5. 落地困难时优先查总纲 §15 故障字典（25 条「现象 → 成因 → 处置」），多数问题已有记录。
