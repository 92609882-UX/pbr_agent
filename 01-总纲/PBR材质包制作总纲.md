> **License**: 本文档受 MIT License 保护 (Copyright (c) 2026 92609882-UX|渐行渐远)。

# Minecraft PBR 材质包制作总纲（Substance 3D Designer 流程）

> **定位**：本文件是 `G:\PBR` 三个项目的**单一入口总纲**——把 `正式版\`、`参考资料\规范\`、
> `开发管线\` 下的分散材料收敛为一份可直接投喂给 Agent 的执行文档。
> 需要细节时按 §18 定位回原文档，不要凭记忆推断参数。
>
> **同源副本**：本文件与 DSH 技能 `pbr-texture-pipeline` 正文一致，且**本文件是权威源**。
> 技能文件（`~\.dsh\skills\pbr-texture-pipeline.md`、`~\.reasonix\skills\pbr-texture-pipeline.md`）
> 在本正文之前多一段 YAML frontmatter（`name` / `description` 两个字段）。
> **同步做法**：改完本文件后，删掉第 1 行协议行与上方这段定位块，在开头补上带 `name` / `description`
> 的 YAML frontmatter，即为技能文件内容（两份技能文件需一致）。

Minecraft 1.21.1 NeoForge + Iris + **LabPBR 1.3** 材质包制作的权威工作流。
项目根 `G:\PBR`，三个项目：附魔灌注台（Enchanting Infuser）、等价交换重制版（ProjectE）、车万女仆（TouhouLittleMaid）。

## 0. 本文定位与权威优先级

三份来源分层，**冲突时按此优先级裁决**：

| 层 | 来源 | 管什么 |
|---|---|---|
| **规范层** | `参考资料\规范\ShaderLABS-LabPBR-Material-Standard.wiki.txt` | 通道**语义**（哪个通道是什么、取值范围）。唯一权威，不可协商 |
| **工程层** | `正式版\PBR材质包制作经验与流程规范.md` | 工程**参数**（放大倍数、分区高度、法线强度、AO 基值、检查清单） |
| **项目层** | `正式版\PBR制作注意事项与Agent约束.md`、`开发管线\WORKLOG-工作过程与注意点.md` | 本项目**实测踩坑**与实测数值 |

- 改**通道含义** → 只查规范层。
- 改**放大/分区/强度** → 查工程层。
- **本项目实测值**（跨度 45~60、转化桌台阶 12.3 等）只在项目层有效，**不要当普适标准**。

---

## 1. 环境事实（先探测，别假设）

| 项 | 值 | 探测方式 |
|---|---|---|
| Designer | `D:\Substance 3D Designer\Adobe Substance 3D Designer\`（实测 14.1.2） | 目录存在性 |
| 命令行四件套 | `sbscooker.exe` / `sbsrender.exe` / `sbsbaker.exe` / `sbsupdater.exe` | 同上 |
| Designer 内置 Python | 3.11，**无第三方库** | `import numpy` 会失败 |
| 外部 Python | 3.10.11 + numpy 2.2.4 + Pillow 11.3.0 + cv2 4.11.0 | `python -c "import numpy,PIL"` |
| 工具脚本 | `开发管线\sbs_cli.py`（cook/info/render/run） | `python sbs_cli.py --help` |
| 游戏测试实例 | `F:\PCL\versions\材质包测试\`（Iris 1.8.12） | — |

### 🔑 决定整体架构的一条约束

**`sd` Python API 是进程内 API**：它依赖 Designer 启动时注入的 `designersdk.dll`（磁盘上**不存在**该 dll）。
外部 Python `import sd` 必然失败（`SD API library not found`）。

> **推论**：外部 Python **不能**建节点图，**只能**（a）算 PNG、（b）改写 `.sbs` 文本、（c）驱动 cook/render。
> 一切"用外部脚本自动建 Designer 图"的方案都不成立——这是本流程所有分工设计的根源。

---

## 2. 铁律（违反必返工）

### 2.1 开工前必须读模型

```bash
cat assets/<mod>/models/block/<name>.json
```

**方块实体渲染器陷阱**：有些方块不由模型 json 决定 UV，而是**渲染器硬编码**。
例：ProjectE 炼金术箱走 `ChestRenderer` + `ModelLayers.CHEST`，UV 来自 `texOffs`
（箱体 `texOffs(0,19)` 14×10×14、盖子 `texOffs(0,0)` 14×5×14、锁扣 2×4×1，**共 18 个面**）。
`models/block/alchemical_chest.json` 里只有 `particle` 就是**这个信号**。

必须确认的三件事：① 哪些面引用哪张贴图；② 每面的 UV 范围；③ 是否由渲染器硬编码绘制。

### 2.2 非 16×16 贴图必须当"多面拼图"处理

按模型 UV 裁切成**多张独立的 128×128** 逐张处理，**不要整张 512×512 一起做**。
否则各面高度基准不一致，游戏里出现"一面平、一面凸"，视差风格左右不一致。

### 2.3 判材质必须看颜色，不能只看灰度

饱和度 / 色相决定材质语义：青绿高饱和 = 能量纹路/宝石；纯灰 = 金属面板；亮灰 = 亮金属件。
实测：箱子 18 个面里 17 面纯灰，唯一彩色是盖子顶面（RGB≈(46,75,80)、sat 0.24、29% 彩色像素）。
**只看灰度会把不同材质混为一谈。**

### 2.4 高度用"色块连通块"分层，禁用亮度梯度

- 像素画的高度来自**色块分区**，块内保持平整
- 原贴图的明暗含"受光/背光"的绘画信息，**不等于几何高度**
- ❌ 禁止直方图均衡、对比拉伸等数学"拉"高度——会破坏原贴图色块格局
- ❌ 禁止把单个 8×8 色块的明暗差误判为凹陷

### 2.5 视差跨度必须受控

| 参照 | 跨度（max−min） |
|---|---|
| 全包绝大多数方块 | **45~60** |
| 转化桌 transmutation_stone（**标杆**） | 55（6 层） |
| 炼金术箱子（最终） | 85（6 层，台阶 11.8） |
| condenser（**异常值，反面教材**） | 127 |

**超过 100 就是异常**，必然 POM 撕裂。标杆要挑同类已验收方块，**不要拿异常值当标杆**。

### 2.6 可见边缘必须满高

可见外轮廓的 `_n` A 通道必须 = 255。边缘不满高时，POM 会把贴图另一侧的视差迭代显示出来 → 方块边缘参差、漏色。
**正确逻辑是"可见边缘满高，透明区保持透明且 RGB 为零"**——`_s`/`_n` 的保满高逻辑**不能误伤透明区**。

### 2.7 法线方向：DirectX（Y-down）

LabPBR 规定 `_n` = DirectX 格式（Y-）：X 向右为正，**Y 向下为正**。

```
写入 G 通道的值 = 255 - G_opengl      # 若上游是 OpenGL 法线
```

Designer 的 `Normal` 节点是 **OpenGL** 格式，因此**导出后必须翻 G**（或在图内 G 分支上加 `Invert Grayscale`）。

### 2.8 AO 判据必须用「邻域高度 − 当前高度」

❌ 不要用「邻域亮度 − 当前高度」——对暗色贴图恒为负，AO 会全 255 失效
（本项目暗物质块 / 炸药 / 收集器共 7 张踩过）。

### 2.9 不做交界柔化（本项目约定）

色块之间保持硬边，只允许 8px 宽法线做过渡。

### 2.10 透明区 RGB 必须清零

透明像素若携带法线/AO/高光数据，mipmap、过滤和斜视采样时会污染可见边缘。
验证：`np.any(arr[alpha < 10, :3] > 0)` 必须为 `False`。

---

## 3. 生产架构

### 3.1 总管线

```
[外部 Python / 已有脚本]                    [Designer 侧]
  分区、高度平台、法线、AO、蒙版  ──> PNG ──┐
                                          ├─> .sbs（换 resource 路径）
  .sbs 里建好的库节点（HBAO/Blur/Shuffle）─┘        │
                                                    ├─ sbscooker ─> .sbsar
                                                    └─ sbsrender ─> _n.png / _s.png
                                                                        │
                                                          打包 zip + texture.properties
                                                                        │
                                                             数值验证 + 游戏内验证
