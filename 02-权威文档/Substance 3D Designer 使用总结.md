# Substance 3D Designer 使用总结（ProjectE PBR 项目实践）

> 本文记录在 `G:\PBR` 三个 LabPBR 材质包项目中实际使用 Substance 3D Designer 14.1.2 的完整经验：
> 环境、Python API 的正确用法、踩过的坑、以及可复用的自动化建图流程。
> 配套文档：`正式版\Substance 3D Designer 操作流程.md`（手工操作版）、`正式版\PBR材质包制作经验与流程规范.md`（通道规范）。

## 一、环境

```
D:\Substance 3D Designer\Adobe Substance 3D Designer\Adobe Substance 3D Designer.exe
  ├── plugins\pythonsdk\                        自带 Python 3.11（含 python.exe）
  ├── resources\python\sd\                      Python API（sd.api.*）
  ├── resources\documentation\pythonapi\html\   API 文档（离线 HTML + _sources/*.rst.txt）
  ├── resources\packages\*.sbs                  700+ 库节点定义
  └── tools\scripting\                          传统脚本接口（functions.py，非本流程所用）
```

**关键约束**：`sd` 模块依赖 Designer 进程内的 C++ 运行时（`designersdk.dll`），该 dll **磁盘上不存在**，
由 Designer 启动时注入。因此：

- ❌ 外部 Python **无法** `import sd` 并操作 Designer（会报 `SD API library not found: ...designersdk.dll`）
- ✅ 脚本**必须**在 Designer 内运行：`窗口 ▸ Python 编辑器 ▸ 粘贴代码 ▸ F5`

## 二、命令行控制（自动化必需）

Designer 是 GUI 程序，若要自动跑脚本，用以下方式：

### 2.1 DPI 陷阱（最易踩）

Windows 显示缩放 150% 时：
- 窗口坐标 API 返回**逻辑**像素（如 1707×1067）
- 截图/模拟点击用**物理**像素（2560×1600）
- **换算：物理 = 逻辑 × 1.5**（两者不一致会导致点击全部落空）

### 2.2 精确定位窗口

Designer 的「Python 编辑器」是独立顶层窗口，**标题与主窗口相同**，必须枚举句柄区分：

```powershell
# 枚举进程所有可见顶层窗口，输出逻辑+物理坐标
[WinEnum]::List([uint32]$pid)
```

主窗口与 Python 编辑器通常是两个等大窗口（如 `(847,0)-(1712,515)` 与 `(847,509)-(1712,1024)`）。

### 2.3 激活 + 输入

```powershell
Add-Type -AssemblyName System.Windows.Forms
$t::SetForegroundWindow([IntPtr]$editorHwnd)   # 用句柄精确激活
Start-Sleep -Milliseconds 800
[System.Windows.Forms.SendKeys]::SendWait("^a")   # 全选
[System.Windows.Forms.SendKeys]::SendWait("^v")   # 粘贴
[System.Windows.Forms.SendKeys]::SendWait("{F5}") # 运行
```

**两个必备前置动作**：
1. 先用鼠标**点击编辑区**让编辑控件获得焦点，否则 `^v` 无效果
2. 每个工具调用之间 Designer 可能失焦，**激活要在同一条命令里完成**

### 2.4 用 Ctrl+O 打开脚本不可靠

Python 编辑器的「打开」对话框筛选器是 `*.sbs`，**打不开 `.py`**；若菜单没点中还会落到主窗口。
**结论：直接把代码粘贴进编辑区**，不要走文件打开流程。

### 2.5 日志必须写文件

Designer 控制台内容无法直接读取（OCR 对混合中英符号识别不可靠）。
**在脚本里显式打开日志文件并逐行 `flush`** —— 即使脚本中途挂起，已写入的部分仍可读取：

```python
_f = open(LOG, 'w', encoding='utf-8')
def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)                      # 同时进控制台
    _f.write(s + '\n'); _f.flush()  # 关键：立即落盘
```

## 三、Python API 权威用法

### 3.1 节点 ID 从哪来

| 来源 | 内容 | 说明 |
|---|---|---|
| `graph.getNodeDefinitions()` | **29 个**内置合成节点 | 实跑枚举，最权威 |
| `resources\documentation\...\_sources\pythonapi\modules\sbs_compositing.rst.txt` | 官方完整定义清单 | 含每个节点的属性名与类型 |
| `resources\packages\*.sbs` | **700+ 库节点** | 需走 `newInstanceNode`（见 3.3） |

