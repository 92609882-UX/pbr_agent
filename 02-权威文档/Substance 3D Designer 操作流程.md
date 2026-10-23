# Substance 3D Designer 操作流程

> 本文是 `PBR材质包制作经验与流程规范.md` 的 **Designer 实操版**，把「用 Python 脚本直接生成贴图」替换为
> 「在 Designer 里用节点图生成」，依据是项目内的 LabPBR 规范与机器流程说明。
>
> 适用：Minecraft 1.21.1 NeoForge + Iris + LabPBR 1.3

## 一、总览

| 阶段 | 输入 | 输出 | 工具 |
|---|---|---|---|
| 1. 准备 | mod jar 里的 16×16 / 64×64 原贴图 | 邻近放大 8× 的 128×128 / 512×512 | 任意图像工具或 `work/designer/` 里的脚本 |
| 2. 建图 | 放大后的基础色 | `_n`（法线/AO/高度）、`_s`（光滑度/F0/孔隙/发光） | Substance 3D Designer |
| 3. 打包 | `_n` / `_s` | 资源包 zip | 打包脚本 |
| 4. 验证 | 资源包 | 检查清单通过 | 数值检查脚本 + 游戏内目视 |

**核心约束**：材质包风格贴近原版，**不颠覆性改动**贴图；以原图 **8×8px 色块为最小处理单位**（16×16 原图放大 8 倍后，一个原像素 = 8×8px）。

## 二、准备工作

### 2.1 从 mod 提取原贴图

```bash
# 解包 mod jar，取 assets/<modid>/textures/ 下的基础色
python -c "
import zipfile
z = zipfile.ZipFile('项目素材/[等价交换重制版] ProjectE-1.21.1-PE1.1.0.jar')
for n in z.namelist():
    if n.startswith('assets/projecte/textures/') and n.endswith('.png'): print(n)
"
```

### 2.2 放大 8 倍（必须邻近/硬边缘采样）

| 原尺寸 | 放大后 |
|---|---|
| 16×16 | 128×128 |
| 64×64 | 512×512 |
| 64×32（护甲层） | 512×256 |

> **不要用双线性/双三次**，否则会出现模糊过渡，后续所有节点都会把过渡当成凹凸。

### 2.3 判断贴图类型（决定处理方式）

| 类型 | 特征 | 处理要点 |
|---|---|---|
| 普通方块 | 16×16 单面 | 直接走基础流程 |
| 箱型 UV / 多面拼图 | 一张图里并排多个面（如 512×512 里有 8×8 个格子） | **必须按模型 uv 裁成多个独立区域分别处理**，否则各面高度基准不一致，会出现「一面平、一面凸」 |
| 动画贴图 | 竖向多帧 | 保持原尺寸，逐帧处理或只处理第一帧 |
| 实体护甲 | 64×32 UV 展开 | 放大到 512×256，注意左右半身对应不同部位 |

> **本项目踩过的坑**：能量凝聚器/炼金术箱子的 `_n` 是 512×512 的多面拼图，早期没按面格分区，导致各面高度幅度从 34 到 146 不等，游戏里视差风格左右不一致。

## 三、Designer 环境

### 3.1 本机位置

```
D:\Substance 3D Designer\Adobe Substance 3D Designer\Adobe Substance 3D Designer.exe
  ├── plugins\pythonsdk\                       自带 Python 3.11
  ├── resources\python\sd\                     Python API（sd.api.sbs.SDSBSCompGraph …）
  ├── resources\documentation\pythonapi\html\  API 文档
  └── resources\packages\*.sbs                 节点定义（可据此确认节点 ID）
```

### 3.2 打开脚本编辑器

**Windows ▸ Python Editor** → File ▸ Open 打开 `.py` → **Run**。
（若 Designer 已关联 `.py`，也可在资源管理器里右键 → Run Script。）

> `sd` 模块依赖 Designer 进程内的 C++ 运行时，**外部 Python 无法 import**，脚本必须在 Designer 内跑。

### 3.3 导入素材

把放大后的基础色放进资源库（Library ▸ 右键 ▸ Import），或在脚本里用 `SDResourceBitmap.sNewFromFile(...)` 直接引用绝对路径。

## 四、基础流程：`_n`（法线 / AO / 高度）

### 4.1 节点链

```
原贴图 → Grayscale Conversion → Auto Levels ─┬─ Levels(0.4~0.6) → Normal → RGBA Split ─┬─ R → PP-R ─┐
                                             │                                          └─ G → PP-G ─┤
                                             │                                                       ├→ RGBA Merge → Normal(normalize) → RGBA Split
                                             │                                                       │
                                             ├─ Levels(0.4~0.6) → Ambient Occlusion ────────────────┼→ Merge.B
                                             │                                                       │
                                             └─ Levels(200/255~1) ──────────────────────────────────┴→ Merge.A
```

### 4.2 关键参数