```

### 3.2 三条可执行路线

| 路线 | 做法 | 适用 | 代价 |
|---|---|---|---|
| **A. Designer 内 Python Editor** | 粘贴 `build_*.py` → F5 运行 → `compute()` + `tex.save()` | 需要真·Designer 节点精度（HBAO、Blur） | 需 GUI，无法黑盒批量 |
| **B. 无头 CLI** | 外部改 `.sbs` 资源路径 → `sbs_cli.py run` | 批量出图、不开 GUI | 图结构必须先在 Designer 建好 |
| **C. 纯外部 Python 复刻** | 用 numpy 复刻每个节点的数值语义 | 全自动、可复现、易调试 | 没有 Designer 库节点精度 |

**实际项目采用 C 为主 + B 辅助**，以 A 的节点语义作为**数值纲领**。
**分工原则**：数值逻辑（分区、对称性、遮罩）放外部 Python（有 numpy）；**四通道组装与导出**放 Designer（`shuffle`/`output` 稳定可靠）；**HBAO 交给 Designer 库节点**（比自写遮罩真实得多：10~255 共 230 级灰阶 vs 自写 150~255）。

---

## 4. 阶段一：素材摸底（第一步必须做）

### 4.1 解包并建立清单

```python
import zipfile
z = zipfile.ZipFile('项目素材/[等价交换重制版] ProjectE-1.21.1-PE1.1.0.jar')
for n in z.namelist():
    if n.startswith('assets/projecte/textures/') and n.endswith('.png'): print(n)
```

要提取的目录：

```text
assets/<modid>/blockstates/
assets/<modid>/models/block/      models/item/
assets/<modid>/textures/block/    textures/entity/    textures/gui/
```

记录每张原图的**文件名、尺寸、色彩模式、透明区域、实际引用位置**。
不要凭文件名猜用途——必须在模型和 blockstate 里确认引用关系。

### 4.2 核对模型父级与 UV

`parent` 和 `faces.uv` 决定贴图如何投影。原文中从未被 UV 使用的像素**不能用来判断游戏内最终外观**。

**本项目血泪教训**：附魔灌注台 side 贴图存在红色像素，美术上看着像"底部装饰"，经模型 UV 后**成了游戏画面里的底部红毯横带**。
→ **PBR 通道修正无法替代基础颜色贴图和 UV 审查**。出现错误颜色时先查基础纹理和 UV，再看 `_s`。

### 4.3 记录材质语义

不要把所有明暗变化直接当高度。结合颜色、用途、构图、相邻像素归类：

| 材质 | 常见语义 | 处理重点 |
|---|---|---|
| 金属金/铁 | 框架、边条 | 高光滑度、金属预设、边界法线 |
| 红毯/布面 | 软质装饰 | 低光滑度、孔隙率、低高度 |
| 紫色核心 | 宝石/魔法晶体 | 中高高度、适量 SSS 或自发光 |
| 黑曜石 | 底座、深色结构 | 高光滑度、低高度、接触 AO |
| 符文 | 凹刻或能量纹路 | 低高度、凹槽 AO、独立发光 |

判据：**通过原贴图不同色系区分**（`sat > 0.35` 判彩色）、通过模组提供的信息判断、通过 mcmod 等网站查方块材质。

---

## 5. 阶段二：放大与分区

### 5.1 邻近（硬边缘）放大 8 倍——**必须**

| 原尺寸 | 放大后 |
|---|---|
| 16×16 | 128×128 |
| 64×64 | 512×512 |
| 64×32（护甲/实体） | 512×256 |

❌ **不要用双线性/双三次**，否则出现模糊过渡，后续所有节点会把过渡当成凹凸。

### 5.2 最小处理单位

16×16 原图放大 8 倍后，**一个原像素 = 8×8px**。蒙版制作与像素处理**一律以 8×8px 为最小单位**。

### 5.3 贴图类型判定（决定处理方式）

| 类型 | 特征 | 处理要点 |
|---|---|---|
| 普通方块 | 16×16 单面 | 直接走基础流程 |
| 箱型 UV / 多面拼图 | 一张图里并排多个面 | **按模型 UV 裁成多个独立区域分别处理** |
| 动画贴图 | 竖向多帧（配 mcmeta） | 保持原尺寸，逐帧或只处理第一帧 |
| 实体护甲 | 64×32 UV 展开 | 放大到 512×256，注意左右半身对应不同部位 |

---

## 6. 阶段三：`_n` 建图（法线 / AO / 高度）

### 6.1 节点链

```
原贴图 → Grayscale Conversion → Auto Levels ─┬─ Levels(0.4~0.6) → Normal → RGBA Split ─┬─ R → PP-R ─┐
                                             │                                          └─ G → PP-G ─┤
                                             │                                          → Invert ────┤
                                             │                                                       ├→ RGBA Merge → Normal(normalize) → RGBA Split ⇒ **_n R,G**
                                             ├─ Levels(0.4~0.6) → Ambient Occlusion ────────────────┼⇒ **_n B**
                                             │                                                       │
                                             └─ Levels(200/255~1.0) ────────────────────────────────┴⇒ **_n A**
