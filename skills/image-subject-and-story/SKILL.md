---
name: image-subject-and-story
description: Decide what an image is actually about and make that visible - the one subject that carries the message, the story beat frozen at the most legible instant, the props that imply before and after, and the composition of absence. Use when a render is pretty but says nothing, when a brief has several competing subjects, when a poster or editorial illustration needs a readable idea, or when the user asks for storytelling, narrative, conceptual or campaign imagery. Model-agnostic: story is carried by described evidence, not by adjectives.
version: 1.0.0
---

# 主题与叙事（Subject & Story）

一张好看的图不一定说得清一件事。**主题**是「这张图在说什么」，**叙事**是「画面里能看出发生了什么」。
两者都不靠形容词，靠**可见证据**：一个动作的后果、一件道具的状态、一个人与另一个人的距离。

本 skill 只管**主题与叙事**：选什么当主角、冻结在哪一刻、用什么道具暗示前后、如何用「缺席」叙事。
不碰取景（→ `image-composition`）、不碰光（→ `image-light-and-value`）、不碰情绪氛围（→ `image-mood-and-atmosphere`）。

## 何时使用

- 画面**漂亮但空**，看第二眼就没东西；
- brief 里有**三个都想当主角**的东西，画面平均用力；
- 海报 / 编辑插画 / 活动 KV 需要**一个读得懂的 idea**；
- 用户要「讲故事」「有叙事感」「概念图」；
- 需要表达**时间**（刚发生 / 即将发生）；
- 群像需要**关系**，而不是一排人各摆各的姿势。

## 输出契约

- **只输出提示词正文 / 主题方案**；要方案时用短条目：`主题 / 瞬间 / 证据 / 缺席` 各一行；
- 默认只出正面提示词；用户要负面词时才追加两段式；
- 不写参数；不写 `storytelling` / `emotional` / `dramatic` 这类词当作叙事本身；
- 用户指定的主体与情节**原样保留**，只补空缺与证据。

## 第一步：一句话说清主题

动笔前先在内部完成这一句（**不要输出**）：

> **「这张图在说：______」**

如果填不出来，说明还没决定。常见可用的主题类型：

| 类型 | 例子 | 需要的可见证据 |
| --- | --- | --- |
| 等待 | 雨夜门口等人 | 湿掉的伞、反复看的手机、被雨打湿的裤脚 |
| 离开 | 收拾到一半的房间 | 空衣架、打开的门、留在桌上的钥匙 |
| 被淹没 | 加班的桌子 | 三只空杯、凌晨的钟、窗外全暗 |
| 克制 | 两个人隔着一段距离 | 视线方向、手没有碰到、脚尖朝外 |
| 秩序 | 极简依旧整齐 | 对齐的边缘、唯一的例外物 |

## 第二步：冻结在最可读的一刻

**不要描述过程，描述一个瞬间**——而且是最能说明前后因果的那一瞬：

| 太早 | 太晚 | 刚好 |
| --- | --- | --- |
| 手伸向杯子 | 杯子已经空了 | **指尖刚碰到杯沿，杯里的水面还在晃** |
| 准备推门 | 门已经关上 | **门缝还在动，他的影子正从光里退出** |
| 起跑 | 冲过终点 | **脚刚离地，尘土还在原地打转** |

写法要点：**一个动作 + 一个还在变化的后果**。

## 第三步：道具承担时间

道具是「前因后果」的载体。每件被写进画面的道具都应该回答一个问题：

- **刚发生过什么**：还冒热气的杯子、翻倒的椅子、没挂断的电话；
- **即将发生什么**：放在门口未拉开的行李箱、已经写好的信没有寄出；
- **谁在这里**：外套挂在椅背、眼镜放在书页上；
- **持续了多久**：桌面磨白的一块、墙上被反复抚摸的漆。

**规则**：一件道具只承担一件事。道具越多，叙事越散。

## 第四步：用「缺席」叙事（最省力、最高级）

画面里**没有出现的东西**往往比出现的更有力：

- 空椅子 + 两副餐具 → 少了一个人；
- 桌上两个杯子只有一个有水 → 刚离开；
- 门口一双鞋、另一双不见了 → 别离；
- 相框背面朝下 → 不愿看。

写法：直接描述**缺席的痕迹**，不要写「暗示某人不在」这种解释性句子。

## 多人：写关系，不写排队

群像失败的根本原因是**每人各摆一个姿势却没有关系**。必须写：

1. **谁对谁做什么**（视线 / 触碰 / 递物 / 背对）；
2. **谁在回应**（表情、身体转向、后退一步）；
3. **空间关系**（谁在前、谁挡住谁、谁离得远）；
4. **一个共同的焦点**（同一件东西、同一个方向）。

## 常见失败与修法

| 症状 | 根因 | 修法 |
| --- | --- | --- |
| 漂亮但空 | 没有主题句 | 先写「这张图在说 ___」 |
| 主角不明确 | 三个主体等权 | 只留一个主角，其余降为配角或环境 |
| 看得出场景但看不懂发生什么 | 只有状态没有后果 | 补「一个动作 + 一个还在变化的后果」 |
| 道具杂乱 | 每件都想说话 | 一件道具只承担一件事 |
| 群像无关系 | 各摆各的 | 写谁对谁做什么、谁在回应 |
| 写了 `storytelling` 没用 | 用形容词代替证据 | 换成可见道具状态与动作后果 |
| 情绪靠 `sad` 撑 | 情绪没有载体 | 用缺席、距离、未完成的事表达 |

## 自检清单

- [ ] 内部有一句「这张图在说 ___」，且不含形容词；
- [ ] 主角唯一，其余是配角或环境；
- [ ] 冻结在一个瞬间，且有一处「还在变化的后果」；
- [ ] 每件道具只承担一件事，并指向过去或未来；
- [ ] 至少考虑过用「缺席」表达；
- [ ] 多人时有明确关系与共同焦点；
- [ ] 没有用 `storytelling` / `emotional` / `dramatic` 代替证据；
- [ ] 只有最终正文，没有解释。

## 示例

**输入**：「一个加班到深夜的人，要孤独但体面」

```text
A wide interior at three in the morning: a small office desk lamp is the only light left on, and
the rest of the floor has gone dark. A woman in a pressed white shirt sits at the desk but has
stopped working; her chair is turned a quarter away from the screen, one hand still resting on
the keyboard while she looks toward the black window beside her. Three empty cups are stacked at
the corner of the desk, the top one with a dried ring inside, and a fourth, half full and long
cold, sits untouched by her elbow. Her coat is already on the back of the chair, the strap of her
bag looped over it, and the desk calendar beside the monitor has been marked through for today
only. The screen has gone to a screensaver, its pale rectangle the only bright shape in the
frame and the only thing not facing her. Everything else in the room is evenly low-contrast and
still, the far cubicles readable only as soft grey blocks.
```

## 依据

- 单帧叙事（single-frame narrative）：一张照片能承载完整故事，靠的是**可读的瞬间**而非系列铺垫，
  见 Magnum《Telling Stories: the Single Image vs. the Series》、W. Scott Olsen《Single Frame
  Narrative Photography》。
- 用「缺席 / 负空间」表达不在场：关于 negative space 作为「absence」符号工具的符号学分析研究。
- 「只出现在转折点前后、把真正发生的事留给画面之外」的省略式叙事：影像叙事研究。
- 以关系而非队列写多人：影视与纪实摄影的群像调度常规。

## 边界

- 不执行脚本、不生成图片、不调 API。
- 不写参数；不用形容词代替可见证据。
- 不替用户编造真实事件、真实人物或真实数据。
- 不复制具体作品的画面与情节。