| 节点 | 参数 | 值 | 理由 |
|---|---|---|---|
| Auto Levels | — | 默认 | 归一化灰度，方便后续 Levels 精确控范围 |
| Levels（Normal 前） | Level Out Low / High | **0.4 / 0.6** | 把灰度压在窄区间，法线强度才合理可控 |
| Normal | Intensity / Format / Alpha | **3** / **OpenGL** / Force Alpha To 1 | LabPBR 法线为 DirectX(Y-)，Designer 用 OpenGL 需在导出时翻 G |
| Ambient Occlusion | Height Depth | 128px 用 **0.03**，按 `(1/size)²` 缩放 | 512px 应显著更小，否则 AO 过强 |
| Levels（高度） | Level Out Low / High | **200/255 / 1.0** | 大多数 POM 光影的视觉下限；**方块边缘必须接近满高**，否则会采样到贴图另一侧，出现边缘参差 |
| Levels（高度） | Level In Mid | 0.3~0.4 | 让同一材质内部高度均匀，减少无意义视差 |

### 4.3 R/G 的 Pixel Processor（重要）

作用：**抑制 8×8 块边界上的假法线**——原贴图放大 8 倍后，色块交界会出现硬台阶，直接差分会在每个块边缘生成一圈法线。

逻辑（`size` = 图片边长，128×128 时 `size=128`）：

```
R-Pixel Processor:
  gray   = Sample($pos)
  gray_x = Sample($pos + (1/size, 0))
  if gray_x > 0.5:  output = gray
  else:             output = (gray > 0.5) ? 0.5 : gray

G-Pixel Processor:
  gray   = Sample($pos)
  gray_y = Sample($pos + (0, 1/size))
  if gray_y <= 0.498: output = gray
  else:               output = (gray <= 0.498) ? 0.5 : gray
```

处理完再进 RGBA Merge（**G 需先 Invert Grayscale**）→ Normal(normalize) → RGBA Split 取 R/G 作为最终法线。

## 五、基础流程：`_s`（光滑度 / F0 / 孔隙 / 发光）

### 5.1 节点链

```
Auto Levels ─┬─ Levels → Merge.R          （光滑度）
             └─ Uniform Color → Merge.G/B/A（常量）
```

### 5.2 通道取值

| 通道 | 含义 | 值域 |
|---|---|---|
| R | 感知光滑度 | 0 最粗糙 / 255 最光滑；机器类金属外壳 `0.55~0.75` |
| G | F0 / 金属 | 非金属约 `8~15`（常用 `10`）；金属预设见下 |
| B | 孔隙率(0–64) / SSS(65–255) | 机器 `0`、木头 `12`、羊毛 `38`、沙 `64`；透光材质 `80~180` |
| A | 自发光 | **不发光用 `255`**（最稳妥）；发光 `20~254` 递增 |

**金属预设**：`230` 铁、`231` 金、`232` 铝/玻璃、`233` 铬、`234` 铜、`235` 铅、`236` 铂、`237` 银、`255` 泛用金属。

> 金属**不能只拉高 R**，必须把 G 设成对应预设或 255，否则光影会当普通高光处理。

### 5.3 材质参考

| 材质 | R | G | B | A |
|---|---|---|---|---|
| 泥土/石头 | 10–50 | 10 | 0–8 | 0 |
| 木头 | 30–80 | 10 | 12 | 0 |
| 羊毛/布料 | 0–25 | 8–12 | 38 | 0 |
| 沙子/砂岩 | 0–30 | 8–12 | 64 | 0 |
| 抛光石材 | 100–170 | 10–15 | 0 | 0 |
| 玻璃/冰 | 220–255 | 10–20 | 0 | 0 |
| 铁块 / 金块 | 170–230 / 180–240 | **230 / 231** | 0 | 0 |
| 发光纹理 | 视材质 | 10 | 0 | 80–254 |

## 六、进阶：蒙版（区分材质与几何）

基础流程用「颜色明暗」推断凹凸，遇到**同一张贴图里有金属+非金属**或**成块的几何凸起/凹陷**时会出错，需要做蒙版。

### 6.1 金属蒙版

1. 手工做一张与原图同尺寸的黑白蒙版（金属部分为白）
2. `_n` R/G：在 `Levels → Normal` 之间插入
   `Blend(Opacity≈1, Add)` → `Blend(Opacity=0.35, Substract)`
   —— 目的：让金属整体略高于周围，且**金属内部不产生法线**（内部统一灰度）
3. 交界柔化：蒙版 → `Non_uniform_blur_grayscale(Intensity=5)` → `Normal(Intensity=1.5, OpenGL)`
   → 与原法线用 `Blend(Overlay, Opacity=1)` 合并（金属与非金属边缘生成约 4px 宽渐变）
   > 尺度规律：`Non_uniform_blur` 的 Intensity 按 **平方反比**、`Normal` 的 Intensity 按 **反比** 缩放（1024px 图用 1.25 / 0.75）