```

**四张灰度图分别接入总 RGBA Merge 的 R/G/B/A，即为 `_n`。**

### 6.2 关键参数

| 节点 | 参数 | 值 | 理由 |
|---|---|---|---|
| Grayscale Conversion | — | `0.2126R+0.7152G+0.0722B` | 标准亮度权重 |
| **Auto Levels** | — | 默认 | **归一化灰度**，让后续 Levels 能精确控范围；跳过它则 Levels 参数失去意义 |
| Levels（Normal 前） | Level Out Low / High | **0.4 / 0.6** | 把灰度压在窄区间，法线强度才合理可控 |
| **Normal** | Intensity / Format / Alpha | **3** / **OpenGL** / Force Alpha To 1 | Designer 用 OpenGL；LabPBR 要 DirectX → **导出时翻 G** |
| Ambient Occlusion | Height Depth | 128px 用 **0.03**；缩放规律见下 | 见 6.4 |
| Levels（高度） | Level Out Low / High | **200/255 / 1.0** | 200/255 是多数 POM 光影的视觉可接受下限 |
| Levels（高度） | Level In Mid | 0.3~0.4 | 让**同一材质内部高度均匀**，减少无意义视差 |

> **法线强度不要照抄数字。** `Intensity=3` 是配合 `Levels(0.4~0.6)` 压缩后的经验值，换管线就失效。
> **真正的不变量是实测值**：`_n` R/G 偏离 128 的均值 ≈ **15**。见 §11。
> （本项目 Python 路线用"平滑后高度差分 × `intensity*2.0`"，512px 下约 8~9.5。）

### 6.3 R/G 的 Pixel Processor（抑制 8×8 块边界假法线）——**重点**

原贴图放大 8 倍后色块交界是硬台阶，直接差分会在**每个块边缘**生成一圈假法线。
`size` = 图片边长（128×128 时 `size=128`）：

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

处理完 → RGBA Merge（**G 需先 Invert Grayscale**）→ `Normal(normalize)` → RGBA Split 取 R/G 作为最终法线。

### 6.4 HBAO 的 Height Depth（⚠ 未完全验证）

- agent_main 实测偏好：**128px 用 0.03**
- 原文给出的缩放规律 `Height Depth = (1/size)²` **自标了"？？？"，未经证实** → 大尺寸**必须实测**，不要盲信公式
- 若改用外部 Python 自写 HBAO（**输入是 0-1 域**）：128px 用 **0.15**。WORKLOG 记：0.03 是为**灰度 0-255 域**标定的，输入 0-1 时阈值相对过大，遮蔽采样全被跳过，B 通道会输出 234~255（AO 形同虚设）

**域混用（0-1 vs 0-255）是数值管线最隐蔽的 bug 来源。**

---

## 7. 阶段四：`_s` 建图（光滑度 / F0 / 孔隙 / 发光）

### 7.1 节点链

```
Auto Levels ─┬─ Levels → Merge.R              （光滑度：精确控制）
             └─ Uniform Color → Merge.G/B/A   （常量：直接设值）
