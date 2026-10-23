> **License**: 本文档受 MIT License 保护 (Copyright (c) 2026 92609882-UX|渐行渐远)。
> 注: 包含图片/贴图素材的部分受上游 mod (MPL-2.0, © heyitsfuzs) 约束, 详见根目录 LICENSE。

# Enchanting Infuser PBR 材质包 v2.0

基于 LabPBR 1.3 标准 (Iris) 的 128px PBR 资源包。
适用: EnchantingInfuser v21.1.4 (1.21.1 NeoForge) + Iris + 支持 LabPBR 的着色器
(推荐 Complementary Reimagined / BSL — 两者 POM 视差与 LabPBR 通道支持最完整)

## 文件清单 (G:\PBR\)

- `EnchantingInfuser-PBR-128x.zip` — 最终安装包 (v2.0, 已含 POM 视差强化)
- `EnchantingInfuser-PBR-128x\` — 解包版
- `README-PBR.md` — 本文档
- `work\` — 生产流水线 (gen_pbr_v2.py 视差版 / gen_pbr2.py 标准版 / pom_preview.py 视差预览器)
- `work\out_v2\*_pom.png` — POM 视差预渲染图 (不开游戏直接看视差效果)

## v2.0 与 v1 区别

| 项目 | v1 | v2 |
|---|---|---|
| 高度图来源 | 灰度 Levels 压缩 | **分区平台高度** (金 0.98 / 红毯 0.72 / 紫石 0.85 / 黑曜石 0.62 / 符纹 0.30 / 铁 0.92) |
| AO 尺度 | depth=0.03 (过浅) | depth=0.15 (匹配视差) |
| 视差标定 | H≈[132,255] 有效深度弱 | H≈[191,249] 分层明确, POM 预渲染验证有 11% 像素位移 |
| 法线 | R/G 127 死平 (bug) | R/G 82~172 真实凹凸 |

## 安装

1. 放入游戏 `resourcepacks/` (PCL: `F:\PCL\versions\材质包测试\resourcepacks\`)
2. 游戏内启用 `Enchanting Infuser PBR 128x`
3. Iris 设置: 按 O 选 `Complementary Reimagined`
   - **按 O → Shader Options → Parallax (视差) 深度建议 0.4~0.6, 仅近距 (≤4 格) 生效**
4. 无 Iris/shader 时 PBR 不渲染 — 必须搭配

## 视差 (POM) 说明

- LabPBR 视差 = `_n.png` 的 A 通道 (255=最高, 0=最深)
- v2 分区高度: 金框 250 / 紫石 217 / 红毯 184 / 黑曜石 158 / 符纹 77 (0-255)
- 视差在 shader 中按距离衰减, 最近处 (1-2 格) 最强 — 贴着方块看效果最明显
- `work/out_v2/*_pom.png` 为模拟 POM 采样渲染, 不经游戏即可查看

## 材质分区 (LabPBR 通道)

| 材质 | _s R 光滑 | _s G 金属 | _s B 孔隙/SSS | _s A 发光 | _n A 高度 |
|---|---|---|---|---|---|
| 金框 (金属金) | 215 | 231 | 0 | 255 | 0.98 |
| 红毯布 | 35 | 10 | 28 | 255 | 0.72 |
| 紫魔法石 (SSS) | 90 | 20 | 110 | 255 | 0.85 |
| 黑曜石底 | 205 | 10 | 0 | 255 | 0.62 |
| 符纹 (凹刻+微光) | 60 | 10 | 90 | 40 | 0.30 |
| 铁 (进阶版灰) | 190 | 235 | 0 | 255 | 0.92 |

## 复现/调参

```bash
# 重新生成 (V2 视差版)
python G:\PBR\work\gen_pbr_v2.py
# 渲染 POM 预览
python G:\PBR\work\pom_preview.py
# 调参入口: gen_pbr_v2.py 中 HEIGHT_LEVEL 表 (高度) / MAT 表 (材质通道)
```
