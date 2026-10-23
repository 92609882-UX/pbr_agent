> **License**: 本文档受 MIT License 保护 (Copyright (c) 2026 92609882-UX|渐行渐远)。
> 注: 包含图片/贴图素材的部分受上游 mod (MPL-2.0, © heyitsfuzs) 约束, 详见根目录 LICENSE。

# Enchanting Infuser PBR v4

基于 v3 的细节修正版，适用于 Minecraft 1.21.1 NeoForge、Iris 与支持 LabPBR 的光影。

- 金属框、红毯、紫色核心、黑曜石底座和符文使用分层 POM 高度。
- 紫色魔法核心使用中等自发光，符文使用更强自发光，符文边缘保留弱辉光。
- AO 加强了符文凹槽和材质交界处，法线边界保持窄而清晰。
- 方块外轮廓和透明区已清理，避免视差越界与 mipmap 污染。

安装 `EnchantingInfuser-PBR-128x-v4.zip` 后，在 Complementary Reimagined 或 BSL 的 Shader Options 中启用 POM；建议视差深度从 0.5 开始。自发光强度由光影的 Bloom 设置决定。
