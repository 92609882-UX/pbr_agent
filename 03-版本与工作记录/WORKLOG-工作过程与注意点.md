> **License**: 本文档受 MIT License 保护 (Copyright (c) 2026 92609882-UX|渐行渐远)。
> 注: 包含图片/贴图素材的部分受上游 mod (MPL-2.0, © heyitsfuzs) 约束, 详见根目录 LICENSE。

# EnchantingInfuser PBR 材质包 — 工作过程与注意点记录

> 项目：为 `EnchantingInfuser-v21.1.4-1.21.1-NeoForge.jar`（附魔灌注台 mod）制作 128×128 LabPBR PBR 材质包
> 环境：Windows 11 / Python 3.10 + numpy + Pillow + cv2 / Substance 3D Designer 14.1.2（D:\）仅作参考
> 目标出图：`_n.png`（法线/AO/高度）+ `_s.png`（光滑/金属/SSS/发光），Iris/LabPBR 1.3 标准
> 记录日期：2026-09-06

---

## 一、任务拆解与工具链决策

### 1.1 两条可执行路线

| 路线 | 工具 | 成本 | 结论 |
|---|---|---|---|
| A. 纯 Python 复现 | numpy/PIL/cv2 | 零安装，全自动 | **实际采用** |
| B. Substance Designer 原生工作流 | Designer 14.1.2（D:\ 已装） | 需 GUI 交互，不便于批量 | 未采用（脚本化受限于进程内 API） |

最终方案：以 manual（agent_main.md）的 Designer 节点语义为**数值纲领**，用 Python 确定性复刻每步节点，并用蒙版/分区实现进阶技法。注意 Designer 官方 Python API 是**进程内 API**（`import sd` 只能在 Designer 自己的解释器跑），无法黑盒调用——这是当初选 A 的核心理由之一。

### 1.2 环境实测结果（做前必查）

- ✅ Python 3.10.11 / PIL 11.3 / numpy 2.2.4 / cv2 4.11.0
- ❌ scipy **未装**（手动改用 cv2.GaussianBlur 替代，避免额外安装）
- ✅ Substance Designer 14.1.2 在 `D:\Substance 3D Designer\`（带内置 python311 + resources/python/samples 样例）
- ✅ 游戏实测实例：`F:\PCL\versions\材质包测试\`（NeoForge 1.21.1 + Iris 1.8.12）

---

## 二、素材摸底（第一步必须做）

### 2.1 解包 jar 结构

jar 共 176 条目。关键发现：

```
assets/enchantinginfuser/
├── blockstates/          2 方块 (enchanting_infuser / advanced_enchanting_infuser)
├── models/block/         继承 minecraft:block/enchanting_table
├── textures/block/       6 张 16×16 (2 方块 × top/side/bottom)
├── textures/entity/      1 张 64×32 (书, 进 blocks 图集)
└── textures/gui/         1 张 GUI (不做 PBR)
```

### 2.2 模型 UV（决定贴图分区逻辑）

原版 `enchanting_table.json`（从 1.20.1 原版 jar 提取验证）关键 UV：

- **side 面：`uv: [0,4,16,16]`** —— 侧贴图**顶部 4 行透明，永远不会被采样**
- top/bottom 面：`uv: [0,0,16,16]` 全采样
- 方块本体只有 1 个 element（立方体），无复杂箱体拆卷

**注意点**：side 图顶 4 行透明区会在 mipmap 采样时污染可见边缘 → 生成时必须在此区 RGB 清零。

### 2.3 贴图色调解析（分区依据）

手工 dump 16×16 像素 + 色相聚类，得出 6 个材质分区：

| 分区 | 代表色 | 语义判断 |
|---|---|---|
| gold 金框 | #fad64a / #e9b115 / #dc9613 | 抛光金属金（G=231 预设） |
| red 红毯 | #a22929 / #952221 / #8f2020 | 布料/羊毛（高孔隙） |
| purple 魔法石 | #6d4eaa / #54398a / #6748a2 | 半透宝石（SSS 区间） |
| obsidian 黑曜石 | #000001 / #06030b / #100c1c | 玻璃质高光泽 |
| rune 符纹 | #8308e4 / #6006ab / #2b0178 | 凹刻 + 弱发光（A=40） |
| iron 铁灰（仅进阶版顶/侧角） | #737173 / #5a575a / #3c3232 | 铁金属（G=235） |

> 进阶版与普通版构图**完全相同**，仅角部紫色 → 灰色，因此可作为独立分区处理。

---

## 三、生产管线实现（gen_pbr 系列）

### 3.1 流程总览

```
16x16 原图 → 邻近放大 ×8 → 128×128
  ├─ 灰度 → Auto Levels → Levels(0.4-0.6) → Normal(Int=3, OpenGL) → RGBA Split
  │    → PP-R / PP-G 修正 → Merge → Normalize → R,G        [_n R,G]
  ├─ Levels → HBAO(Height Depth) → _n.B                      [_n B]
  ├─ Levels(200/255..1, mid 0.35) → 边缘保满高 → _n.A        [_n A] (v1)
  ├─ 分区平台高度 (v2: 金0.98/红0.72/紫0.85/曜石0.62/符纹0.30/铁0.92) → _n.A  (v2)
  └─ 分区材质通道 → _s R/G/B/A