```

简单材质可直接用 `Uniform Color` 的 Grayscale L 值。

### 7.2 通道取值

| 通道 | 含义 | 值域与经验 |
|---|---|---|
| R | 感知光滑度 | 无反射 `0~50`；`0.5`(R=128) = 有一定光滑但非强反光；未打磨/锈蚀金属、不透光毛玻璃 `190~220`；抛光金属 / 打磨玻璃 `240~255`。**同材质内 `Out High − Out Low < 0.2`**（如木板 0.4/0.5） |
| G | F0 / 金属 | 非金属 **`8~15`（默认 `10`，≈4% F0）**；金属**必须**设硬编码预设 |
| B | 孔隙率 / SSS | `0~64` 孔隙率（沙 64 / 羊毛 38 / 木头 12 / 金属 0）；`65~255` SSS（65=0%，255=100%）。**同一像素不能同时表达** |
| A | 自发光 | `0` = 0%；`20~254` 递增；**`255` 被规范定义为"忽略"** |

> **`_s` R 的内部差异问题**：经 Auto Levels 后逐像素灰度差异会很大，即使压缩 Out Low/High 也仍在。
> 解决：**减小 `Level In Mid` 到 0.3~0.4**，可获得接近 Out High 的均匀材质光滑度。

> **`_s` G 的"非金属 0"是旧表的说法**。规范层规定 `0~229` 是**线性 F0**，取 0 等于零反射率，物理上不成立。**默认用 10。**

### 7.3 自发光 A：`0` 还是 `255`？

规范原文：**`0` = 0% 发光；`255` 被忽略（不发光）**。所以**两者都不发光**，区别在安全性：

- **不发光一律用 `255`（最稳妥）** —— RGB 图像没有 alpha 通道时默认就是 255，合并时不会意外引入发光
- 需要发光才用 `0~254`；`A=50~100` 视觉上已极亮；模组硬编码发光强度 < 10 的方块建议 `A=20~30`
- **发光颜色来自基础颜色贴图**，`_s` A 只控制强度

**自发光要按视觉功能分层，不要整张贴图统一提 A**：
符文最强 > 魔法核心中等 > 核心边缘/相邻材质低强度过渡 > 金属框/红毯/黑曜石底座不发光。

---

## 8. 阶段五：蒙版进阶

基础流程靠"颜色明暗"推断凹凸，遇到以下情况**必然出错**，必须做蒙版：

- 同一张贴图里**金属与非金属并存**且有明显分区
- 贴图含**成块的几何信息**（砖块凸起与砖缝凹陷、木板纹理等有规律的凹凸）
  —— *这些有规律的、整体化的而非像素化的效果，需要综合分析原始贴图含义得出结论*

### 8.1 金属蒙版

① 生成与原图同尺寸黑白蒙版（金属为白）→ 导入资源库。

② **`_n` R/G**：在 `Levels → Normal` 之间插入
`Blend(Opacity≈1, Add(Linear Dodge))` → `Blend(Opacity=0.35, Substract)`

> 第一个 Blend 让所有金属灰度顶到 255；第二个减回，使金属**略高于**周围。
> **目的**：金属内部 8×8 块之间**不产生法线**（内部统一平滑），**只在金属/非金属交界产生法线**。

③ **交界柔化**：蒙版 → `Non_uniform_blur_grayscale(Intensity=5)` → `Normal(Intensity=1.5, OpenGL)` → RGBA Split → PP-R/PP-G（同一套逻辑）→ 与原法线 `Blend(Overlay, Opacity=1)` 合并（金属侧生成约 4px 渐变法线）。

> **尺度规律**：`Non_uniform_blur` 的 Intensity 按**平方反比**、`Normal` 的 Intensity 按**反比**缩放。
> 1024×1024 用 `1.25 / 0.75`。

④ **`_n` B / A**：在 Levels 后 `Blend(Add)` 叠金属蒙版——AO 用 `Opacity≈0.1`，高度用 `Opacity=1.0`（金属一般 POM 略高，直接填 A=255）。

⑤ **`_s` R/G**：`Blend(Add, Opacity=*)` 叠到目标值（旧金属 R≈210、抛光 R≈245~255、铁 G=230、铜 G=234）。
若 Add 后金属内部灰度差异仍大：`Blend(Add, Opacity=1)` → `Blend(Substract, Opacity=*)` 先统一再降到区间。

### 8.2 几何形状蒙版

① 生成**两张**黑白蒙版（凸起为白 / 凹陷为白各一张）。

> **凸起凹陷的判定必须是规则的、有规律的。**
> ❌ 不要把单个 8×8 色块的灰度偏低误判为凹陷——模组原贴图存在色块不合理处，请综合**方块用途、实际规律、几何形状、美观整洁度**判断。
> ⚠ 原贴图会在凸起部分画明暗渐变表示**受光/背光**，**背光面常常被误判为凹陷**。

② **`_n` 各通道**：在 Levels 前后用 `Blend(Add)` 抬高凸起、`Blend(Substract)` 压低凹陷，使**大尺度形状更明显**。

③ **需要凸起内部更平**（内部视差要小）：先 `Blend(Add, Opacity=1)` 全部顶到 255，再 `Blend(Substract)` 减到合适区间。`Opacity=1` 是抵消内部灰度差的极限值。

④ **宽法线**：大块凸起（如 24×40px）的 1px 法线太硬，需在边缘一圈铺 **8px 宽**渐变。
生成逻辑等价于「**把 128×128 当成 16×16 来算法线**」，法线生成在**高灰度一侧**。

```
R: PP-R → Blend(Add,      Opacity=0.08~0.15)(fg = *_up_x_right.png) 
        → Blend(Substract,Opacity=0.08~0.15)(fg = *_up_x_left.png)
G: PP-G → Blend(Add,      Opacity=0.08~0.15)(fg = *_up_y_down.png)
        → Blend(Substract,Opacity=0.08~0.15)(fg = *_up_y_on.png)
```

⑤ **`_s` 各通道**：用凸起/凹陷蒙版分别控制 R/G/B/A；**若凸起/凹陷内部还有不同材质，再各建一张蒙版独立处理**。

### 8.3 让低凹凸材质更真实

纸张、羊毛这类视差与法线都不明显的材质：叠一张**真实纹理**（照片或 AI 生成），
`真实纹理 → Normal → RGBA Split → PP-R / PP-G → Invert` 后与原法线 `Blend(Overlay)`。
可为低视差、低法线材质提供更真实的纹理感。

---

## 9. 阶段六：导出

1. 图中放**两个 Output 节点**，分别连 `_n` 与 `_s` 的 RGBA Merge
2. 导出：**Tools ▸ Export Outputs**（或 Output 节点右键），分辨率按放大后尺寸，格式 PNG
3. 命名：`<基础色名>_n.png` / `<基础色名>_s.png`，**与原图同目录**
4. ⚠ **DirectX / OpenGL 检查**：LabPBR 要 DirectX(Y-)。Designer 的 Normal 是 OpenGL → **导出后翻 G**（`G' = 255 - G`）

**命名陷阱**：源文件名常带 `block_` 前缀，而 Iris 要求与基础贴图**同名**。
`stem = name.replace(".png","").replace("block_","")` —— **一次成型，不做二次重命名**（重命名会与旧文件撞车，真实发生过 IOException）。

---

## 10. 阶段七：打包与 labPBR 声明

### 10.1 必须是 labPBR 声明（跨光影视差错乱的根因）

`_n` / `_s` 的通道含义在 **labPBR** 与 **oldPBR（seusPBR）** 下**不同**。
资源包若不声明，部分光影会按 oldPBR 解码：

| 通道 | labPBR（本包语义） | oldPBR（被误判） | 后果 |
|---|---|---|---|
| `_n` B | 材质 AO | 法线 Z 分量 | 法线归一化后严重倾斜 → 光照/视差错乱 |
| `_s` G | F0 / 硬编码金属(230+) | 金属度 0–255 | 反射性质整体改变 |
| `_s` B | 孔隙率 / SSS | 自发光 | 大面积假发光 |
| `_s` A | 自发光 | 未使用 | 真自发光丢失 |

**修复**：每个包必须写 `assets/minecraft/optifine/texture.properties`：

```properties
format=lab-pbr/1.3
```

