> **注意**：本目录是**外部公开资料的本地副本**，版权归各原作者（见每项来源链接），**不适用**根目录 LICENSE 的 MIT 授权。仅供离线查阅。

# 参考资料索引

抓取时间：2026-09-09（来源：原始站点 / jsDelivr CDN / wiki 镜像）

## 目录

```
参考资料\
├── 规范\        LabPBR 格式规范与光影端解码参考（最优先看）
├── 中文资料\    中文规范翻译与制作教程
├── 工具\        生成 / 打包工具的文档
├── 参考材质包\  开源 labPBR 材质包 README
└── 光影\        光影端 labPBR 支持说明
```

## 一、规范

| 文件 | 来源 | 内容要点 |
|---|---|---|
| `ShaderLABS-LabPBR-Material-Standard.wiki.txt` | [shaderlabs.org](https://shaderlabs.org/wiki/LabPBR_Material_Standard) | **权威规范全文**。`_n`：R/G = 法线 XY（DirectX Y-），B = AO（线性，0=全遮蔽），A = POM 高度（0 = 25% 深度，建议最小 1）；`_s`：R = 感知平滑度，G = F0（0–229）/硬编码金属（230–254）/255 用 albedo，B = 孔隙率(0–64) 或 SSS(65–255)，A = 自发光（255 被忽略） |
| `ShaderLABS-LabPBR-Implementation-Requirements.wiki.txt` | [shaderlabs.org](https://shaderlabs.org/wiki/LabPBR_Implementation_Requirements) | 材质包与光影各自"必做 / 可选"清单 |
| `ShaderLABS-LabPBR-Supported-Packs.wiki.txt` | [shaderlabs.org](https://shaderlabs.org/wiki/LabPBR_Supported_Packs) | 已支持 labPBR 的材质包列表 |
| `ShaderLABS-LabPBR-Materials.html` | [shaderlabs.org](https://shaderlabs.org/wiki/LabPBR_Materials) | 材质参数页（该页 `action=raw` 只有 38 字节，故存 HTML） |
| `shaders.properties-PBR-Standards.html` | [shaders.properties](http://shaders.properties/current/how-to/pbr_standards/) | `texture.properties` 声明方式、labPBR 与 oldPBR(seusPBR) 的差异 |
| `LVutner-LabPBR-unpacking-template.glsl` | [gist](https://gist.github.com/LVutner/c07a3cc4fec338e8fe3fa5e598787e47) | 1.3 通道解码参考代码，含 `is_metal = (specular.y * 255.0) > 229.5` 判定 |
| `rre36-wiki-Normal-Texture-Details.html` | [wiki 镜像](https://github-wiki-see.page/m/rre36/lab-pbr/wiki/Normal-Texture-Details) | 法线贴图通道细节（原始 wiki） |
| `rre36-wiki-Specular-Texture-Details.html` | [wiki 镜像](https://github-wiki-see.page/m/rre36/lab-pbr/wiki/Specular-Texture-Details) | 反射贴图通道细节，含 8 种硬编码金属的 N/K 数据 |
| `rre36-wiki-Implementation-Requirements.html` | [wiki 镜像](https://github-wiki-see.page/m/rre36/lab-pbr/wiki/Implementation-Requirements) | 实现要求（与 shaderlabs 版互为印证） |
| `rre36-wiki-Version-History.html` | [wiki 镜像](https://github-wiki-see.page/m/rre36/lab-pbr/wiki/Version-History) | 版本沿革，1.3 的 f0 线性化与法线归一化变更 |
| `rre36-wiki-Resource-Packs.html` | [wiki 镜像](https://github-wiki-see.page/m/rre36/lab-pbr/wiki/Resource-Packs) | 带 Normals/Height/AO/Porosity/Emission/SSS 特性矩阵的材质包列表 |

## 二、中文资料

| 文件 | 来源 | 内容要点 |
|---|---|---|
| `MineGraph-LabPBR材质标准.html` | [docs.minegraph.cn](https://docs.minegraph.cn/labpbrmaterialstandard) | 规范的中文翻译 |
| `BessonNote-关于Minecraft资源包中的LabPBR标准.html` | [beishanair.github.io](https://beishanair.github.io/BessonNote/2026/02/27/labpbr/) | 个人制作笔记：Blockbench 绘制 → 放大 → 通道分离/合并 → Materialize 生成法线；作者亦提到"这方面教程很少" |
| `苦力怕论坛-基岩版PBR贴图教程.html` | [klpbbs.com](https://klpbbs.com/thread-118830-1-1.html) | 基岩版 `texture_set.json` 与 MER 通道（对 Java 版参考价值有限） |

## 三、工具

| 文件 | 来源 | 内容要点 |
|---|---|---|
| `PixelGraph-README.md` | [Null-MC/PixelGraph](https://github.com/Null-MC/PixelGraph) | 在 raw 贴图空间工作，发布到 labPBR 1.3 等多种编码；CLI + Docker；注意商用许可门槛 |
| `PixelGraph-wiki-Generating-Normal-Maps.html` | 同上 wiki | 高度图 → 法线，`strength` / `blur` / `wrapping` 参数 |
| `PixelGraph-wiki-Generating-Occlusion-Maps.html` | 同上 wiki | 高度图 → AO，`quality` / `step-count` / `z-bias` / `z-scale`；wiki 建议预烘焙（很慢） |
| `PixelGraph-wiki-Pack-Profile-Properties.html` | 同上 wiki | `*.pack.yml` 发布配置（`pbr-lab1.3-64x` 等） |
| `comfy-ui-minecraft-pbr-README.md` | [jasonjgardner](https://github.com/jasonjgardner/comfy-ui-minecraft-pbr) | GPU 节点打包 labPBR/Bedrock；`Derive AO + Height` 用 Frankot–Chellappa 从法线反推高度 |
| `Textureslap-README.md` | [Fitzgerald777](https://github.com/Fitzgerald777/Textureslap) | Pillow + NumPy + SciPy(Sobel) 生成法线/AO/粗糙度，CLI + GUI |
| `BumpToNormalMap-README.md` | [MircoWerner](https://github.com/MircoWerner/BumpToNormalMap) | 最小 Sobel → 法线实现，数学写得最清楚 |
| `RGBA-Formats-Converter-README.txt` | [flodri](https://github.com/flodri/RGBA-Formats-Converter) | 旧格式 → labPBR 转换器（该仓库无完整 README，只有此文件 + Releases） |

## 四、参考材质包

| 文件 | 来源 | 内容要点 |
|---|---|---|
| `Textureless-README.md` | [Null-MC/Textureless](https://github.com/Null-MC/Textureless) | **CC0**，纯材质数值包，最适合读通道数值对照材质语义 |
| `Vanilla-Normals-Renewed-README.md` | [Poudingue](https://github.com/Poudingue/Vanilla-Normals-Renewed) | 原版贴图 + 法线/光泽，同时兼容 oldPBR 与 labPBR |
| `MizunoPBR-README.md` | [survivalLABS](https://github.com/survivalLABS/MizunoPBR) | Mizuno 16x 的 labPBR 1.3 版本 |
| `Oversized-README.md` | [Null-MC/Oversized](https://github.com/Null-MC/Oversized) | 公共领域高清贴图 + CTM，labPBR 1.3 编码 |

## 五、光影

| 文件 | 来源 | 内容要点 |
|---|---|---|
| `photon-labPBR支持-DeepWiki.html` | [deepwiki.com](https://deepwiki.com/sixthsurge/photon/3.3-labpbr-support) | Photon 的 labPBR 解码实现，含硬编码金属 F0/F82 处理 |

## 格式说明

- `.wiki.txt` —— MediaWiki 源码（规范原文）。`== 标题 ==`、`'''粗体'''`、`[[内链]]`；用文本编辑器或支持 wikitext 的编辑器查看
- `.html` —— 网页快照，用浏览器打开。正文完整，外部样式可能缺失
- `.md` / `.txt` / `.glsl` —— Markdown / 纯文本 / 着色器代码

## 与本地规范的关系

`正式版\PBR材质包制作经验与流程规范.md` 是**本项目自研规范**，管的是工程参数（放大倍数、分区高度、法线强度、AO 基值等）。本目录的 shaderLABS 规范只定义**通道语义**，不涉及放大与分区策略。两者互补：

- 改 `_n` / `_s` 的**通道含义** → 先查本目录
- 改**放大/分区/强度**等工程参数 → 查本地规范

## 未收录

- 各工具与材质包的完整源码仓库（体积大；需要时用 `git clone` 或 jsDelivr 单独取）
- 视频教程（B 站等，非文档形态）
- `RGBA-Formats-Converter` 的完整文档（上游仓库没有）

## 六、第二轮补充（2026-09-10）

### 工具文档（新增）

| 文件 | 来源 | 内容要点 |
|---|---|---|
| `PixelGraph-wiki-PBR-Channel-Encoding.html` | Null-MC/PixelGraph wiki | labPBR 各通道的编码规则（最直接的一页） |
| `PixelGraph-wiki-Material-Formats.html` | 同上 | raw 材质空间与导出格式 |
| `PixelGraph-wiki-Texture-Naming.html` | 同上 | `_n`/`_s` 命名与自动配对 |
| `PixelGraph-wiki-Pack-Input-Properties.html` | 同上 | `input.yml` 输入配置 |
| `PixelGraph-wiki-Creating-Materials-and-Adding-Textures.html` | 同上 | 材质定义与贴图添加流程 |
| `PixelGraph-wiki-Using-Multi-Part-Images.html` | 同上 | 双高方块/CTM 的拆分 |
| `PixelGraph-wiki-Create-a-New-Project.html` | 同上 | 项目初始化 |
| `substance3d_minecraft-README.md` | jasonjgardner | Substance Designer/Painter 的 labPBR 工具链 |
| `Texture-Set-Manager-README.md` | Cubeir | Bedrock RTX / Vibrant Visuals 的 texture_set 自动生成 |
| `NormalMapsGenerator-README.md` | mrglaster | 用 DeepBump AI 模型生成法线 |

### 光影文档（新增）

| 文件 | 来源 | 内容要点 |
|---|---|---|
| `photon-README.md` | sixthsurge/photon | 完整 labPBR 支持的光影 |
| `DrDestens_McShader-README.md` | DrDesten | 同时支持 labPBR 与 oldPBR 的光影 |

### 参考材质包（完整内容）

| 目录 | 来源 | 说明 |
|---|---|---|
| `Vanilla-Normals-Renewed/` | Poudingue（浅克隆 11M） | 原版贴图的法线/光泽，兼容 oldPBR 与 labPBR |
| `MizunoPBR/` | survivalLABS（浅克隆 987K） | Mizuno 16x 的 labPBR 1.3 版 |
| `Textureless-LabPbr-32x-v115.zip` | Null-MC/Textureless Release | **CC0**，labPBR 规范实现参考（完整仓库 204M 克隆失败，改用 Release 成品） |

> `Null-MC/Oversized` 仓库 5 GB，未下载。
