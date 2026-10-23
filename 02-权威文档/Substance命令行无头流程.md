> **License**: 本文档受 MIT License 保护 (Copyright (c) 2026 92609882-UX|渐行渐远)。

# Substance 3D Designer 命令行无头流程

> **一句话**：Designer 随附 4 个命令行 exe，配合「`.sbs` 是纯 XML」这个事实，
> 可以**完全不打开 GUI** 完成 cook（.sbs → .sbsar）和 render（.sbsar → PNG）。
> 工具脚本：`开发管线\sbs_cli.py`。

## 1. 为什么可行

| 事实 | 说明 |
|---|---|
| 命令行工具随 Designer 一起装 | `D:\Substance 3D Designer\Adobe Substance 3D Designer\` 下有 `sbscooker.exe` / `sbsrender.exe` / `sbsbaker.exe` / `sbsupdater.exe`（本项目实测 14.1.2） |
| `.sbs` 是**纯 XML 文本** | 文件头就是 `<?xml version="1.0" encoding="UTF-8"?><package>…`，可直接用文本工具读写 |
| `<resource>` 的路径可重定向 | `<filepath v="res/x.png"/>` 是**相对 `.sbs` 所在目录**的路径 |

**不可行的那条路**：Designer 内置的 `sd` Python API（`resources\python\sd`）依赖 Designer 进程内注入的
`designersdk.dll`，磁盘上不存在该 dll，**外部 Python 无法 `import sd`**。所以建图逻辑要么在 GUI 内跑，
要么直接生成/修改 `.sbs` 文本。

## 2. 命令行工具速查

```bash
SD="/d/Substance 3D Designer/Adobe Substance 3D Designer"

# 版本
"$SD/sbsrender.exe" --version          # version 14.1.2 (build 8986)

# cook：.sbs → .sbsar
"$SD/sbscooker.exe" --inputs X.sbs --output-path OUTDIR --output-name NAME

# info：看 .sbsar 里有哪些图 / 输入 / 输出
"$SD/sbsrender.exe" info --input X.sbsar

# render
"$SD/sbsrender.exe" render --input X.sbsar \
    --input-graph "pkg://GRAPH_NAME" \
    --output-path OUTDIR \
    --output-name "{inputGraphUrl}_{outputNodeName}" \
    --set-value '$outputsize@9,9'
```

`--set-value '$outputsize@9,9'` 里的 `9` 是**指数**：`9,9 → 512×512`，`8,8 → 256×256`，`7,7 → 128×128`。

## 3. `.sbs` 文件结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<package>
  <identifier v="Unsaved Package"/>
  <formatVersion v="1.1.0.202401"/>
  <updaterVersion v="1.1.0.202401"/>
  <fileUID v="{838d4cdc-...}"/>
  <versionUID v="0"/>
  <dependencies>
    <dependency><filename v="?himself"/><uid v="1581079063"/><type v="package"/>
      <fileUID v="0"/><versionUID v="0"/></dependency>
  </dependencies>
  <content>
    <graph>
      <identifier v="alchemical_chest_pbr"/>
      <uid v="1581079064"/>
      <graphOutputs>
        <graphoutput><identifier v="output"/><uid v="1581079082"/></graphoutput>
      </graphOutputs>
      <compNodes>
        <compNode>
          <uid v="1581079065"/>
          <GUILayout><gpos v="-1280 -480 0"/></GUILayout>
          <compOutputs><compOutput><uid v="1581079066"/><comptype v="1"/></compOutput></compOutputs>
          <compImplementation>
            <compFilter>
              <filter v="bitmap"/>                       <!-- 节点类型 -->
              <parameters>
                <parameter><name v="bitmapresourcepath"/><relativeTo v="0"/>
                  <paramValue><constantValueString v="pkg:///normal_alchemical_chest?dependency=1581079063"/></paramValue>
                </parameter>
              </parameters>
            </compFilter>
          </compImplementation>
        </compNode>
      </compNodes>
      <baseParameters/>
      <options><option><name v="defaultParentSize"/><value v="9x9"/></option></options>
      <root><rootOutputs>
        <rootOutput><output v="1581079082"/><format v="0"/><usertag v=""/></rootOutput>
      </rootOutputs></root>
    </graph>
    <resource><identifier v="normal_alchemical_chest"/><uid v="1581079067"/>
      <type v="bitmap"/><format v="png"/><filepath v="out/normal_alchemical_chest.png"/></resource>
  </content>
</package>
```