声明后 Iris 才定义 `MC_TEXTURE_FORMAT_LAB_PBR_1_3` 宏，光影才走 labPBR 解码路径。
**唯一受支持的 labPBR 版本就是 1.3**，不要写其他版本号。

- 不支持 labPBR 的光影（SEUS PTGI 系列）无论如何都按 oldPBR 解析，需**另出一套 oldPBR 包**
- 光影侧若有 RP Support / PBR Format 选项，**要选 LabPBR**（BSL 里 "Old PBR + Emissive" 是 oldPBR，不要选）

### 10.2 目录与 ZIP

- ZIP 内使用**正斜杠 `/`**；根目录直接含 `pack.mcmeta` 和 `assets/`
- 命名空间与模组 `modid` 一致；`_n/_s` 与基础贴图同名
- 改完必须：**重新打包 zip → 验证条目数 → `git commit`（工作区干净）**

---

## 11. 阶段八：验证门禁（必做，禁止凭感觉）

### 11.1 出图前置检查

**先确认资源真的加载了**——不看退出码，只看 cook 输出里有没有
`Unreachable resource` / `Can't load resource`。有就是源图缺失，**而 `sbscooker` 退出码仍是 0**（见 §15）。

### 11.2 数值检查（不开游戏）

| 检查项 | 期望 |
|---|---|
| `_n` R/G 偏离 128 的均值 | **≈15**（<5 法线过弱，>40 过强）；实测健康范围 50~205 |
| `_n` B（AO） | **有层次**（全 255 = AO 失效） |
| `_n` A（高度） | **无 0**；边缘接近 255；**多面拼图要逐面格检查幅度是否一致** |
| `_s` G | 非金属 `8~20`；金属**命中预设值**（230/231/…） |
| `_s` A | 不发光为 `255` |
| 透明区 | **RGB 全 0**：`np.any(arr[alpha<10, :3] > 0)` 必须 `False` |
| 通道统计 | **每次生成都打印 min/max/mean**，不能只看成品图 |
| 输出非常色 | `np.unique(arr).size > 1`，全 0 即失败 |

### 11.3 四项核心指标

| 指标 | 含义 | 参照 |
|---|---|---|
| 高度跨度 | max − min | 同类方块 **45~60** |
| 块级台阶 | 相邻 8×8 块高度差均值 | 转化桌 12.3 / 箱子 11.8 |
| 层占比 | 各层像素占比 | 均衡，**不能一层吃掉 90%** |
| 覆盖率 | UV 面覆盖 | **100%**，不能漏面 |

❌ **「像素级梯度均值」是无效指标**——放大 8 倍后块内是纯色，梯度天然接近 0，看它会得出完全错误的结论。

### 11.4 其他验证手段

- **看高度图**：导出 `_n` 的 A 通道当灰度图直接看，应能一眼看出色块分层
- **光照预览**：用 `_n` 的 AO+法线渲染 Lambert 预览（`work\designer\preview_relief.py`）
- **POM 预渲染**（`work\...\pom_preview.py`）：模拟 shader 沿视线对高度图二分步进采样，**位移像素 > 8% 才及格**，可不开游戏直接看视差是否有效

### 11.5 游戏内检查

1. 资源包放 `resourcepacks/`，**只启用最新版**（同一 mod 的旧版包要关掉，否则同时生效）
2. Iris 已启用；光影 RP Support 选 **LabPBR**；打开 **Parallax(POM)**（默认常关），深度 0.4~0.6
3. `F3+T` 重载；贴脸（1–2 格）看视差，斜看边界有无撕裂，检查各面凹凸力度是否一致

> **shader 配置只在启动时读取**！游戏内改 `iris.properties` / 重载资源**不会**重读启动配置。
> 排查时看 `latest.log`（`Shaders are disabled because enableShaders is set to false` 就是铁证）。
> 必要时**完全重启游戏**排除缓存。

---

## 12. LabPBR 1.3 通道权威速查

### 12.1 `_n`：R=法线X G=法线Y B=材质AO A=高度

| 通道 | 规范定义 |
|---|---|
| R | X 轴，`0`=左 → `255`=右（`128`≈平面） |
| G | Y 轴，`0`=上 → `255`=下（**DirectX Y-**；`128`≈平面） |
| B | **材质 AO**，线性，`0`=100% 遮蔽，`255`=0% 遮蔽 |
| A | **高度/位移**，线性，`255`=0% 深度。**`0` 会让部分光影 POM 出问题，最小建议用 `1`** |

> **B 为什么是 AO**：法线向量长度为 1，已知 R/G 就能用 `sqrt(1 - dot(xy,xy))` 重建 Z，于是 B 空出来存 AO。

**常用组合**：

| 场景 | R | G | B | A |
|---|---|---|---|---|
| 完全平面（最安全默认） | 128 | 128 | 255 | 255 |
| 只有法线，无 AO/高度 | 法线 R | 法线 G | 255 | 255 |
| 缝隙 AO，无高度 | 128 | 128 | 120–220 | 255 |
| 轻微视差 | 法线 R | 法线 G | 220–255 | 180–245 |
| 深凹槽 / 砖缝 | 法线 R | 法线 G | 80–180 | 32–160 |

### 12.2 `_s`：R=感知光滑度 G=F0/金属 B=孔隙率或SSS A=自发光

| 通道 | 规范定义 |
|---|---|
| R | 感知光滑度。`roughness = pow(1 - smoothness, 2.0)` |
| G | `0~229` = **线性 F0**（229/255 ≈ 90%）；`230~254` = 硬编码金属；`255` = 用 albedo 当 F0 |
| B | `0~64` 孔隙率（64=100%）；`65~255` SSS（65=0%，255=100%）。**同像素互斥** |
| A | 自发光，`0`=0%，`254`=100%；**`255` 被忽略（不发光）** |

**硬编码金属位值**（规范原文 N/K 数据见 `参考资料\规范\ShaderLABS-LabPBR-Material-Standard.wiki.txt`）：

| G 值 | 230 | 231 | 232 | 233 | 234 | 235 | 236 | 237 | 255 |
|---|---|---|---|---|---|---|---|---|---|
| 金属 | 铁 | 金 | 铝 | 铬 | 铜 | 铅 | 铂 | 银 | 泛用（albedo 作 F0） |

