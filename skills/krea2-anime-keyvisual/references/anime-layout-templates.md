# 二次元主视觉 / 分镜版式参考

配套 `krea2-anime-keyvisual`。

## 一、主视觉版式（竖版）

| 区带 | 占比 | 内容 | 注意 |
| --- | --- | --- | --- |
| 标题带 | 上 22–28% | 低细节天空 / 纯色 / 虚化 | 角色不要压进来 |
| 主体带 | 中 40–50% | 角色上半身 + 最强对比 | 脸在中线偏上 |
| 叙事带 | 下 25–30% | 道具 / 动作结果 / 环境 | 压饱和，别抢戏 |
| 底边 | 3–6% | 日期 / 小字 | 一行以内 |

横版换成「左 1/3 标题竖条 + 右 2/3 主体」。

## 二、漫画格位模板

**四格**：`2 rows and 2 columns` —— 起 / 承 / 转 / 合。
**条漫**：`4 rows and 1 column` —— 竖向阅读，每格高度递进。
**单页日漫**：`3 rows and 2 columns` + 一格跨两列做高潮。
**跨页**：`1 row and 2 columns`，中间留装订沟。

每格必写：景别 / 主体 / 动作 / 背景一层 / 有无气泡。

## 三、气泡与拟声词写法

```text
a rounded speech bubble in the upper right of the panel reading "你迟到了";
a jagged burst bubble in the lower left reading "砰";
a small caption box in the lower right reading "三天前".
```

规则：

- 气泡**不压在脸上**，指定「格内左上 / 右上 / 空白处」；
- 气泡形状说明语气（圆 = 正常，锯齿 = 喊叫，云 = 心之所想，方框 = 旁白）；
- 文本逐字加引号，保留原语言；
- 拟声词按画面文字处理，可写「粗体、带速度线」。

## 四、草图 → 成品检查

| 检查 | 说明 |
| --- | --- |
| 构图锚点 | 谁在哪、多大、朝哪、遮住什么——四件事写死 |
| 成品描述 | 只描述成品，不描述「草图」 |
| 参考上限 | 风格参考最多 4 张，草图和风格图不要混着塞满 |
| 画风锚句 | 只要一句（来自 `krea2-anime-style`） |

## 五、出处

- 草图转分镜流程、工作室画风牵引：Krea 官方博客《From sketch to anime panel with Krea 2》
  与《Studio anime aesthetics with Krea 2》（<https://www.krea.ai/blog>）。
- 文字与版式规则（加引号、留白、行列写法）：Krea 官方 `docs/prompting.md` / `docs/expansion.txt`，
  以及本仓库 `h3-image-prompt-writing` 的同类规则（行列、无文字声明）。
- 本文件为方法论整理，不含第三方原文或示例图。