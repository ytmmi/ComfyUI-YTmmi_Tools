# Z-Image 文字与版式参考

配套 `z-image-bilingual-text`。前三节是可替换词槽，第四节是版式模板。

## 一、字体气质写法（不要写字体名）

| 想要的感觉 | 写成 | 别写 |
| --- | --- | --- |
| 黑体 / 现代 | `heavy geometric sans-serif with tight spacing, flat terminals` | `思源黑体` / `Helvetica` |
| 宋体 / 印刷 | `high-contrast Ming-style serif with fine hairline strokes` | `宋体` |
| 楷体 / 手写 | `brush-style 楷体 with visible dry-brush edges and uneven pressure` | `楷体` |
| 复古招牌 | `chipped enamel lettering on painted metal, slight bevel` | `复古风` |
| 霓虹 | `thin bent neon tube, warm pink core with a soft halo` | `霓虹灯字` |
| 烫金 | `embossed gold foil on matte black card, hard specular edge` | `烫金` |
| 手写便签 | `uneven ballpoint scrawl on lined paper, slight ink bleed` | `手写体` |
| 粗描边标题 | `outlined display face, 3 mm stroke, offset drop shadow` | `描边字` |

## 二、字数可靠性阶梯

| 文字量 | 可靠性 | 建议 |
| --- | --- | --- |
| 中文 1–6 字 / 英文 1–3 词 | 高 | 主标首选 |
| 中文 7–10 字 / 英文 4–6 词 | 中 | 拆成两行，或降为副标 |
| 中文 11–20 字 | 偏低 | 分层（主标 + 副标 + 小字），多抽几张 |
| 多段落正文 | 低 | 不要用图像模型排版正文；用设计工具 |

## 三、中英对照模板

```text
<Chinese title in quotes> is set in <font character>, <ink/material>, centered <position>,
at <height ratio>. Directly beneath it, <English title in quotes> appears in <font character>
at about <ratio> of the Chinese title's height, aligned <alignment>.
<Additional licensed line in quotes> sits <position> at <size relation>.
No other text appears in the frame.
```

双语三条铁律：

1. 一种语言做主标，另一种做副标，**字号必须有明显差异**；
2. 两种语言**各自成行**，中间用分隔线或留白；
3. 双语内容必须**一一对应**，不要让模型自己翻译。

## 四、版式模板

### A. 竖版海报（上图上字）

```text
上 2/3：主视觉图像（给三个层次：前景 / 主体 / 远景）
下 1/3：底色纯色区，主标居中 → 英文副标 → 底部小字（时间 / 地点）
分隔：一条细横线
收束：除上述文字外无其他文字
```

### B. 方版包装标签

```text
外框：<材质> 圆角矩形，边距均匀
顶部：品牌名（中文主标）
中部：产品图（居中）+ 一句英文品类名
下部：规格 / 重量 / 小字说明
角标：一个圆形印章式图形（可选）
```

### C. 横版书封 / 展板

```text
左侧 40%：主标（竖排中文，从上到下）+ 英文副标横排
右侧 60%：图像或大面积留白
底边：作者 / 日期小字
```

### D. 菜单 / 价目表

```text
顶部：店名（中文主标 + 英文副标）
主体：2–3 列条目，每行「菜名 + 价格」，中文名 + 英文名上下排
底部：营业时间
收束：不添加未给出的菜品或价格
```

> ⚠ 菜单 / 价格 / 规格类：**只写用户给的真实内容**，示例数据必须标明是示例，
> 不要把编造的数字当成真实信息画进图里。

## 五、出处

- 双语文字渲染能力：官方 README 的 Showcase「Accurate Bilingual Text Rendering」与
  ComfyUI 教程「准确的双语文字渲染」（<https://docs.comfy.org/tutorials/image/z-image/z-image>）。
- 变体差异（Turbo 8 步无 CFG / Base 30–50 步 CFG 3–5、多样性差异）见
  `z-image-prompt-writing/references/z-image-official-guidelines.md`。
- 官方仓库：<https://github.com/Tongyi-MAI/Z-Image>。