> 部分光影不支持硬编码金属，会把 `230~255` 全当 `255` 处理。
> 判定代码参考：`is_metal = (specular.y * 255.0) > 229.5`

### 12.3 材质参考表

| 材质 | R | G | B | A |
|---|---|---|---|---|
| 泥土/石头 | 10–50 | 10 | 0–8 | 255 |
| 木头 | 30–80 | 10 | 12 | 255 |
| 羊毛/布料 | 0–25 | 8–12 | 38 | 255 |
| 沙子/砂岩 | 0–30 | 8–12 | 64 | 255 |
| 抛光石材 | 100–170 | 10–15 | 0 | 255 |
| 玻璃/冰 | 220–255 | 10–20 | 0 | 255 |
| 铁块 / 金块 / 铜块 | 170–240 | **230 / 231 / 234** | 0 | 255 |
| 发光纹理 | 视材质 | 10 | 0 | 80–254 |
| 树叶/植物半透 | 10–60 | 8–12 | 80–160 | 255 |

> 旧版 `LabPBR通道备忘` 的不发光材质列 A=`0`，本表统一为 `255`。按规范两者都不发光（`0`=0% 强度、`255`=被忽略），**取 255 更安全**，理由见 §7.3。

### 12.4 分区高度平台参考（相对层级起点）

| 材质 | 高度 (0-1) | `_n`.A (0-255) |
|---|---|---|
| 金属金框 | 0.98~1.00 | 250 |
| 铁（进阶） | 0.92~0.96 | 235 |
| 紫魔法石 | 0.85~0.88 | 217 |
| 红毯 | 0.64~0.72 | 184 |
| 普通底材 | 0.58 | 148 |
| 黑曜石 | 0.44~0.62 | 158 |
| 符文（深凹） | 0.12~0.30 | 77 |

**不是固定标准，是保持结构逻辑的起始值**——必须落在 §2.5 的跨度约束内。
交界用**软权重渐变** + `gauss_blur(2.5)` 过渡，边缘保满高（≥0.98）。

---

## 13. 无头 CLI 速查（不开 GUI）

工具随 Designer 安装于 `D:\Substance 3D Designer\Adobe Substance 3D Designer\`。

```bash
SD="/d/Substance 3D Designer/Adobe Substance 3D Designer"
"$SD/sbsrender.exe" --version                       # version 14.1.2 (build 8986)
"$SD/sbscooker.exe" --inputs X.sbs --output-path OUT --output-name NAME
"$SD/sbsrender.exe" info --input X.sbsar
"$SD/sbsrender.exe" render --input X.sbsar --input-graph "pkg://GRAPH" \
    --output-path OUT --output-name "{inputGraphUrl}_{outputNodeName}" \
    --set-value '$outputsize@9,9'
```

`--set-value '$outputsize@9,9'` 的 `9` 是**指数**：`9,9 → 512×512`，`8,8 → 256`，`7,7 → 128`。

### 工具脚本 `开发管线\sbs_cli.py`

```bash
python sbs_cli.py --help
python sbs_cli.py cook  X.sbs
python sbs_cli.py info  X.sbsar
python sbs_cli.py render X.sbsar --graph "pkg://GRAPH" --outdir out/ \
    --pattern "{inputGraphUrl}_{outputNodeName}" --size 9,9
python sbs_cli.py run X.sbs --graph "pkg://GRAPH" --workdir out/ --outdir out/render/ \
    --size 9,9 --map "资源名=新图片.png"          # --map 可重复
```

环境变量 `DESIGNER_HOME` 可覆盖安装路径。

**`--map` 是「外部 Python 算通道 → Designer 负责打包」的接缝**。

### `.sbs` 是纯 XML 文本

可直接用 Python 读写，不需要 Pysbs。`<filepath>` 相对 `.sbs` 所在目录。

```xml
<package><content>
  <graph>
    <graphOutputs><graphoutput><identifier v="output"/><uid v="..."/></graphoutput></graphOutputs>
    <compNodes>
      <compNode><uid v="..."/>
        <compImplementation><compOutputBridge><output v="graphoutput的uid"/></compOutputBridge></compImplementation>
      </compNode>
      <compNode><uid v="..."/>
        <compImplementation><compFilter><filter v="bitmap"/>
          <parameters><parameter><name v="bitmapresourcepath"/>
            <paramValue><constantValueString v="pkg:///资源名?dependency=PKG_UID"/></paramValue>
          </parameter></parameters>
        </compFilter></compImplementation>
      </compNode>
    </compNodes>
    <options><option><name v="defaultParentSize"/><value v="9x9"/></option></options>
    <root><rootOutputs><rootOutput><output v="graphoutput的uid"/></rootOutput></rootOutputs></root>
  </graph>
  <resource><identifier v="资源名"/><uid v="..."/><type v="bitmap"/>
    <format v="png"/><filepath v="res/x.png"/></resource>
</content></package>
```

**两个必须记住的坑**：
1. **根输出必须走 `<compOutputBridge>` 节点**，不能用图级 `<connections>`（见 §15 坑 1）
2. **`<resource>` 直接挂在 `<content>` 下**，没有 `<resources>` 容器；引用时用
   `pkg:///资源名?dependency=<dependencies 里 ?himself 的 uid>`

---

## 14. Designer Python API 速查（必须在 Designer 内跑）

**入口**：`窗口 ▸ Python 编辑器` → 粘贴代码 → **F5**。
（`^O` 打开脚本不可靠：对话框筛选器是 `*.sbs`，打不开 `.py`。）

### 14.1 节点与参数

**29 个内置合成节点**（`graph.getNodeDefinitions()` 实测枚举）：

```
bitmap  blend  blur  curve  directionalwarp  dirmotionblur  distance  dyngradient
emboss  fxmaps  gradient  grayscaleconversion  hsl  input_color  input_grayscale
input_value  levels  normal  output  passthrough  pixelprocessor  sharpen  shuffle
svg  text  transformation  uniform  valueprocessor  warp
```

> 是 `grayscaleconversion`（**无下划线**），不是 `grayscale_conversion_advanced`。
> 通道拆分/合并用 **`shuffle`**（`rgba_split`/`rgba_merge` 不在内置列表）。
> **没有** `auto_levels` / `ambient_occlusion` / `invert` / `non_uniform_blur` —— 它们属**库节点**。