```

### 3.2 节点语义数值对照表（manual → 实现）

| manual 节点 | 参数 | Python 实现 |
|---|---|---|
| Grayscale Conversion | - | `0.2126R+0.7152G+0.0722B` |
| Auto Levels | 归一化 | `(g-min)/(max-min)` |
| Levels (A) | Out 0.4-0.6 | 线性映射 + mid 伽马 |
| Normal | Intensity=3, OpenGL, ForceAlpha1 | 中心差分 + 归一化 |
| R-Pixel Processor | 邻接修正 | `if n1>0.5: g else (g>0.5? 0.5 : g)` |
| G-Pixel Processor | 邻接修正 + 反相 | `if n1<=0.498: g else (g<=0.498? 0.5 : g)` 后取负 |
| HBAO | Height Depth=0.03 (v1) / 0.15 (v2) | 8 向 × 4 半径遮蔽采样 |

---

## 四、踩坑全记录（本项目的真正价值）

### 🔴 P1：法线 R/G 死平（最严重，修复两次才成功）

**现象**：第一版 `_n` 的 R/G 通道输出 `min=126 max=128`——法线贴图等于空白，PBR 立体感完全不存在（这就是用户"看不出 PBR 效果"的根因之一）。

**根因链**：
1. `normal_from_h` 用 `s = intensity/255` 缩放差分 → 输入是 **0-1 浮点**高度，不是 0-255 灰度 → 差分全在 ±0.01 量级 → 归一化后 nx≈0
2. 8×8 硬块贴图（16×16 放大 8 倍，块内同值）→ **块内差分恒为 0**，只有块边界有值
3. PP_R/PP_G 的钳制逻辑进一步把边界值抹掉（`g>0.5` 条件对微弱信号失效）

**修复**（三次迭代）：
1. 差分后缩放改为 `intensity*2.0`（匹配 Designer 0-255 域语义）→ R/G 达到 50~205
2. 法线差分前对高度做强平滑 `gauss_blur(5.0)`
3. PP 逻辑保留但依赖前两步已修复的输入质量

**经验**：写数值管线时**域混用**（0-1 vs 0-255）是最隐蔽的 bug 来源。每次生成后必须打印通道 min/max/mean 验证，不能只看成品图。

### 🟠 P2：透明区 RGB 泄漏（mipmap 污染）

**现象**：side 贴图 top 4 行透明区里，RGB 通道填了法线/AO 数据（`transparent_rgb_leak=True`）。

**危害**：mipmap 采样时将透明区数据模糊进可见边缘 → 金框边缘出现错误的法线渐晕。

**修复**：`n_arr[~inside, :3] = 0.0`，`_s` 同理。

**验证**：每张输出检查 `np.any(a[alpha<10, :3] > 0)` 必须为 False。

### 🟡 P3：HBAO 尺度错误

**现象**：B 通道输出 234~255，几乎无遮蔽（AO 形同虚设）。

**根因**：`hbao(h, depth=0.03)` 的 depth 是为**灰度 0-255 域**标定的，输入 0-1 高度时 0.03 的阈值相对过大，遮蔽采样全部被跳过。

**修复**：v2 改为 `depth=0.15`（匹配 0-1 域 + 视差标定），且透出可见的缝暗效果。

### 🟡 P4：边缘"保满高"误伤透明区

**现象**：`hgt[edge]=1.0` 把透明区也强制设为 255。

**修复**：`np.where(edge & inside, 1.0, hgt)` —— 只对可见区。

### 🟢 P5：output 命名混乱（脏工作区）

**现象**：生成时保留 `block_` 前缀（源文件名），而 Iris 要求与基础贴图**同名** → `block_xxx_n.png` vs 需要的 `xxx_n.png`。

**修复**：`stem = name.replace(".png","").replace("block_","")`，一次成型，不做二次重命名（重命名会与旧文件撞车——真实发生过 IOException）。

### 🟢 P6：zip 分隔符虚惊

**怀疑**：PowerShell 列 zip 内容显示 `assets\...`（反斜杠），怀疑 Java 资源包系统读不了。

**验证**：Python `zipfile` 读 `namelist()` 确认实际是 **0 个反斜杠**（纯正斜杠），顺带确认 `zipfile.read("assets/...")` 成功 —— 虚惊，PowerShell 显示差异而已。

**经验**：跨语言检查文件内容时，不要相信 shell 的显示转义，用能读原始字节的工具验证。

### 🟢 P7：资源包在 game 目录被占用

**现象**：替换 `F:\PCL\versions\材质包测试\resourcepacks\*.zip` 时 `The process cannot access the file... being used by another process`。

**原因**：Minecraft 进程还在运行，jar 持有文件句柄。

**处理**：`Stop-Process` 关闭 java 进程 → 替换成功。之后提醒用户重开游戏（贴图已缓存，不重启不生效）。

---

## 五、游戏侧排查（用户报告"看不出 PBR"后）

### 5.1 排查顺序（按证据）

1. **版本目录结构**：`F:\PCL\versions\材质包测试\` 有 mods/ shaderpacks/ resourcepacks/ → PCL 版本隔离，配置都在版本目录下（不是全局 .minecraft）
2. **mods 检查**：Iris 1.8.12 ✅、附魔灌注台 ✅
3. **shaderpacks 检查**：BSL / Complementary Reimagined r5.6.1 / iterationRP 都有
4. **resourcepacks 检查**：我们的包在启用列表尾部（最高优先级，正确）
5. **iris.properties 检查**：`enableShaders=true` + `shaderPack=...`
6. **日志取证**（关键）：`latest.log` 显示 `[Iris/]: Shaders are disabled because enableShaders is set to false` → **启动时 shader 是关的**，之后才被改 → 那次会话 PBR 必然不渲染
7. **改配**：切到 `ComplementaryReimagined_r5.6.1.zip`（对 LabPBR/视差支持最全），`allowUnknownShaders=true` 保持

### 5.2 结论与教训

- **资源包没有错 ≠ 看得到**：PBR 渲染链条 = 资源包 `_n/_s` + Iris 启用 + shader 启用 + shader 对 LabPBR 的支持。任何一环断掉都看不到。
- **shader 配置只在启动时读取**！游戏内改 iris.properties / 资源重载不会重读启动配置。日志时间戳（启动 18:07:48 vs 配置文件 18:09:55）就是铁证。
- iterationRP 对 LabPBR `_n` B/A 通道的表现弱于 Complementary/BSL —— shader 选择本身就是质量因素。

---

## 六、v2 视差（POM）专项

### 6.1 为什么 v1 视差弱

- LabPBR 视差 = `_n.A` 通道（255=平/最高，0=最深凹）
- v1 高度是"灰度 Levels 压缩" → 大部分像素挤在 224+（直方图：side 65% 在 224-256，top 50%）→ 有效深度只有 ~20%，POM 位移几乎不可见
- HBAO depth 又配错（P3）

### 6.2 v2 视差设计

**分区平台高度**（不再从灰度推导，直接赋值）：

| 材质 | 高度 (0-1) | _n.A (0-255) |
|---|---|---|
| 金框 | 0.98 | 250 |
| 铁（进阶） | 0.92 | 235 |
| 紫魔法石 | 0.85 | 217 |
| 红毯 | 0.72 | 184 |
| 黑曜石 | 0.62 | 158 |
| 符纹（深凹） | 0.30 | 77 |

- 交界用**软权重渐变** + `gauss_blur(2.5)` 过渡（不硬跳变，符合 manual"同材质内均匀、规则视差"取向）
- 边缘保满高（≥0.98）防 POM 迭代错误
- **POM 预渲染验证器**（pom_preview.py）：模拟 shader 沿视线对高度图二分步进采样 → 实测 **11.2% 像素产生位移**，证明视差数据有效，且可以不开游戏直接看图

### 6.3 视差的游戏侧开关（用户必看）

- shader：选 Complementary Reimagined / BSL
- **必须打开 Shader Options → Parallax（POM）**，默认可能关闭；深度建议 0.4~0.6
- 视差按距离衰减：**贴脸（1-2 格）最强**，远看几乎无感——这不是贴图问题，是 POM 设计使然

---

## 七、可复现的生产管线（G:\PBR\work\）

| 文件 | 作用 |
|---|---|
| `dump_grid.py` | 16×16 像素 dump（分区分析用） |
| `gen_masks.py` | 色调聚类 → 28 张分区蒙版 (masks/) |
| `gen_pbr2.py` | v1 标准管线（灰度高度） |
| `gen_pbr_v2.py` | **v2 视差管线（分区平台高度）— 当前正式版** |
| `pom_preview.py` | POM 视差预渲染验证器 |
| `verify_v2.py` / `recheck.py` / `quality.py` | 通道数据验证脚本 |
| `src/` `masks/` `out/` `out_v2/` | 素材/蒙版/产物 |

**每次生成的验证步骤（不能省）**：
1. 通道 min/max/mean（法线 R/G 必须明显偏离 127")
2. 透明区 RGB 泄漏检查（必须 False）
3. 高度直方图（视差版必须有低值分布）
4. POM 预渲染位移统计（>8% 才及格）

---

## 八、当前交付物清单（G:\PBR\）

```
EnchantingInfuser-PBR-128x.zip      最终安装包 v2.0 (15.2 KB, 13 条目)
EnchantingInfuser-PBR-128x/         解包版
README-PBR.md                       用户文档
POM对比-top.png                     左原图/右视差渲染 对比
POM预览-top.png / POM预览-side.png  视差效果图
预览-normal-side.png                法线通道预览
预览-specular-side.png              光泽通道预览
work/                               全部生产管线 + 验证脚本
[附魔灌注台] EnchantingInfuser-v21.1.4-1.21.1-NeoForge.jar  源 mod
```

**已安装**：`F:\PCL\versions\材质包测试\resourcepacks\EnchantingInfuser-PBR-128x.zip`（v2.0）

---

## 九、未完成 / 后续可做

1. **实体书**（64×32）没做 `_n/_s`：它是进 blocks 图集的实体纹理，要做需先按书模型 UV 拆卷（类似箱型 UV 处理），再走同一管线
2. 蒙版可靠性：当前分区用色调聚类，进阶/普通共用；若用户在图包里看到某分区材质判断不对，可手工调 `gen_masks.py` 的色相边界
3. Designer 版 `.sbs` 图：若坚持 Designer 原工作流，可用 `resources/python/samples/sample_sbs_graph.py` 的 API 模式写建图脚本（在 Designer 内 Python Editor 执行）
4. 游戏内截图对比验证：最终质量仍需游戏内截图与实际 shader 参数（POM 深度）做闭环
