# 授权范围说明（License Scope）

> 项目根目录 `G:\PBR\LICENSE` 与本文档共同定义本项目代码/文档部分的授权；贴图部分遵守上游条款，见下文。

## 一、代码与文档 —— MIT License

**授权主体**：Copyright (c) 2026 渐行渐远

**覆盖范围**（MIT）：

| 类别 | 内容 |
|---|---|
| 代码 | `work\` 下全部 `*.py` 脚本（生成器 gen_masks / gen_pbr / gen_pbr_v2 / gen_pbr_v3 / gen_projecte_* / pom_preview / enhance_enchanting_fabric_v6 / 验证脚本等，共 25 个） |
| 文档 | 全部 `*.md`：WORKLOG / PBR材质包制作经验与流程规范 / README 系列 / ProjectE 说明 / 目录说明等 |

按 MIT 条款：可自由使用、复制、修改、出售、分发，但必须保留版权与许可声明（即本授权）。

## 二、贴图与材质 —— 受上游约束（不属于 MIT）

**警告**：本项目的 `_n.png` / `_s.png` / 预览图是 **Enchanting Infuser mod 官方贴图的衍生作品**，上游条款为：

- 代码许可：**Mozilla Public License 2.0**（jar 内 LICENSE.md）
- 素材许可：**Copyright © 2023-2025 @heyitsfuzs. All Rights Reserved.**（jar 内 LICENSE-ASSETS.md——保留一切版权，未授予再分发许可）

因此贴图部分**不能**以 MIT 名义重新授权或公开分发（除非获得 Fuzs 的书面许可，或明确向用户说明适用 MPL-2.0 + 版权保留）。

## 三、分包建议

如果日后把本项目拆开发布：

- `scripts/` + 文档 → 可整体作为 MIT 项目发布（本 LICENSE 足够）
- `EnchantingInfuser-PBR-*.zip`（含贴图）→ 应标注："材质贴图衍生自 Enchanting Infuser (MPL-2.0, © heyitsfuzs)"，且不宣称 MIT；个人使用不受限

## 四、第三方参考

- GitHub 上查阅过的 `frugbug/labpbr-substance-tools`（MIT）、`jasonjgardner/substance3d_minecraft`（MIT）等仓库**仅作参考，未复制其代码**，不构成衍生，不受其许可约束。