| 节点 | 参数 | 类型 | 备注 |
|---|---|---|---|
| `bitmap` | `bitmapresourcepath` | string | **需要包内资源 URL**，不是文件路径 |
| `levels` | `levelinlow`/`levelinhigh`/`levelinmid`/`leveloutlow`/`levelouthigh` | float4 | 是 `leveloutlow` 而非 `level_out_low` |
| `normal` | `intensity`(float), `inversedy`(bool), `input2alpha`(bool) | | `input2alpha=True` 会用 alpha 算梯度 |
| `shuffle` | `channelred`/`channelgreen`/`channelblue`/`channelalpha` | int | **0-3 = Input1 RGBA，4-7 = Input2 RGBA** |
| `uniform` | `outputcolor` | ColorRGBA | `ColorRGBA` **大写开头**（`sdbasetypes.ColorRGBA`） |
| `output` | `inputNodeOutput` | SDTypeTexture | 只输出一张纹理 |

### 14.2 库节点（突破 29 个限制）

**库节点不能用 `newNode()` 创建**：

```python
# 1) 载入库包（注意：不是 SDResource.sNewFromFile！见坑 1）
lib = app.getPackageMgr().loadUserPackage(
        r'D:\...\resources\packages\ambient_occlusion.sbs', True, True)
# 2) 取包内合成图资源
res = [r for r in lib.getChildrenResources(True)          # 必须传 isRecursive
       if 'CompGraph' in str(r.getClassName())][0]
# 3) 实例化
node = graph.newInstanceNode(res)     # 定义 ID 统一为 sbs::compositing::sbscompgraph_instance
```

**端口名要读实例，不能猜**：

| 库节点 | 输出 | 输入 |
|---|---|---|
| `auto_levels` | `Output` | `Input` |
| `ambient_occlusion` | `Ambient_Occlusion` | `Source`（另有 `AO_Spread`/`AO_Levels`/`Light_*`） |
| `rgba_split` | `R`/`G`/`B`/`A` | `Input` |

### 14.3 载入图片（`bitmapresourcepath` 必须是包内 URL）

```python
from sd.api.sdresource import SDResource, EmbedMethod
r = SDResource.sNewFromFile(pkg, r'G:\...\height.png', EmbedMethod.Linked)
node.setInputPropertyValueFromId('bitmapresourcepath', SDValueString.sNew(r.getUrl()))
# 得到形如 pkg:///height?dependency=1581078655
```

### 14.4 建图 / 连线 / 计算 / 导出

```python
from sd.api.sbs.sdsbscompgraph import SDSBSCompGraph
g = SDSBSCompGraph.sNew(pkg)
g.setIdentifier('my_graph'); g.setDefaultParentSize(int2(512, 512))
n1 = g.newNode('sbs::compositing::bitmap')
n2 = g.newNode('sbs::compositing::levels')
n1.newPropertyConnectionFromId('unique_filter_output', n2, 'input1')   # 源输出 → 目标输入
n2.setInputPropertyValueFromId('leveloutlow', SDValueFloat4.sNew(float4(.4,.4,.4,.4)))
g.compute()                                   # 阻塞直到完成
for prop in outNode.getDefinition().getProperties(SDPropertyCategory.Output):
    val = outNode.getPropertyValue(prop); tex = val.get() if val is not None else None
    if tex is not None: tex.save(r'G:\...\out.png')
```

### 14.5 GUI 自动化（若必须驱动 Designer）

- **DPI 陷阱**：Windows 缩放 150% 时窗口 API 返回**逻辑**像素、截图/点击用**物理**像素。
  **物理 = 逻辑 × 1.5**，混用会导致点击全部落空。
- Python 编辑器是独立顶层窗口，**标题与主窗口相同**，必须枚举句柄区分。
- 先用鼠标**点击编辑区**让编辑控件获得焦点，否则 `^v` 无效；**激活要在同一条命令里完成**。
- **日志必须写文件并逐行 `flush`**——Designer 控制台无法可靠读取：

```python
_f = open(LOG, 'w', encoding='utf-8')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); _f.write(s+'\n'); _f.flush()
```

---

## 15. 故障字典