**29 个内置节点**（实测枚举）：

```
bitmap  blend  blur  curve  directionalwarp  dirmotionblur  distance  dyngradient
emboss  fxmaps  gradient  grayscaleconversion  hsl  input_color  input_grayscale
input_value  levels  normal  output  passthrough  pixelprocessor  sharpen  shuffle
svg  text  transformation  uniform  valueprocessor  warp
```

**注意易错点**：
- 是 `grayscaleconversion`（**无下划线**），不是 `grayscale_conversion_advanced`
- 通道拆分/合并用 `shuffle`（`rgba_split`/`rgba_merge` 不在内置列表）
- **没有** `auto_levels` / `ambient_occlusion` / `invert` / `non_uniform_blur`（它们属库节点）

### 3.2 关键节点参数名（实测）

| 节点 | 参数 | 类型 | 说明 |
|---|---|---|---|
| `bitmap` | `bitmapresourcepath` | string | **需要包内资源 URL**，不是文件路径（见 3.4） |
| `levels` | `levelinlow`/`levelinhigh`/`levelinmid`/`leveloutlow`/`levelouthigh` | float4 | 注意是 `leveloutlow` 而非 `level_out_low` |
| `normal` | `intensity`(float), `inversedy`(bool), `input2alpha`(bool) | | `input2alpha=True` 时会用 alpha 通道算梯度 |
| `shuffle` | `channelred`/`channelgreen`/`channelblue`/`channelalpha` | int | **0-3=Input1 的 RGBA，4-7=Input2 的 RGBA** |
| `uniform` | `outputcolor` | ColorRGBA | 注意 `ColorRGBA` 是**大写开头**（`sdbasetypes.ColorRGBA`） |
| `output` | `inputNodeOutput` | SDTypeTexture | 只输出一张纹理 |

### 3.3 库节点（突破 29 个限制）

**库节点不能用 `newNode()` 创建**，必须：

```python
# 1) 载入库包（注意：不是 SDResource.sNewFromFile！见坑位）
lib = app.getPackageMgr().loadUserPackage(
        r'D:\...\resources\packages\ambient_occlusion.sbs', True, True)
# 2) 取包内的合成图资源
res = [r for r in lib.getChildrenResources(True)          # 必须传 isRecursive
       if 'CompGraph' in str(r.getClassName())][0]
# 3) 实例化为节点
node = graph.newInstanceNode(res)     # 定义 ID 统一为 sbs::compositing::sbscompgraph_instance
```

**端口名要读实例，不能猜**：

| 库节点 | 输出端口 | 输入端口 |
|---|---|---|
| `auto_levels` | `Output` | `Input` |
| `ambient_occlusion` | `Ambient_Occlusion` | `Source`（另有 `AO_Spread`/`AO_Levels`/`Light_*`） |
| `rgba_split` | `R`/`G`/`B`/`A` | `Input` |

### 3.4 载入图片

`bitmapresourcepath` 需要**包内 URL**，直接给文件路径不生效（会得到空白常数图）：

```python
from sd.api.sdresource import SDResource, EmbedMethod
r = SDResource.sNewFromFile(pkg, r'G:\...\height.png', EmbedMethod.Linked)  # Linked=引用原文件
node.setInputPropertyValueFromId('bitmapresourcepath', SDValueString.sNew(r.getUrl()))
# 得到形如 pkg:///height?dependency=1581078655
```

> 另有一处易错：`SDValueResource` 这个模块**不存在**（`sd.api.sdvalueresource` 导入会失败）。

### 3.5 建图 / 连线 / 计算 / 导出

```python
from sd.api.sbs.sdsbscompgraph import SDSBSCompGraph
g = SDSBSCompGraph.sNew(pkg)
g.setIdentifier('my_graph')
g.setDefaultParentSize(int2(512, 512))

n1 = g.newNode('sbs::compositing::bitmap')
n2 = g.newNode('sbs::compositing::levels')
n1.newPropertyConnectionFromId('unique_filter_output', n2, 'input1')  # 源输出 → 目标输入
n2.setInputPropertyValueFromId('leveloutlow', SDValueFloat4.sNew(float4(.4,.4,.4,.4)))

g.compute()                                   # 阻塞直到计算完成
for prop in outNode.getDefinition().getProperties(SDPropertyCategory.Output):
    val = outNode.getPropertyValue(prop)
    tex = val.get() if val is not None else None
    if tex is not None:
        tex.save(r'G:\...\out.png')           # 导出 PNG
```

