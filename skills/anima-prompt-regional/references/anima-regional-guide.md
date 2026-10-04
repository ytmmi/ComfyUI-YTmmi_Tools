# Anima 分区与局部重绘参考（Regional / Inpaint）

## 1. 两个形态的本质区别

| | Regional LLLite | Inpaint / repair |
|---|---|---|
| 目标 | 在**同一张图**的不同空间位置放**不同主体/风格** | 只改**一小块**，其余像素保持 |
| 控制方式 | 颜色遮罩分区，每区一份提示词 | 遮罩区域内重绘，区域外不动 |
| 提示词结构 | `Global` + 每区一块 + `Negative` | `Whole image context` + `Masked area prompt` + `Negative` |
| 最大风险 | 区域串味、主体合并 | 接缝、画风/光照不匹配 |
| 专属负面 | `wrong region, object bleeding into other region, merged characters` | `visible mask edge, patchy repair, mismatched lighting/style` |

## 2. 区域颜色约定（社区常用，非标准）

| 颜色 | 常用用途 |
|---|---|
| 红 | 主角 / 主要焦点 |
| 蓝 | 次要角色 / 对手 |
| 绿 | 背景 / 环境 |
| 黄 | 文字、标题、前景道具 |

> 颜色只是**遮罩标签**。如果用户真的要红色衣服，必须在区域块里**另外写明** `red cape`——
> 不能靠遮罩颜色"顺便"上色。

## 3. 区域块写作规则

1. **一句一区域，自包含**：主体 + 外观 + 朝向 + 空间位置，不引用其它区域。
2. **必须有空间词**：`left side` / `right side` / `foreground` / `middle ground` / `background` /
   `upper band` / `center-left` / `slightly higher`。
3. **层级要写清**：`occupies the foreground center-left`、`one layer further back`。
4. **禁止备选表述**：不写 `or` / `maybe` / `could be`。
5. **区域数量**：3~5 区最稳；超过 5 区会互相挤压，建议拆成多张图。
6. **规模差异**：区域大小差异大时，大区域写整体气质，小区域写具体物件或细节。

## 4. 分区失败模式与对策

| 现象 | 原因 | 对策 |
|---|---|---|
| 两个区域的人物融合 | 缺空间词 / 缺合并负面 | 每区加左/右/前后；负面加 `merged characters, duplicated character` |
| 主体跑到错误区域 | 区域描述太泛 | 区域块开头就写空间词；负面加 `wrong region` |
| 物件跨区渗色 | 该物件在两区都被描述 | 只在一个区域描述该物件；负面加 `object bleeding into other region` |
| 某一区整体消失 | 该区描述过短 / 被其它区压制 | 补足该区描述；必要时提高该区主体权重 `(subject:2)` |
| 全局风格被某个区域带偏 | 区域块里混入了风格词 | 风格只写在 `Global prompt` |

## 5. Inpaint 块模板

```text
Whole image context
<媒介与画风：anime illustration, clean lineart, soft cel shading>, <角色身份与服装配色>,
<光照方向与质量>, <背景类型>, 以上保持不变。

Masked area prompt
<该局部完成后的样子：解剖正确性 + 材质 + 配色 + 与接缝的过渡>

Negative prompt
visible mask edge, patchy repair, mismatched lighting, mismatched style, mismatched lineart,
bad anatomy, bad hands, extra fingers, missing fingers, fused fingers, deformed fingers, messy lineart
```

### 常用局部目标写法

| 修复目标 | `Masked area prompt` 写法要点 |
|---|---|
| 手 | `a natural five-finger human hand with correct anime anatomy, slender fingers, clean knuckles, matching skin tone, matching cel-shaded highlights` + 袖口与手腕自然衔接 |
| 脸 | `clean facial proportions, symmetrical anime eyes, consistent eye colour, matching lineart weight, natural expression` |
| 衣服 | `the same garment design in matching fabric colour and folds, shading consistent with the existing cel shading` |
| 背景补全 | `background continuation in the same palette, same line density and same depth of field as the surrounding area` |
| 去物件 | **不要写 remove**；改写该位置应有的内容：`an unobstructed section of wooden floorboard with matching perspective and shadows` |
| 加物件 | `a correctly lit, correctly scaled <object>, grounded by a soft contact shadow, matching the scene's cel-shaded look` |

> **通用铁律**：局部重绘提示词描述**结果**，不描述**过程**。写 `remove` / `fix` / `repair`
> 会让模型把"修复工具/动作"当成内容画出来。

## 6. 组合流程（进阶：先分区再细化）

1. Regional 出一张分区构图；
2. 从结果里框出不满意的小区域；
3. 用 Inpaint 块做局部重绘，`Whole image context` 直接抄 Regional 的 `Global prompt` 内容，
   保证风格与光照不漂。

## 7. 交付前清单

- [ ] Regional：每区都有空间词与层级词
- [ ] Regional：`Global prompt` 只含全局项（质量、风格、光照、色调）
- [ ] Regional：区域块之间零交叉引用
- [ ] Inpaint：`Masked area prompt` 是"目标成品"而非"编辑动作"
- [ ] Inpaint：`Whole image context` 含画风 + 光照方向
- [ ] 负面含该形态的专属项
- [ ] 提示词里没有被塞进分辨率 / 遮罩尺寸 / 重绘强度 / 步数 / 采样器

## 8. 来源

- 社区提示词工程参考（分区 / 局部重绘块模板与负面表）：<https://github.com/AI-KSK/anima-prompt-crafter-skill>
- 模型卡（Anima 基础规则与约束）：<https://huggingface.co/circlestone-labs/Anima>
