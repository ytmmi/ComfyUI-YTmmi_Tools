# Anima 权重语法与触发词参考

## 1. 权重语法

Anima 使用与 SDXL 相同的括号语法，但**需要的数值更高**（官方示例：`(chibi:2)`）。

| 写法 | 含义 | 建议用途 |
|---|---|---|
| `tag` | 权重 1.0 | 默认，绝大多数标签都用这个 |
| `(tag:1.3)` | 轻微强调 | 想让某个特征"更明显一点" |
| `(tag:1.5)` | 明显强调 | 主体身份、关键风格 |
| `(tag:1.8)` ~ `(tag:2.0)` | 强强调 | 多 LoRA 里要压过其它 LoRA 的那一路（官方示例级别） |
| `(tag:2.2)` ~ `(tag:2.6)` | 很强 | 谨慎使用，容易过曝 / 变形 / 变成贴图 |
| `(tag:0.6)` | 减弱 | 想保留但弱化某个标签 |
| `[tag]` | 减权（等价于 `:0.9` 左右） | 非精确减权；要精确就用 `(tag:0.8)` |

### 使用原则

1. **默认不加权重**。只对确实需要压过其它因素的一两个标签加。
2. **加权的标签数量控制在 1~3 个**。满屏括号等于没有权重。
3. **权重与标签数量互相影响**：标签越少，每个标签的权重影响力越大。
4. **不要用权重替代描述**：`(beautiful:2)` 这种空泛加权几乎无效，不如写具体特征。
5. 权重对**自然语言区也有效**，但优先级低于标签区；跨区加权很难精确控制，尽量避免。

## 2. 触发词摆放位置

```text
[质量/元信息/安全标签]
[人数标签]
[角色 LoRA 触发词]
[角色名] [作品名]
[画师标签 @artist]
[风格 LoRA 触发词] [风格/媒介标签]
[通用标签]
. [自然语言描述]
```

| LoRA 类型 | 位置 | 注意 |
|---|---|---|
| 角色身份 | 人数标签之后、角色名前 | 触发词紧贴角色名，帮助归位 |
| 服装 / 道具 | 角色名之后、通用标签区 | 与角色触发词分开写，避免身份漂移 |
| 视觉风格 | 质量标签之后、通用标签之前 | 同时写少量风格词（`watercolor, paper texture`）帮助落位 |
| 背景 / 场景 | 通用标签区 | 权重通常不需要加 |
| 姿势 / 构图 | 通用标签区前部 | 容易与角色 LoRA 的固有姿势打架，必要时降权角色 LoRA |

## 3. 多 LoRA 组合配方

### 3.1 角色 + 风格（最常见）

```text
1girl, solo, <char_trigger>, <Character Name>, <hair/eyes/outfit tags>, (<style_trigger>:1.6), <style words>. 
The character trigger defines identity and outfit; the style trigger defines rendering, line weight and palette.
```

### 3.2 双角色（各有自己的角色 LoRA）

```text
2girls, <char_a_trigger>, <A's appearance tags>, <char_b_trigger>, <B's appearance tags>, …
A stands on the left with …, B stands on the right with …, clearly separated figures with distinct outfits.
```

负面加 `merged characters, duplicated character, character fusion`。

### 3.3 风格 + 风格（刻意混风格）

```text
(<style_a_trigger>:1.4), (<style_b_trigger>:1.4), blended rendering …
```
两个风格权重接近时会"互相妥协"成混合体；想让其中一个主导，比例用 1.6 : 1.2 左右，
不要用 2.5 : 0.5（后者等于只用前者）。

### 3.4 触发词与画师标签并存

触发词负责身份/渲染，画师标签负责审美倾向。二者可以并存，但**不要同时**用三个以上画师标签 +
两个风格触发词——模型会失控。且负面里必须删掉 `artist name`。

## 4. 排障表

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 加了权重但没变化 | 权重太低（SDXL 习惯值） | 提到 1.5~2.0 再试 |
| 画面过曝 / 变贴图 | 权重过高或加权标签过多 | 降回 ≤1.6，减少加权标签数量 |
| 角色身份漂移 | 触发词离角色名太远 / 被风格标签压过 | 触发词移到角色名前，风格权重降到 1.4 以下 |
| 风格没生效 | 风格触发词位置太靠后 / 被大量通用标签淹没 | 前移到风格标签区，减少同义通用标签 |
| 两个 LoRA 都不生效 | 触发词写错（大小写/下划线被"规范化"） | 逐字照抄用户给的触发词 |
| 画师风格被压掉 | 负面里有 `artist name` | 从负面删除 `artist name` |
| 姿势锁死、不会变 | 角色 LoRA 强度过高 | 角色 LoRA 强度降到 0.7 左右，或降低其触发词权重 |
| 出现莫名其妙的服装/道具 | 服装 LoRA 触发词被放在了角色身份位置 | 触发词位置按第 2 节表重排 |

## 5. 训练相关提醒（用户问到才说）

- **不要训练 LLM adapter**：`llm_adapter_lr=0`。adapter 在文本嵌入送入扩散模型之前工作，
  影响力过大且极易训坏；`diffusion-pipe` 示例配置默认已关闭。
- **学习率要低**：rank 32 的 LoRA 从 `2e-5` 起调。
- Anima-Base 是真正的基座（没有激进的美学调优 / RLHF 需要对抗），轻推即可。
- 模型本身已内置极多视觉概念，LoRA 只需要"轻触"。

## 6. 来源

- 模型卡（权重语法、训练建议、LoRA 说明）：<https://huggingface.co/circlestone-labs/Anima>
- 社区工作流参考（双 LoRA 质量前缀与强度实践）：<https://github.com/ShiroEirin/comfyui-good-anima>