4. `_n` B（AO）与 A（高度）：在 Levels 后 `Blend(Add)` 叠金属蒙版（AO 用 Opacity≈0.1，高度用 1.0 让金属满高）
5. `_s` R/G：`Blend(Add, Opacity=*)` 叠金属蒙版到目标值（旧金属 R≈210、抛光 R≈245–255、铁 G=230、铜 G=234）

### 6.2 几何形状蒙版

1. 做两张黑白蒙版：**凸起为白**、**凹陷为白**（各自一张）
2. `_n` 各通道的 Levels 前后，用 `Blend(Add)` 抬高凸起、`Blend(Substract)` 压低凹陷，让大尺度形状更明显
3. 若凸起内部需要更平（减少内部视差）：先 `Blend(Add, Opacity=1)` 全部顶到 255，再 `Blend(Substract)` 减到一个合适区间
4. **宽法线**：大块凸起（如 24×40px）的 1px 法线太硬，需要在边缘一圈铺 8px 宽的渐变
   —— 做法等价于「把 128×128 当成 16×16 来算法线」，法线生成在高灰度一侧
   —— 用 `Blend(Add / Substract, Opacity=0.08–0.15)` 分别叠 x_left / x_right / y_on / y_down 四张方向蒙版
5. `_s` 各通道：用凸起/凹陷蒙版分别控制 R/G/B/A；若凸起内部还有不同材质，再各建一张蒙版

> **判断凸起/凹陷的原则**：必须是**规则的、有规律的**（砖块凸起、木板纹理），
> **不要把单个 8×8 色块的明暗差异误判为凹陷**；原贴图有明暗渐变表示受光/背光面，背光面不能当凹陷。

### 6.3 让低凹凸材质更真实

纸张、羊毛这类法线/视差都不明显的材质，可以叠一张真实纹理的照片：
`真实纹理 → Normal → RGBA Split → PP-R / PP-G → Invert` 后与原法线 `Blend(Overlay)`。

## 七、导出与打包

1. 图中放两个 **Output** 节点，分别连 `_n` 与 `_s` 的 RGBA Merge
2. 导出：**Tools ▸ Export Outputs**（或在 Output 节点上右键导出），
   分辨率按放大后的尺寸（128 / 512），格式 PNG
3. 命名规则：`<基础色名>_n.png`、`<基础色名>_s.png`，与原图同目录
4. **DirectX / OpenGL 检查**：LabPBR 要求 DirectX（Y-down）。若 Designer 用的是 OpenGL 法线，
   导出后需**翻转 G 通道**（`G' = 255 - G`）
5. 打包：把 `assets/...` 与 `pack.mcmeta`、`assets/minecraft/optifine/texture.properties`
   （内容 `format=lab-pbr/1.3`）一起压成 zip

## 八、验证

### 8.1 数值检查（不开游戏）

对每张 `_n` / `_s` 统计：

| 检查项 | 期望 |
|---|---|
| `_n` R/G 偏离 128 的平均值 | 15 左右（<5 说明法线过弱，>40 说明过强） |
| `_n` B（AO） | 有层次（全 255 = AO 失效） |
| `_n` A（高度） | 无 0；边缘接近 255；**多面拼图要逐面格检查幅度是否一致** |
| `_s` G | 非金属 8–20；金属命中预设值（230/231…） |
| `_s` A | 不发光为 255 |
| 透明区 | RGB 全 0（防 mipmap 污染） |

### 8.2 游戏内检查

1. 资源包放 `resourcepacks/`，只启用最新版（关闭旧版）
2. 光影 RP Support 选 **LabPBR**；打开 Parallax，深度 0.4–0.6
3. 贴脸（1–2 格）看视差，斜看边界有无撕裂，检查各面凹凸力度是否一致

## 九、脚本化（可选）

Designer 提供 Python API，可以自动建图，免去手工连节点：

- 脚本：`work/designer/build_condenser_graph.py`
- 说明：`work/designer/README-Designer建图说明.md`
- 用法：Designer ▸ Windows ▸ Python Editor ▸ Open ▸ Run

脚本遵循本文第四、五节的节点链与参数；后续可扩展到第六节的蒙版流程（建蒙版节点 + Blend）。

## 十、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 每个 8×8 色块边缘都有一圈亮/暗线 | 放大后的硬台阶被差分 | 加 R/G Pixel Processor（§4.3） |
| 一面有视差、另一面几乎平的 | 多面拼图各面高度基准不同 | 按面格分区，各自归一化到统一幅度（§2.3） |
| 斜看时边缘撕裂、出现另一侧的图案 | 边缘高度不是满高 | 高度 Levels 的 Out Low 保持 ≥200/255，边缘强制 255（§4.2） |
| 金属看起来像塑料 | 只调了 R，没设 G 的金属预设 | G 设为 230/231/…（§5.2） |
| 换光影后整体错乱 | 未声明 labPBR，光影按 oldPBR 解码 | 加 `assets/minecraft/optifine/texture.properties`（§7.4） |
| AO 全区 255 没有遮蔽 | 用「邻域亮度 − 当前高度」做判据，暗色贴图恒为负 | 改用「邻域高度 − 当前高度」 |
