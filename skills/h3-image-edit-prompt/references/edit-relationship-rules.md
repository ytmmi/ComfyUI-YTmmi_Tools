# H3-Image 编辑提示词：关系句与判定细则

配套 `h3-image-edit-prompt`。正文讲流程，本文件是**判断依据与可替换句式**。

## 一、四种关系句（官方定义）

| 关系 | 官方写法 | 何时用 | 常见误用 |
| --- | --- | --- | --- |
| 完全保留 | 单独一句 `<Subject N> is fully preserved.` | 该 Subject 全部范围（数量、位置、状态、外观、角色）都不变 | 只写「保持不变」而不编号，模型找不到对象 |
| 部分保留 | 自然语言说明「保留了哪些类别、改了什么」 | 只改颜色 / 位置 / 尺度 / 状态中的一项或几项 | 只写「稍微改一下」，保留范围不清 |
| 属性迁移 | `<Subject 2> supplies the exact body color transferred to <Subject 1>.` | 只借一个属性（颜色、材质、纹理） | 把属性捐赠者也写成「部分保留」，导致形状被一起搬过来 |
| 弱参考 | `<Subject 2> serves as a weak style reference for …, with freely adapted forms.` | 借气质 / 风格，允许形体自由发挥 | 写「参考图 2 的风格」而不说明可以自由改编到什么程度 |

## 二、什么算「改动」

官方的口径很硬，以下都**不是**保留：

- 移动、旋转、复制（副本本身是新出现的内容）；
- 重新打光、改变阴影方向；
- 被遮挡（新增前景物体压住它）；
- 尺寸变化导致取景改变。

推论：

1. **完全保留的父项里不能有被编辑的子项**——要么把范围拆细，要么降级为「部分保留」。
2. 新产生的**影子与反射**算作它们影响到的范围的改动，要给对应 Subject 标注。
3. 只把物体放大 1.5 倍不会改变画布比例；但**加宽画布**会（宽不变高不变时比例 ×1.5）。

## 三、画布与取景的判定顺序

1. 用户给了明确尺寸 / 裁剪 → 照用。
2. 没给，但构图保留 → 用**被编辑底图**的画布。
3. 需要参考图决定构图时 → 用「底图或指定的构图参考」，
   **不要用「只给颜色 / 只给材质」的参考图**来决定取景。
4. 分格数与画面里的屏幕尺寸**不是**整张画布的比例。

## 四、文字与数据的处理

- 每处文字 / 数据在定义段**逐行转录一次**（含将被改写的原文），保留语言、标点、大小写与行序。
- 看不清就写「无法辨认」，**不要猜**；也不要因为看不清就删掉。
- 改动时给**完整结果行**（不是只给替换词）；翻译给实际译文。
- 需要你写文案时，当场写出实际措辞（用户语言，或需求指定语言）。
- 只有**打算出现在画面里**的文字才写成字面文案；其它文字要说明它不在画面里。

## 五、句式模板（可直接改词）

```text
The <object> at <position> in <Picture 1> is <Subject 1>. The <object> in <Picture 2> is <Subject 2>.
The target image shows <principal result>. <Subject 1> is partially preserved; its <shape, material,
position, scale> remain while <what changes>. <Subject 2> supplies the exact <property> transferred
to <Subject 1>. <Subject 3> is fully preserved. <description of the completed change, including
contact, light and the surface that fills a removed area>.
```

多轮编辑时加一句范围声明：

```text
This round changes only <the named region or property> in <Picture 1>; <the other subjects> and the
canvas stay as they are.
```

## 六、与文生图的差别

| 维度 | 文生图 | 编辑 |
| --- | --- | --- |
| 正文结构 | 一段或多段自由描述 | **一段**，固定三段顺序 |
| 编号 | 无 | `<Picture N>` + `<Subject N>`，全文稳定 |
| 保留声明 | 不需要 | 每个 Subject 必须有关系句 |
| 画布 | 由版面决定 | 由底图 / 构图参考决定 |
| 文字 | 逐字加引号 | 逐字加引号 + 定义段逐行转录 |

## 七、出处

- 官方编辑指南：`MiniMax-AI/MiniMax-H3-Image` → `skills/h3-image-prompt-writing/references/edit-en.txt`。
- 官方 Prompting Tips 与 Sizes：同仓库 `README.md`（Prompting Tips / Request Parameters / Sizes）。
- 平台文档：<https://platform.minimax.io/docs/guides/image-generation.md>（编辑端点、参考图限制：
  JPG/PNG/WebP/HEIC/HEIF，单文件 ≤ 64 MiB，边长 128–8192 px，长边比 ≤ 4:1，1–16 张）。
- ComfyUI 教程：<https://docs.comfy.org/tutorials/image/minimax/minimax-h3-image>（编辑模板、`<Picture 1>` 约定）。
- 许可证：MiniMax-H3-Image Community License Agreement。