## 四、坑位清单（都实际踩过）

| # | 现象 | 原因 | 正确做法 |
|---|---|---|---|
| 1 | 脚本**静默挂起**，Designer 不报错不崩溃，线程卡死 | 用 `SDResource.sNewFromFile()` 载入 `.sbs` | 用 `SDPackageMgr.loadUserPackage()` |
| 2 | 同样静默挂起 | 载入 `rgba_merge.sbs` 这个特定包 | 组装改用内置 `shuffle` |
| 3 | `getChildrenResources() missing 1 required positional argument` | 漏传参数 | 传 `isRecursive`（`True`/`False`） |
| 4 | 导出的是**纯色常数图**（法线 R/G 恒 127） | bitmap 没真正载入 | 用 `sNewFromFile` + `getUrl()` 写入 `bitmapresourcepath` |
| 5 | `Normal` 节点输出恒为平面 | 输入或用参不当 | 本项目中改为由高度图差分生成法线（也符合规范 §5.3） |
| 6 | `cannot import name 'colorrgba'` | 大小写 | `from sd.api.sdbasetypes import ColorRGBA` |
| 7 | `No module named 'sd.api.sdvalueresource'` | 该模块不存在 | 用 `SDResource.sNewFromFile` |
| 8 | 点击全部落空 | DPI 缩放 150%，逻辑/物理坐标混用 | 物理坐标 = 逻辑 × 1.5 |
| 9 | `^v` 粘贴无效 | 编辑控件没焦点 | 先鼠标点击编辑区 |
| 10 | 无法读取控制台输出 | OCR 对混合中英符号不可靠 | 脚本内写日志文件 + 逐行 flush |
| 11 | 内置 Python 里 `import numpy` 失败 | Designer 自带 Python 无第三方库 | 数值计算放外部 Python，Designer 只做建图/组装/导出 |

## 五、本项目采用的流程（Designer + Python 分工）

```
[外部 Python]                          [Designer 内 Python API]
  gen_height_platform.py  ─┐
  gen_normal.py           ─┼─> PNG ──> build_*.py
  gen_ao.py               ─┘            ├ bitmap 载入
                                        ├ auto_levels (库节点)
                                        ├ ambient_occlusion (库节点, 真 HBAO)
                                        ├ shuffle 组装 RGBA 四通道
                                        ├ output
                                        └ compute() + tex.save() ──> _n.png / _s.png
```

**分工理由**：
- 高度平台、对称性、遮罩等**数值逻辑**用外部 Python（有 numpy，易调试、可复现）
- **四通道组装与导出**放 Designer（`shuffle`/`output` 稳定可靠，且符合"用 Designer 出图"的要求）
- **HBAO 交给 Designer 库节点**（比自写遮罩真实得多：10~255 共 230 级灰阶 vs 自写 150~255）

## 六、可复用脚本清单（`G:\PBR\work\designer\`）

| 脚本 | 作用 |
|---|---|
| `build_v6_mixed.py` | **主力**：Designer 内建 `_n`/`_s` 图并导出（含库节点 HBAO） |
| `build_ns_graph.py` | v6 初版（纯内置节点 + Python AO），保留对照 |
| `gen_height_platform.py` | 按 `base_chest` UV 切 18 面格 → 语义高度平台 |
| `gen_normal.py` | 高度差分 → DirectX 法线 |
| `gen_ao.py` | 高度差遮罩 AO（已被 HBAO 取代） |
| `rebuild_all_final.py` | **全包 163 个 `_n` 分类重做**（方块保层次 / 物品保安全） |
| `audit_all_pbr.py` | 全包体检：边缘/对称/幅度/法线/AO 异常扫描 |
| `final_accept.py` | 交付验收 |
| `probe_*.py` | API 探测（节点 ID、库节点、属性名）——排错时先跑这些 |

## 七、版本与授权

- 适用：Substance 3D Designer 14.1.2（其他版本节点 ID/参数名可能不同，用 `probe_*.py` 重新确认）
- 本文档受 MIT License 保护 (Copyright (c) 2026 渐行渐远)