| 现象 | 成因 | 处置 |
|---|---|---|
| **渲染全黑** + cook 报 `Unknown filter entry UID` | 根输出没走 `<compOutputBridge>` | 用 `<compOutputBridge>` 接 `<graphOutputs>` |
| **渲染全黑** + cook 报 `Unreachable resource` | `<filepath>` 指向的源图不存在，**退出码仍是 0** | `--map` 重定向到现存 PNG，或补齐源图 |
| 每个 8×8 色块边缘一圈亮/暗线 | 放大后硬台阶被差分 | 加 R/G Pixel Processor（§6.3） |
| `_n` R/G 死平（min≈126 max≈128） | **域混用**：0-1 浮点当 0-255 灰度做差分 | 差分缩放改为 `intensity*2.0`；差分前强平滑 `gauss_blur(5.0)`；**每次生成打印 min/max/mean** |
| 一面有视差、另一面几乎平的 | 多面拼图各面高度基准不同 | 按面格分区，各自归一化到统一幅度（§2.2） |
| 斜看边缘撕裂、出现另一侧图案 | 边缘高度不是满高 | 高度 Levels Out Low ≥200/255，**可见边缘强制 255** |
| 金属看起来像塑料 | 只调了 R，没设 G 的金属预设 | G 设为 230/231/… 或 255（§7.2） |
| 换光影后整体错乱 | 未声明 labPBR，光影按 oldPBR 解码 | 加 `assets/minecraft/optifine/texture.properties`（§10.1） |
| AO 全区 255 没有遮蔽 | 用「邻域亮度 − 当前高度」做判据，暗色贴图恒为负 | 改用「**邻域高度 − 当前高度**」 |
| AO 全 234~255（形同虚设） | HBAO `Height Depth` 域不匹配（0-1 域用了 0-255 标定值） | 0-1 域用 0.15；Designer 内 128px 用 0.03，大尺寸实测 |
| POM 看起来像普通平面 | 高度 A 几乎集中在 224–255，层级过浅 | 重建材质平台，拉开符文/底材/核心高度差；确认光影 POM 已开 |
| 画面边缘彩色污染 | 透明区携带 RGB / 未采样区 / mipmap | 透明区 RGB 清零；检查轮廓高度 |
| 底部出现不该有的红色 | 基础色贴图的**采样区域**含红毯色块（UV 决定） | 先查基础纹理和 UV，**改 `_s` 无效** |
| 进阶版发光过脏 | 普通/进阶版盲目共用辉光规则 | 进阶版灰铁框用铁金属属性；只让明确的核/符文发光 |
| 脚本**静默挂起**，Designer 不报错 | 用 `SDResource.sNewFromFile()` 载入 `.sbs` | 改用 `SDPackageMgr.loadUserPackage()` |
| 同样静默挂起 | 载入 `rgba_merge.sbs` 这个特定包 | 组装改用内置 `shuffle` |
| 导出纯色常数图（法线 R/G 恒 127） | bitmap 没真正载入 | `sNewFromFile` + `getUrl()` 写入 `bitmapresourcepath` |
| `Normal` 节点输出恒为平面 | 输入或用参不当 | 改为**由高度图差分生成法线** |
| `getChildrenResources() missing 1 required positional argument` | 漏传参数 | 传 `isRecursive` |
| `cannot import name 'colorrgba'` | 大小写 | `from sd.api.sdbasetypes import ColorRGBA` |
| `No module named 'sd.api.sdvalueresource'` | 该模块不存在 | 用 `SDResource.sNewFromFile` |
| Designer 内置 Python `import numpy` 失败 | 自带 Python 无第三方库 | 数值计算放外部 Python |
| 替换 resourcepacks 里的 zip 报文件被占用 | Minecraft 进程持有句柄 | `Stop-Process` 关 java → 替换 → **提醒重开游戏** |
| PowerShell 列 zip 显示 `assets\...` | shell 显示转义 | 用 Python `zipfile.namelist()` 验证——实际是正斜杠，**虚惊** |

---

## 16. 必须向用户求助的决策点

**以下判断在不确定时必须问用户，不要自行猜测**（原文明确要求）：

1. **蒙版的制作** —— 哪些像素属于金属 / 属哪个材质分区
2. **几何形状的判断** —— 哪里是凸起、哪里是凹陷
3. **材质的属性判断** —— 对应什么物理材质、用什么通道值
4. **基准版本确认** —— 本项目同时存在 v4~v7，**开工前必须确认基准**
5. **大尺度几何形状** —— 原贴图用明暗渐变表现受光/背光，**背光面极易被误判为凹陷**

---

## 17. 项目约定与禁止事项

### 约定

- 所有生成脚本用 `ROOT = r"G:\PBR"` 起算
- 交付包必须有 `assets/minecraft/optifine/texture.properties` → `format=lab-pbr/1.3`
- 版本管理：**正式版只留最新**，旧版移入 `历史版本\`；修订记录写入对应版本说明
- 生产目录分离：`work/src/`（原贴图）`work/masks/`（蒙版）`work/out/`（产物）
- **脚本应确定性生成。不要手工改一张输出图后又用脚本覆盖**，避免源文件/蒙版/最终结果不一致
- 每次生成记录：输入模组版本、MC/NeoForge/Iris/光影版本、高度平台与通道参数、改过的基础色贴图、已知限制

### 禁止

- ❌ 用直方图均衡/对比拉伸"拉"高度
- ❌ 在别人的成品上缝缝补补（先确认基准版本）
- ❌ **手工列举 UV 区域**——必须脚本化从模型 json 提取全部面（**漏一个是 100% 会发生的事**）
- ❌ 未确认基准版本就动手
- ❌ 声称"完成"却没有量化验证
- ❌ 资源包做它做不到的事：**不能**改方块实体渲染器控制的动画轨迹、书本开合/旋转/悬浮、动态粒子、模组硬编码的发光（这些需要 NeoForge 客户端扩展或注入渲染器）

---

## 18. 权威来源

| 文档 | 位置 | 用途 |
|---|---|---|
| **LabPBR 材料标准（规范全文）** | `参考资料\规范\ShaderLABS-LabPBR-Material-Standard.wiki.txt` | **通道语义唯一权威** |
| LabPBR 实现要求 | `参考资料\规范\ShaderLABS-LabPBR-Implementation-Requirements.wiki.txt` | 材质包/光影各自必做与可选清单 |
| PBR 格式声明与 oldPBR 差异 | `参考资料\规范\shaders.properties-PBR-Standards.html` | `texture.properties` 声明方式 |
| 1.3 解码参考代码 | `参考资料\规范\LVutner-LabPBR-unpacking-template.glsl` | 含 `is_metal` 判定 |
| 参考资料总索引 | `参考资料\README-参考资料索引.md` | 工具/中文资料/参考材质包/光影 全索引 |
| **Agent约束-Designer 制作流程** | `正式版\` | **节点级流程纲领**（本文 §6~§8 依据） |
| **Agent约束-LabPBR 通道备忘** | `正式版\` | 通道速查与材质参考表 |
| **PBR 材质包制作经验与流程规范** | `正式版\` | 工程参数、交付检查清单、labPBR 声明根因 |
| **PBR 制作注意事项与 Agent 约束** | `正式版\` | **硬性约束清单 + 实战复盘** |
| Substance 命令 行无头流程 | `正式版\` | CLI + `.sbs` XML + 两个坑 |
| Substance 3D Designer 使用总结 | `正式版\` | Python API 用法、坑位清单、内外分工 |
| Substance 3D Designer 操作流程 | `正式版\` | Designer 实操版（准备/建图/蒙版/导出/验证） |
| WORKLOG 工作过程与注意点 | `开发管线\` | 附魔灌注台工作日志与排错记录（P1~P7） |
| Designer 建图说明 | `work\designer\README-Designer建图说明.md` | 脚本化建图的具体步骤 |
| agent.zip（示意图包） | `项目素材\agent.zip` | 上述两份 Agent 约束文档 + 20 张节点连线示意图 |

> 本总纲是把以上材料**收敛后的单一入口**。需要细节时按上表定位到原文档，不要凭记忆推断参数。