### ⚠ 两个必须记住的坑

1. **根输出必须走 `<compOutputBridge>`**，不能用图级 `<connections>`：

   ```xml
   <compNode>
     <uid v="桥接节点uid"/>
     <connections><connection><identifier v="input1"/><connRef v="上游输出uid"/></connection></connections>
     <compImplementation><compOutputBridge><output v="graphoutput的uid"/></compOutputBridge></compImplementation>
   </compNode>
   ```

   写错的典型症状：`sbscooker` 报 **`Unknown filter entry UID`**，且渲染出来**全黑**（实测踩过）。

2. **`<resource>` 直接挂在 `<content>` 下**，没有 `<resources>` 容器；`<graph>` 里引用时用
   `pkg:///资源名?dependency=<dependencies 里 ?himself 的 uid>`。

## 4. 工具脚本 `开发管线\sbs_cli.py`

```bash
# 看有哪些子命令
python sbs_cli.py --help

# 1) cook
python sbs_cli.py cook G:/PBR/work/designer/build_ns_graph.sbs

# 2) 查看 .sbsar 结构
python sbs_cli.py info out/build_ns_graph.sbsar

# 3) 渲染
python sbs_cli.py render out/build_ns_graph.sbsar --graph "pkg://alchemical_chest_pbr" \
    --outdir out/ --pattern "{inputGraphUrl}_{outputNodeName}" --size 9,9

# 4) 一步到位：换资源路径 + cook + render
python sbs_cli.py run G:/PBR/work/designer/build_ns_graph.sbs \
    --graph "pkg://alchemical_chest_pbr" \
    --workdir out/ --outdir out/render/ \
    --pattern "{inputGraphUrl}_{outputNodeName}" --size 9,9 \
    --map "alchemical_chest_128x=G:/PBR/work/designer/alchemical_chest_128x.png" \
    --map "normal_alchemical_chest=G:/PBR/work/designer/height_512.png"
```

`--map 资源名=图片路径` 可以重复，用来把 `.sbs` 里的输入图换成外部算好的 PNG——
**这就是「外部 Python 算高度/AO，Designer 负责打包成 LabPBR 四通道」的接缝**。

环境变量 `DESIGNER_HOME` 可覆盖 Designer 安装路径（默认自动探测 `D:\Substance 3D Designer\Adobe Substance 3D Designer`）。

## 5. 实测记录（2026-09-11）

```
$ sbs_cli.py --help                                        EXIT=0  列出 cook/info/render/run
$ sbs_cli.py info  .../tmpl.sbsar                          EXIT=0  GRAPH-URL pkg://alchemical_chest_pbr
$ sbs_cli.py run build_ns_graph.sbs --graph pkg://alchemical_chest_pbr \
      --workdir _test --outdir _test/out --size 9,9 --map ×4        EXIT=0
    → _test/build_ns_graph_cli.sbs (23219 B)
    → _test/build_ns_graph_cli.sbsar (2878 B)
    → _test/out/{inputGraphUrl}_{outputNodeName}.png  512×512

像素检查：
    output.png    (512,512,4)  R 0.0–205.0    A 0.0–205.0
    output_1.png  (512,512,4)  R 140.0–181.0  A 255.0–255.0
```

## 6. 推荐的分工

```
[外部 Python / 本项目已有脚本]              [Designer 命令行，无需 GUI]
  色块分层、高度、法线、AO  ───> PNG ──┐
                                       ├─> .sbs (换 resource) ─> sbscooker ─> .sbsar ─> sbsrender ─> _n.png / _s.png
  .sbs 里已建好的 Blur/HBAO/Shuffle  ──┘
```

- **适合放 Designer**：HBAO、Blur、Shuffle 打包 RGBA、Normal 节点的归一化等需要库节点精度的环节。
- **适合放外部 Python**：色块分区、按模型 UV 裁面、批量命名、指标验证——这些用 numpy 更快也更可控。
- **GUI 只在"新建/改图结构"时需要**；改参数、换输入图、批量出图都可以无头跑。
