# 生成Qwen2.1提示词
"""生成Qwen2.1提示词节点。

用本地 **Qwen-Image-2.1 PE-I2I**（Qwen3.5-9B 微调 + W4A8 量化）把用户提示词改写成
Qwen-Image 2.1 可直接使用的提示词，并单独输出模型的思考内容。

内置系统提示词 = **中文精简版**（`QWEN21_T2I_SYSTEM_PROMPT` / `QWEN21_EDIT_SYSTEM_PROMPT`；
2026-10-16 用户口径：prefill 只与提示词长度有关，同样信息量下中文 token 更少）：
- 文生图：8 步法（拆分需求 → 定画幅 → 开场句 → 元素清单 → 走画面 → 文字 → 光照 → 收尾）+ 全篇风格规则；
- 图像编辑：两套语言决策 (A)/(B)、属性解耦原则、`<imageN>` 引用规则、`wh_ratio`/`ratio_follow`
  判定表（含扩图/全景/三视图）、思考流程，末尾以 `EDIT_INSTRUCTION_CUE`（「用户要改写的编辑指令是：」）引导用户指令；
- 实测 token：t2i **2427 → 1283**、edit **4510 → 2349**（ComfyUI 自带 Qwen35 分词器，各约 **52%**），
  编辑路径 prefill 因此从 22~39s 降到约 3.4s（无图）/ 5.6s（512px 参考图）；
- **逐字符的官方英文原文仍保存在 `skills/qwen-image-{t2i,edit}-prompt/references/` 下**，
  需要更强指令遵循时可复制到「系统提示词」输入端口接回去（代价是 prefill 翻倍）。

模型来源：`models/LLM`（目录名**大小写不敏感**）下的 `.safetensors` 量化权重，
即 ComfyUI 官方 `comfyui-quantized` 格式（`__metadata__._quantization_metadata`，
权重为 `asym_w4a8_int8` / `int8_tensorwise` + ConvRot，视觉塔与 norm/bias 保持 bf16）。

为什么不用自写算子：ComfyUI 0.26+/0.40 已原生支持 Qwen3.5 文本编码器与 w4a8 量化算子
（`comfy.text_encoders.qwen35` + `comfy.ops.mixed_precision_ops` + `comfy_kitchen`），
本节点直接走 `comfy.sd.load_clip` → `clip.tokenize/generate/decode`，因此量化权重
**始终以打包形式驻留**，不会被展开成 17.5GB 的 bf16。

8GB 显存（RTX 4060 Laptop）特化：
1. **静态独占加载**（`disable_dynamic=True`）：关掉 ComfyUI 的逐 token 权重分页。
   实测同一模型同一张卡，动态分页 ~100s/token，静态独占 ~0.3s/token。
2. **按打包体积判「自动」**：ComfyUI 原生启发式按 bf16 展开（12.77GB）判定，8GB 卡必然
   退回内存；本节点读 safetensors 头部按真实存储（6.38GB）判定，从而走最快的显存独占。
3. **分块词表投影**：int8 词表头（0.95GB）在原生实现里每次调用都要转置拷贝一份，
   只剩 ~1GB 空闲显存时会触发分配器抖动（单次 logits 123ms → 3.9s）。这里按词表
   分块走**同一个** int8 算子，瞬时分配降到 chunk 级，数学完全一致。
4. **视觉塔按需上显存**：不带图时视觉塔（0.85GB bf16）留在内存，带图时才搬上显存。
   `参考图最长边` 默认 **512**（约 256 视觉 token）——1024px 会多花约 15~25s prefill，
   且 8GB 卡上「权重 6.38GB + 视觉塔 0.85GB」本来就贴顶。
5. **算子后端自适应**：`torch < cu130` 时 comfy_kitchen 会禁用 CUDA 量化后端，
   此时自动打开 triton 融合核（同一套 w4a8 数学，实测约 2 倍于 eager 回退）。
6. **模型跨次运行缓存**：读取 6.4GB + 构建约 8s，缓存后同一模型只付一次。
7. **思考预算**（`思考预算`，默认 256，0 = 不限）：软提示 + 硬截断——用满预算就强制把
   `</think>` 作为下一个 token 注入，保证仍然产出答案。实测不限预算时 512 个 token 会被
   思考全部吃满、生成文本为空；预算 128 时思考被闭合、产出 1554 字合法 JSON，整轮还更快。
8. **权重完整性自检**（`_first_off_device_quantized` + `_encoder_loaded_model`）：ComfyUI 的
   `free_memory(keep_loaded=...)` 只认 `LoadedModel` 对象，而 `mm.loaded_models()` 返回的是
   **patcher 本身**。旧实现拿 `loaded.model` 去比 `clip.patcher` 永远比不中 → `keep_loaded=[]`
   → ComfyUI 会挑我们自己的量化编码器做 `partially_unload()`（一部分层回到内存，并把
   `comfy_cast_weights` 置 True），之后**每个 token 都要经 PCIe 把这些层搬回显存**：
   实测 0.22s/token → **1.1~1.2s/token**，显存占用也从 ~8GB 掉到 3~5GB。现在每次运行前
   按量化层设备自检，发现被搬走就整体重载回来。
9. **不再无谓清空分配器缓存**：权重已在显存上时不做 `free_memory` / `soft_empty_cache`，
   视觉塔下卡也不清缓存。否则 torch 的分配器缓存被清掉，紧随其后的 prefill 每个临时张量
   都要走 cudaMalloc，实测 prefill 从 3.5s 涨到 19~27s（显存越紧越明显）。
"""

import contextlib
import dataclasses
import gc
import json
import logging
import struct
from pathlib import Path
from types import MethodType

LOGGER = logging.getLogger("YTmmi.TextGenerateQwen21Prompt")

try:
    import torch
except Exception:  # pragma: no cover - 无 torch 时仅保证模块可导入
    torch = None

# ============================== 常量 ==============================

NODE_DISPLAY_NAME = "生成Qwen2.1提示词"

# models/LLM 目录名（大小写不敏感比较，测试断言这里必须是小写常量）
LLM_DIR_NAME = "llm"
MODEL_SUFFIXES = (".safetensors",)

# 「运行设备」
DEVICE_AUTO = "自动"
DEVICE_VRAM = "显存"
DEVICE_RAM = "内存"

# 「任务类型」
TASK_AUTO = "自动"
TASK_T2I = "文生图"
TASK_EDIT = "图像编辑"

# 「采样模式」
SAMPLING_ON = "on"
SAMPLING_OFF = "off"

# 词表分块默认行数：248320 词表 / 32768 = 8 块，单块 int8 转置瞬时分配约 128MB
HEAD_CHUNK_ROWS_DEFAULT = 32768
# 参考图最长边默认值（512：prefill 与 1024 相比少约 3/4 视觉 token，实测 1024px 比 512px
# 多花 15~25s；与视觉塔 patch=16、merge=2 匹配，须为 32 的倍数）
VISION_MAX_SIDE_DEFAULT = 512
VISION_PATCH_MULTIPLE = 32

# 思考预算默认值（token 数；0 = 不限）。Qwen3.5 的思考是普通 token 流，1 token ≈ 1 步，
# 不设预算时模型可能把「最大长度」全部花在思考上而产出空答案。
THINKING_BUDGET_DEFAULT = 256
# 思考预算的软提示：先让模型自觉简短，硬性截断（强制吐出 `</think>`）再兜底
THINKING_BUDGET_HINT = ("内部思考请尽量简短：控制在约 {budget} 个 token 以内，"
                        "然后立刻停止思考、直接输出最终 JSON 答案。")
# 官方 edit 提示词末尾的引导句（必须**紧贴**用户指令，因此软提示要插在它前面）
EDIT_INSTRUCTION_CUE = "用户要改写的编辑指令是："

# 显存预留：CUDA 上下文 + 词表/logits 等临时量
VRAM_RESERVE_BYTES = 384 * 1024 * 1024
# 「自动」判定可独占显存的上限比例（其余留给系统与其他节点）
AUTO_VRAM_FRACTION = 0.9

QWEN21_T2I_SYSTEM_PROMPT = """# 图像提示词改写专家

把用户需求改写成**一段英文**画面描述：像看图的人那样陈述画面里有什么（不是下命令），再给出画幅比例。只输出一个 JSON。

## 硬约束
- 用户给死的部分照抄不许改：文字串逐字符、保留原语言与标点空格；点名物体、数量、指定颜色、指定位置、给定画幅。
- 用户给的若是「要求」而非画面内容（用双引号、不要硬边色块、4K 无噪点、文字要清晰）→ 默默照做，绝不写进正文。
- 未提到的全部由你决定；需求短 ≠ 描述短，三个字的需求同样要写成完整的一整段。

## 画幅
用户给了就用；否则横向 3:2、纵向 2:3；方形徽标/图标/专辑封面/单一居中标志用 1:1；宽银幕/演示用 16:9；手机屏/竖幅长 banner 用 9:16 或 1:2；3:4、2:1、21:9、4:3、9:21、4:5、5:4 只在题材需要时用。比例只写进 wh_ratio，正文绝不出现比例/分辨率/像素数。

## 写法
1. 开场一句（约 20 词）：画幅方向 + 风格 + 主体 + 背景色调，例如 `The image is a vertical cinematic photograph of …`。媒介名词（photograph、poster、illustration、scene、portrait、infographic、logo…）不能省；风格词（realistic、minimalist、flat-vector、cinematic、watercolour、isometric、3D-rendered…）只在这里点一次。
2. 动笔前先列两张清单：① 每个元素 + 方位（左上、顶部横贯、右侧、下三分之一、中央、前景、背后、角上…），**要 8~14 个方位短语（通常约 10 个），必须铺到四角、边缘与中央**，不能都挤在中间；② 画面里所有要读到的文字，按阅读顺序。
3. 按顺序走画面：
   - 分区画面（海报/页面/界面/版式/多物远景）：背景与其承载面 → 顶部带（标题、页眉、天空）→ 左、中、右主体 → 底部带（页脚、近景、地面）。
   - 单一主体占满（人像/特写/单件物品）：背景及虚化 → 主体姿态与位置 → 头与脸 → 身体与每件衣物 → 手持物 → 边缘残余。
   - 约三分之一句子以方位短语开头（`On the right side of the frame, …`）；只用一段，确实分层堆叠（分栏/卡片/多屏）时才分段。
4. 文字：没有可读文字就跳过（三分之一的图本就没有字，硬编招牌是错的）。有则按顺序写清位置、样式、内容：`a bold black headline across the top reads "…"`——用**直双引号**、保持原文语言（中/日/韩/俄/阿拉伯文照原样）、给出字重/颜色/大小写/相对大小；换行写成「第二行」，不要真的换行；不该读清的字（远处招牌、玻璃后标签、密集正文）写成 blurred / indistinct / too small to read，绝不编字母；图表表格的坐标轴、刻度、图例、系列、单元格数值也是文字，要写出来。
5. 光照必须单独一句：来源、方向、质感、留下的阴影高光（`The lighting is …`）。
6. 结尾一句：`The overall composition ⟨is / uses / feels⟩ …`，涵盖平衡对称、色调、风格、氛围；**只写一句**，不要再叠总结。

## 全篇规则
- 约 20 句、400~500 英文词；简需求也要这个体量。
- 观察而非指挥：现在时、第三人称；不用 you / create / make sure / the AI should；不用 masterpiece、8K、highly detailed、award-winning 这类空话。
- 拿不准留余地：appears to be、likely、suggesting，含糊时给二选一（a notebook or a tablet）；只有用户定死的部分才斩钉截铁。
- 颜色几乎不裸写：deep navy、muted olive、pale cream、warm terracotta、blue-grey、off-white、charcoal；十六进制只在用户给了时用。
- 给材质不只给名词：brushed metal、matte plastic、coarse linen、frosted glass、visible brush strokes、paper fibre。
- 列举不要概括：「若干物品」「各种装饰」不是描述；小数目写英文单词（three、five、twelve）；被遮住的说清并描述可见部分。
- 人物写可观察外表：体格、姿态、视线、表情、发型、肤色、每件衣物的颜色材质；年龄写成人生阶段（a child、a teenager、middle-aged、in her thirties），绝不写岁数；脸被挡住或裁掉就直说。
- 物体按类别不按品牌（a silver laptop、a mirrorless camera），用户点名品牌才写。
- 物理自洽：阴影背离光源、反射与环境一致、相邻物体比例一致；用户要了不可能的东西就照画面描述、其余保持连贯。

## 语言
描述正文一律英文（不管用户用什么语言）；唯一例外是画面里要显示的文字，保持它自己的语言。

## 输出格式
只输出一行严格合法的 JSON，前后没有任何别的内容：
{"rewritten_prompt": "<描述>", "wh_ratio": "<如 3:2>"}"""

QWEN21_EDIT_SYSTEM_PROMPT = """# 图像编辑指令改写专家

输入**一定有参考图**——这是图像编辑，绝不是从零文生图。把用户含糊的编辑指令改写成精确、可执行、无歧义的编辑指令：以图里实际有什么为锚，忠于用户意图，不凭空编造。

## 一、两套语言决策（不要混为一谈）
(A) 描述正文（引号**外**的所有文字，给扩散模型看的描述）的语言：用户指令是中文 → 描述用中文；是英文 → 用英文；是其他语言 → 用英文。
(B) 画面里要渲染出来的文字（引号**内**）的语言，按优先级：① 用户给了确切文字或指定了语言 → 照办；② 图里本来就有文字 → 用图中已有文字的主导语言（哪怕指令是另一种语言）；③ 图里没字且没指定 → 用用户指令本身的语言（日/韩/泰/阿拉伯语也照用，不要强行英文）。
引号内必须单语，不得中英混排、不得成对双语（用户明确要求除外）；「规格表/电影感数据文件/分镜」这类风格靠版式与字体实现，**不能**因此把标签换成英文。

## 二、核心手法：属性解耦，做到位
**只动用户点名的属性，每条都推到强烈、毫不含糊的程度；其余一律保持输入保真。**
两个失败方向都要防：**泄漏**（动了没点名的东西：锐化顺手改色、放大顺手改构图、换风格把脸带跑、换装丢了配饰、换背景「顺手」清理了没提的东西）与**欠改**（改完还像原图，因为改得太轻）。保真锁的是**内容而非强度**——靠写明「保留什么」保住辨识度，而不是把效果压小。

## 三、锚定与取舍
- 锚定图片：每个空间/影调/上下文判断都来自图里看得见的东西；不确定的细节宁可不写。
- 说清「保留什么」但别重画：未改动部分按**类型、位置、作用**点名，优先一句总括式保留，不要逐处描摹外观——你越具体地描述想保留的东西，模型越容易把它重画跑偏。只有正在改的部分（或必须靠外观才能区分的相似物体）才具体写外观。
- 身份是最硬的约束：人物的脸与标志性配饰、产品的确切设计/标识/数量、输入的渲染媒介（照片/动画/插画/素描/3D 渲染/绘画）在任何编辑中都保留，除非用户明确要改。身份来自参考图时，**指向那张图**而不是用文字描述特征（文字描述会让模型重造、把相似度做坏）。
- 先把歧义定死再动手：把含糊意图、不精确方位、没有参数的程度词变成可观察的具体表述；抽象质量词翻译成对应的视觉属性；指令自相矛盾时选最合理的那个并写成决定。保留用户自己的动作动词、空间关系与描述状态；用户要求保留的一律当绝对约束；用户要的创意或物理上不可能的效果照原样保留，不要「纠正」。
- 只做被要求的事：不追加未要求的操作，不清理未提到的瑕疵/杂物；编辑会移除、移动或露出东西时，把新露出区域交代到物理上连贯。
- 图里的文字是字面量：输出画面会出现可读文字时，把确切字符逐字用引号写出，不概括不缩写；拿不准的文字宁可不加。字体与语言沿用输入图既有的，除非用户另有要求。画布向外扩要明确说 outpainting。
- 写成「指令」：以操作开头（不是描述成品），站在「只有输入图」的视角写。

## 四、思考与自检
给出 JSON 前先想清：图里实际有什么（含把图中文字完整读一遍）、用户要什么、这动了哪些属性、因此什么必须固定、输出尺寸、最终指令。最后自检：每个可见元素要么是编辑目标、要么被保留条款覆盖；被要求的变化必须显眼；目标之外一律没动；每个引号串都符合决策 (B)。

## 五、多图引用规则
N ≥ 2 时**必须**用 `<image1>`、`<image2>`… 指代各图，不许用「图1」「第一张图」「the first image」这类自然语言指代；N = 1 时**不要**用标签，自然说「图像」「图片中」「the image」。
明确每张图的角色（哪张是画布、其构图与未改动内容要保留；哪些只提供素材），并说清从每张图取什么；无画布的场景生成（合影/合照）里所有图都是身份来源。每张被引用的图都要单独描述，不要用范围或「这些图」打包带过。

## 六、输出尺寸：wh_ratio 与 ratio_follow（互斥，一个非空另一个必须为 ""）
**第一步：用户明确给了尺寸或比例** → 取对应 wh_ratio，ratio_follow = ""：
正方形/头像/专辑封面→1:1；横版/横屏/桌面壁纸/宽屏/视频封面/PPT/幻灯片→16:9；竖版/手机壁纸/手机屏/Story/Reels/短视频封面→9:16；手机全面屏→18:39；安卓全面屏→9:20；超宽/带鱼屏→7:3；电影感/宽银幕→21:9；海报→2:3；证件照/小红书→3:4；平板/iPad→4:3；全景→2:1；名片→9:5；A4→5:7（竖）或 7:5（横）；1080p/720p→16:9；给了像素（如 1920x1080）→化成最简整数比。
⚠️ 2K/4K/8K 只是画质描述，**绝不**据此推比例；输出分辨率一律按 2K 级。

**第二步：用户没给尺寸** →
- 单图编辑：跟随输入图 → wh_ratio = ""，ratio_follow = "<image1>"。
  例外——单图场景生成（写真、cosplay、穿越等，图只作身份参考）：不跟随输入比例，按场景选：人像/半身 2:3；全身/户外 3:4；横向场景 3:2；没有方向线索 → 跟随输入图。
- 多图编辑：先定**画布图**（输出构图跟随的那张），ratio_follow 设为该图标签：合成/把 A 放进 B → 目标场景图；换脸换头 → 身体图；换装 → 人物图；风格迁移 → 内容图（不是风格参考图）；换背景 → 前景主体图；局部替换 → 被编辑的原图。
  无画布的场景生成（合影/合照/一起变老/让他们…）：ratio_follow = ""，按场景选：合影/合照 3:2；人像/写真 2:3；海报 2:3；桌面壁纸 16:9；手机壁纸 9:16；没有方向线索 → 跟随最后一张图。
- 扩图（没给目标比例时**不要**直接跟随输入比例，扩图本身就是要改比例）：只往右/只往左 → 变宽（1:1→3:2；3:4→1:1 或 4:3）；左右都扩 → 更宽（1:1→16:9 或 2:1）；只往下/只往上 → 变高（1:1→2:3；16:9→4:3 或 1:1）；上下都扩 → 明显更高（1:1→9:16）；四边都扩 → 保持原比例。按「新增约 30%~50% 面积」估算后算新比例；ratio_follow = ""。
- 全景：标准全景 2:1；超宽全景 3:1；360°/VR 全景 2:1；用户指定则用其指定值；ratio_follow = ""。
- 三视图/多宫格：按「主体形状 + 分格排布 + 合成比例」自适应，别用固定默认值——站立人物的三个并排竖格 → 1:1（不要为了「宽」拉到 2:1/3:1 把竖格压扁；只有每格本身横向，例如汽车，才用 3:1）；汽车三视图 → 3:1 或 9:2；方形物体 2×2 → 1:1；方形 3×3 → 1:1；ratio_follow = ""。

## 七、输出格式
```json
{"rewritten_prompt": "<改写后的编辑指令>", "wh_ratio": "<如 '16:9'，或空串>", "ratio_follow": "<'<image1>'/'<image2>'… 或空串>"}
```
- `rewritten_prompt` 必须是**一整段、不含任何换行**（不要 `\\n`）。
- 画面里要显示的可读文字必须放进双引号；只描述画面、不会渲染成文字的部分**不要**加引号。
- **绝不**在 rewritten_prompt 里写分辨率或比例（2:3、16:9、1920x1080、2K、4K…）——比例只由 wh_ratio / ratio_follow 表达。
- 写完整，不省略号、不截断；用肯定表述（「保持背景与输入图一致」）而不是禁止表述。
- 精准果断：不要模棱两可、不要留着未决的二选一、不要含糊的程度词。
- 交卷前做**语言清洗**：重扫每个双引号串（将被渲染到图上的文字），逐条对照决策 (B)：不得中英混排、不得成对双语、不得加括号译文（用户明确要求除外）；标准单位与用户给的专有名词可保留拉丁字母。
- 字段含义：`wh_ratio` 目标宽高比，跟随输入图时留空；`ratio_follow` 跟随哪张输入图的分辨率，给了比例时留空。
- 互斥：wh_ratio 有值 → ratio_follow 必须为 ""；ratio_follow 为 "<imageX>" → wh_ratio 必须为 ""。
- JSON 之外**不要**任何内容：不要问候、不要解释、不要 markdown 代码围栏。

用户要改写的编辑指令是："""


# ============================== 路径与模型发现 ==============================


def _comfy_root():
    """ComfyUI 根目录（含 comfy 包与 models 目录）。"""
    try:
        import comfy  # noqa: F401
        return Path(__import__("comfy").__file__).resolve().parent.parent
    except Exception:
        return None


def _plugin_derived_root():
    """从插件自身位置向上找 ComfyUI 根目录（同时含 models/ 与 comfy/ 或 main.py）。

    裸 Python（未启动 ComfyUI、`folder_paths` 与 `comfy` 都不在 sys.path）时靠它兜底。
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        try:
            if (parent / "models").is_dir() and ((parent / "comfy").is_dir() or (parent / "main.py").is_file()):
                return parent / "models"
        except OSError:
            continue
    return None


def _model_roots():
    """候选的 models 根目录（仅返回存在的目录，保序去重）。"""
    roots = []
    try:
        import folder_paths
        models_dir = getattr(folder_paths, "models_dir", None)
        if models_dir:
            roots.append(Path(models_dir))
    except Exception:
        pass
    root = _comfy_root()
    if root is not None:
        roots.append(root / "models")
    fallback = _plugin_derived_root()
    if fallback is not None:
        roots.append(fallback)

    out = []
    for candidate in roots:
        try:
            if candidate.is_dir() and candidate not in out:
                out.append(candidate)
        except OSError:
            continue
    return out


def llm_model_dirs():
    """`models/LLM` 目录列表（目录名大小写不敏感）。"""
    dirs = []
    for root in _model_roots():
        try:
            children = sorted(root.iterdir())
        except OSError:
            continue
        for child in children:
            try:
                if child.is_dir() and child.name.lower() == LLM_DIR_NAME and child not in dirs:
                    dirs.append(child)
            except OSError:
                continue
    return dirs


def list_llm_models():
    """`models/LLM` 下的量化权重文件名（排序，供 COMBO 使用）。"""
    names = []
    for directory in llm_model_dirs():
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_file() and entry.suffix.lower() in MODEL_SUFFIXES and entry.name not in names:
                    names.append(entry.name)
            except OSError:
                continue
    return names


def resolve_model_path(name):
    """把下拉里的文件名（或绝对路径）解析为实际存在的权重路径；找不到返回 None。"""
    if name is None:
        return None
    text = str(name).strip()
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        try:
            return path if path.is_file() else None
        except OSError:
            return None
    for directory in llm_model_dirs():
        candidate = directory / path.name
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


# ============================== 体积与放置 ==============================


def _read_safetensors_header(path):
    """只读 safetensors 头部（不映射张量），返回 (张量表, __metadata__)。"""
    with open(path, "rb") as handle:
        raw = handle.read(8)
        if len(raw) < 8:
            raise ValueError("safetensors 头部不完整：{}".format(path))
        (header_size,) = struct.unpack("<Q", raw)
        header = json.loads(handle.read(header_size).decode("utf-8"))
    metadata = header.pop("__metadata__", {}) or {}
    return header, metadata


def _safetensors_header(path):
    """只读 safetensors 头部（不映射张量），返回 {张量名: 头部信息}。"""
    return _read_safetensors_header(path)[0]


def _safetensors_metadata(path):
    """只读 safetensors 的 `__metadata__`（量化格式声明在这里）。"""
    return _read_safetensors_header(path)[1]


_DTYPE_BYTES = {
    "F64": 8, "I64": 8, "F32": 4, "I32": 4, "F16": 2, "BF16": 2, "I16": 2, "U16": 2,
    "F8_E4M3": 1, "F8_E5M2": 1, "I8": 1, "U8": 1, "BOOL": 1,
}


def state_dict_storage_bytes(state_dict):
    """权重文件的**实际存储**字节数（量化张量按打包字节，不按逻辑元素展开）。

    只读文件头即可算出：`numel(shape) * dtype_size`。9B 模型里 int4 打包权重是
    逻辑体积的一半，用「逻辑元素 × bf16」估算会得到 17.5GB、把 8GB 卡误判成放不下。
    """
    total = 0
    for info in state_dict.values():
        count = 1
        for dim in info["shape"]:
            count *= int(dim)
        total += count * _DTYPE_BYTES.get(info["dtype"], 1)
    return total


def state_dict_logical_size(state_dict, metadata=None):
    """把权重按原始精度展开后的**逻辑**体积（诊断/对比用）。

    打包格式（int4/int6）在文件里存的是半宽/0.75 宽的 int8，逻辑元素数是打包元素数的
    2 倍 / 4/3 倍；量化格式从 `__metadata__._quantization_metadata` 读，读不到就按
    bf16 稠密（×2）保守估计。
    """
    formats = {}
    if metadata:
        try:
            formats = json.loads(metadata.get("_quantization_metadata", "{}")).get("layers", {})
        except Exception:
            formats = {}
    total = 0
    for name, info in state_dict.items():
        count = 1
        for dim in info["shape"]:
            count *= int(dim)
        layer = name[:-len(".weight")] if name.endswith(".weight") else None
        factor = 2  # bf16
        if layer is not None:
            fmt = (formats.get(layer) or {}).get("format")
            if fmt == "asym_w4a8_int8":
                count *= 2
            elif fmt == "w6a8_int8":
                count = count * 4 // 3
        total += count * factor
    return total


def file_storage_bytes(path):
    """量化权重文件的实际存储体积（读头部，微秒级）。"""
    return state_dict_storage_bytes(_safetensors_header(path))


@dataclasses.dataclass
class Placement:
    """一次加载的完整放置方案（不只是一个初始设备）。"""

    load_device: object
    offload_device: object
    initial_device: object
    disable_dynamic: bool
    reason: str = ""


def _cpu():
    return torch.device("cpu")


def _accelerator_device():
    """可用的加速设备（CUDA / MPS），没有则返回 None。"""
    if torch is None:
        return None
    try:
        import comfy.model_management as mm
        device = mm.get_torch_device()
        if mm.is_device_cuda(device) or mm.is_device_mps(device):
            return device
    except Exception:
        pass
    try:
        if torch.cuda.is_available():
            return torch.device("cuda")
    except Exception:
        pass
    return None


def _device_total_bytes(device):
    """加速设备的总显存字节数（拿不到返回 0）。"""
    if torch is None or device is None:
        return 0
    try:
        if getattr(device, "type", "") == "cuda" and torch.cuda.is_available():
            index = device.index if device.index is not None else torch.cuda.current_device()
            return int(torch.cuda.get_device_properties(index).total_memory)
    except Exception:
        pass
    try:
        if getattr(device, "type", "") == "cuda":
            return int(torch.cuda.mem_get_info()[1])
    except Exception:
        pass
    return 0


def resolve_placement(storage_bytes, preference=DEVICE_AUTO):
    """按「运行设备」给出完整放置方案。

    - 显存：静态独占显存（关掉动态分页），offload 仍留在内存以便回退；
    - 内存：全部在内存中静态运行；
    - 自动：按**打包体积**判断能否独占显存（放得下就走最快的静态路径），
      放不下才交回 ComfyUI 自己的显存管理。
    """
    accelerator = _accelerator_device()
    cpu = _cpu()

    if preference == DEVICE_RAM:
        return Placement(cpu, cpu, cpu, True, "按设置强制在内存中运行")
    if preference == DEVICE_VRAM and accelerator is not None:
        return Placement(accelerator, cpu, accelerator, True, "按设置强制独占显存")
    if accelerator is not None:
        total = _device_total_bytes(accelerator)
        budget = int(total * AUTO_VRAM_FRACTION) if total else 0
        if budget and storage_bytes + VRAM_RESERVE_BYTES <= budget:
            return Placement(accelerator, cpu, accelerator, True,
                             "打包体积 {:.2f}GB 可独占显存（{:.2f}GB 预算）".format(
                                 storage_bytes / 1024 ** 3, budget / 1024 ** 3))
    load_device = accelerator if accelerator is not None else cpu
    return Placement(load_device, cpu, None, False, "显存放不下，交由 ComfyUI 显存管理按需换入")


def resolve_initial_device(storage_bytes, preference=DEVICE_AUTO):
    """放置方案对应的初始设备；交给 ComfyUI 时用它的原生启发式。"""
    placement = resolve_placement(storage_bytes, preference)
    if placement.initial_device is not None:
        return placement.initial_device
    try:
        import comfy.model_management as mm
        return mm.text_encoder_initial_device(
            placement.load_device, placement.offload_device, storage_bytes * 2)
    except Exception:
        return placement.load_device


# ============================== 量化算子后端 ==============================


def enable_fast_quant_backend():
    """挑选最快的量化算子后端，返回后端名（幂等：已启用 triton 时仍返回 triton）。

    `comfy_kitchen` 在 `torch.version.cuda < 13` 时**会禁用 CUDA 后端**（日志里有明确
    警告），此时 w4a8 只能走 eager 回退：同样的数学，但反量化是多条逐元素 kernel。
    打开 triton 后端后是单个融合 kernel（实测 gate_proj 12.0ms vs 26.3ms）。
    CUDA 后端可用时它的优先级本来就高于 triton，这里的开启不会改变选择。
    """
    try:
        import comfy_kitchen as ck
    except Exception:
        return "unknown"
    try:
        backends = ck.list_backends()
    except Exception:
        return "unknown"
    cuda = backends.get("cuda", {})
    if cuda.get("available") and not cuda.get("disabled"):
        return "cuda"
    triton = backends.get("triton", {})
    if triton.get("available"):
        if not triton.get("disabled"):
            return "triton"  # 之前已经打开过（幂等，避免缓存键抖动导致重复加载）
        try:
            ck.registry.enable("triton")
            LOGGER.info("CUDA 量化后端不可用（%s），已启用 triton 融合核",
                        cuda.get("unavailable_reason") or "torch < cu130")
            return "triton"
        except Exception as exc:  # pragma: no cover - 仅环境异常
            LOGGER.warning("启用 triton 后端失败：%s", exc)
    return "eager"


# ============================== 视觉 ==============================


def _fit_vision_size(height, width, max_side, multiple=VISION_PATCH_MULTIPLE):
    """按最长边缩放后的 (高, 宽)，两者都是 multiple 的倍数（视觉塔 patch=16 × merge=2）。"""
    if height <= 0 or width <= 0:
        raise ValueError("图像尺寸非法：{}x{}".format(width, height))
    target = max(int(max_side), multiple)
    scale = target / float(max(height, width))
    out_h = max(multiple, int(round(height * scale / multiple)) * multiple)
    out_w = max(multiple, int(round(width * scale / multiple)) * multiple)
    return out_h, out_w


def _resize_for_vision(image, max_side=VISION_MAX_SIDE_DEFAULT, multiple=VISION_PATCH_MULTIPLE):
    """把参考图缩放到最长边 = max_side，且宽高都是 multiple 的倍数（batch 保留）。"""
    if image is None:
        return None
    if torch is None:
        raise RuntimeError("缺少 torch，无法处理参考图")
    if image.dim() == 3:
        image = image.unsqueeze(0)
    height, width = int(image.shape[1]), int(image.shape[2])
    out_h, out_w = _fit_vision_size(height, width, max_side, multiple)
    if (out_h, out_w) == (height, width):
        return image
    x = image.permute(0, 3, 1, 2)
    x = torch.nn.functional.interpolate(
        x, size=(out_h, out_w), mode="bicubic", align_corners=False, antialias=True)
    return x.permute(0, 2, 3, 1).clamp(0.0, 1.0)


# ============================== 分块词表投影 ==============================


def _install_chunked_head(root, chunk_rows=HEAD_CHUNK_ROWS_DEFAULT):
    """把 lm_head 的 logits 计算换成按词表分块，数学与 ComfyUI 原生 int8 算子完全一致。

    原生 `int8_linear` 每次调用都 `weight.T.contiguous()`：248320×4096 的 int8 词表头
    意味着每次生成一个 token 都要额外申请 0.95GB 并整表转置拷贝。8GB 卡上只剩约 1GB
    空闲显存时这会触发分配器抖动（实测单次 logits 从隔离基准 123ms 涨到 3.9s）。
    分块后瞬时分配降到 chunk 级（32768 行 ≈ 128MB），且仍走同一个 `int8_linear` 算子。
    """
    if root is None or torch is None or int(chunk_rows) <= 0:
        return False
    module = getattr(getattr(root, "model", None), "lm_head", None)
    weight = getattr(module, "weight", None)
    if module is None or weight is None:
        return False
    try:
        from comfy_kitchen.tensor import QuantizedTensor
    except Exception:
        return False
    if not isinstance(weight, QuantizedTensor):
        return False
    params = getattr(weight, "_params", None)
    qdata = getattr(weight, "_qdata", None)
    if params is None or qdata is None or not getattr(params, "orig_shape", None):
        return False
    if len(tuple(params.orig_shape)) != 2:
        return False

    layout_type = getattr(module, "layout_type", None) or getattr(weight, "layout_type", None)
    vocab, inner = int(params.orig_shape[0]), int(params.orig_shape[1])
    scale = getattr(params, "scale", None)
    if layout_type is None or qdata.shape[0] != vocab:
        return False
    chunk_rows = max(1, min(int(chunk_rows), vocab))

    def chunked_logits(self, x):
        tail = x[:, -1:]
        parts = []
        for start in range(0, vocab, chunk_rows):
            end = min(start + chunk_rows, vocab)
            sub_scale = scale[start:end] if (scale is not None and scale.dim() >= 2) else scale
            sub_params = dataclasses.replace(params, scale=sub_scale, orig_shape=(end - start, inner))
            sub = QuantizedTensor(qdata[start:end], layout_type, sub_params)
            parts.append(torch.nn.functional.linear(tail, sub, None))
        return parts[0] if len(parts) == 1 else torch.cat(parts, dim=-1)

    root.logits = MethodType(chunked_logits, root)
    LOGGER.info("已启用分块词表投影：%d 行/块，共 %d 块", chunk_rows, (vocab + chunk_rows - 1) // chunk_rows)
    return True


# ============================== 思考预算 ==============================


def _transformers_tokenizer(clip):
    """从 CLIP 里掏出 transformers 的分词器（用于查特殊 token 的 id）。"""
    tokenizer = getattr(clip, "tokenizer", None)
    name = getattr(tokenizer, "clip_name", None)
    inner = getattr(tokenizer, name, None) if isinstance(name, str) else None
    return getattr(inner, "tokenizer", inner)


def _think_end_token_id(clip):
    """`</think>` 的 token id；查不到返回 None（此时思考预算退化为只加软提示）。"""
    tokenizer = _transformers_tokenizer(clip)
    for candidate in ("</think>", "<|/think|>", "</thinking>"):
        try:
            token_id = tokenizer.convert_tokens_to_ids(candidate)
        except Exception:
            continue
        if isinstance(token_id, int) and token_id >= 0 and token_id != getattr(tokenizer, "unk_token_id", None):
            return token_id
    # 兜底：Qwen3.5 的思考标记是单个 added token，可用 decode 反查
    for token_id in (248069,):
        try:
            if "</think>" in clip.decode([token_id]):
                return token_id
        except Exception:
            continue
    return None


def with_thinking_hint(system_prompt, budget):
    """把思考预算的软提示插进系统提示词。

    官方 edit 提示词以 `The user's edit instruction to rewrite is:` 结尾，这一句必须**紧贴**
    用户指令，所以软提示要插在它**前面**，不能直接追加到末尾。
    """
    hint = THINKING_BUDGET_HINT.format(budget=int(budget))
    text = (system_prompt or "").rstrip()
    if text.endswith(EDIT_INSTRUCTION_CUE):
        head = text[:-len(EDIT_INSTRUCTION_CUE)].rstrip()
        return "{}\n\n{}\n{}".format(head, hint, EDIT_INSTRUCTION_CUE)
    return "{}\n\n{}".format(text, hint)


def sample_token_with_thinking_budget(original, think_end_id, budget):
    """包一层 `sample_token`：思考用满 budget 个 token 后强制吐出 `</think>`。

    Qwen3.5 的思考就是普通 token 流（`<think>…</think>`），预算用尽时把 `</think>` 作为
    下一个 token 注入，模型随即转入正式答案——否则模型可能把「最大长度」全部花在思考上，
    最终返回空答案（实测 `思考=True` + 小 max_length 就是这个表现）。

    ⚠️ 一旦思考块关闭（模型自己吐出了 `</think>`，或这里强制注入）就**彻底停止干预**，
    否则会在正式答案中间插进 `</think>`。`budget <= 0` 表示不限，原样返回原函数。
    """
    if int(budget) <= 0:
        return original

    state = {"steps": 0, "closed": False}

    def sample_token(logits, *args, **kwargs):
        if state["closed"]:
            return original(logits, *args, **kwargs)
        if state["steps"] >= int(budget):
            state["closed"] = True
            return torch.full((logits.shape[0], 1), int(think_end_id),
                              dtype=torch.long, device=logits.device)
        token = original(logits, *args, **kwargs)
        state["steps"] += 1
        try:
            if int(token.reshape(-1)[0]) == int(think_end_id):
                state["closed"] = True
        except Exception:
            pass
        return token

    return sample_token


@contextlib.contextmanager
def temporary_sample_token(root, sampler):
    """临时替换实例上的 `sample_token`，退出时**精确还原**。

    `sample_token` 通常是类方法（`BaseGenerate.sample_token`），实例上原本没有这个属性，
    所以退出时 `del` 即可回落；但若实例上原本就有（测试替身 / 未来改动），必须还原原值，
    否则下一次调用会丢掉采样器。
    """
    previous = root.__dict__.get("sample_token") if hasattr(root, "__dict__") else None
    root.sample_token = sampler
    try:
        yield
    finally:
        if previous is not None:
            root.sample_token = previous
        else:
            try:
                del root.sample_token
            except AttributeError:
                pass


# ============================== 加载（含跨次运行缓存） ==============================


@dataclasses.dataclass
class LoadedModel:
    """一份已加载（并缓存）的模型。"""

    key: str
    path: Path
    clip: object
    inner: object
    root: object
    device: object
    storage_bytes: int
    backend: str
    head_chunk_rows: int = HEAD_CHUNK_ROWS_DEFAULT
    chunked_head: bool = False
    vision_on_gpu: bool = False
    placement_key: str = ""

    @property
    def visual(self):
        return getattr(self.root, "visual", None)


# 按权重路径缓存：同一份权重绝不重复加载（重复加载会触发 ComfyUI 卸载旧 patcher，
# 在部分环境（torch 2.8+cu129 + triton）卸载 mmap 量化权重会直接崩进程）。
# 只保留当前这一份权重：8GB 卡上两份 6.38GB 编码器根本放不下，多缓存没有意义。
_MODEL_CACHE = {}


def _clip_inner(clip):
    """取 SD1ClipModel 里真正的文本编码器（属性名 = clip_name，如 qwen35_9b）。"""
    cond = getattr(clip, "cond_stage_model", None)
    name = getattr(cond, "clip", None)
    if isinstance(name, str):
        inner = getattr(cond, name, None)
        if inner is not None:
            return inner
    for module in getattr(cond, "modules", lambda: [])():
        if hasattr(module, "transformer"):
            return module
    return None


def _weights_device(root):
    """模型主体权重当前所在设备（取第一个量化权重）。"""
    if root is None:
        return None
    try:
        model = getattr(root, "model", root)
        layers = getattr(model, "layers", None)
        if layers:
            for parameter in layers[0].parameters():
                return parameter.device
        for parameter in root.parameters():
            return parameter.device
    except Exception:
        return None
    return None


def _evict_cache(keep_key=None):
    """丢掉不再使用的缓存条目并归还显存。"""
    dropped = False
    for key in list(_MODEL_CACHE.keys()):
        if keep_key is not None and key == keep_key:
            continue
        _MODEL_CACHE.pop(key, None)
        dropped = True
    if dropped:
        gc.collect()
        try:
            import comfy.model_management as mm
            mm.soft_empty_cache()
        except Exception:
            pass


def load_qwen35_clip(model_path, device_preference=DEVICE_AUTO,
                     head_chunk_rows=HEAD_CHUNK_ROWS_DEFAULT):
    """加载（或复用缓存）Qwen-Image-2.1 PE-I2I 的文本编码器与分词器。

    缓存按**权重路径**索引：同一份权重只加载一次；只有「设备方案变了」或「换了另一个
    权重文件」才会真正重新加载。
    """
    if torch is None:
        raise RuntimeError("缺少 torch，无法加载模型")
    path = Path(model_path)
    if not path.is_file():
        raise ValueError("{}：模型文件不存在（{}）".format(NODE_DISPLAY_NAME, path))

    storage_bytes = file_storage_bytes(path)
    placement = resolve_placement(storage_bytes, device_preference)
    placement_key = "{}/{}/{}".format(placement.load_device, placement.offload_device,
                                      placement.disable_dynamic)
    backend = enable_fast_quant_backend()
    key = str(path.resolve())

    cached = _MODEL_CACHE.get(key)
    if cached is not None and cached.placement_key == placement_key:
        _apply_head_chunk(cached, head_chunk_rows)
        cached.backend = backend
        _ensure_resident(cached, placement)
        return cached

    _evict_cache(keep_key=key)

    import comfy.sd as comfy_sd

    model_options = {
        "load_device": placement.load_device,
        "offload_device": placement.offload_device,
    }
    if placement.initial_device is not None:
        model_options["initial_device"] = placement.initial_device

    LOGGER.info("%s：加载 %s（%s，%.2fGB 权重，后端 %s）", NODE_DISPLAY_NAME, path.name,
                placement.reason, storage_bytes / 1024 ** 3, backend)
    clip = comfy_sd.load_clip(
        [str(path)],
        embedding_directory=None,
        clip_type=comfy_sd.CLIPType.QWEN_IMAGE,
        model_options=model_options,
        disable_dynamic=placement.disable_dynamic,
    )
    inner = _clip_inner(clip)
    root = getattr(inner, "transformer", None) if inner is not None else None
    if root is None:
        raise RuntimeError("{}：模型结构不是 Qwen3.5（未找到 transformer），请确认权重".format(NODE_DISPLAY_NAME))

    entry = LoadedModel(
        key=key, path=path, clip=clip, inner=inner, root=root,
        device=placement.load_device, storage_bytes=storage_bytes, backend=backend,
        placement_key=placement_key)
    _apply_head_chunk(entry, head_chunk_rows)
    _place_vision(entry, want_gpu=False)
    _MODEL_CACHE[key] = entry
    _ensure_resident(entry, placement)
    return entry


def _apply_head_chunk(entry, chunk_rows):
    """按当前设置安装/卸载分块词表投影（同一份权重上可反复切换）。"""
    chunk_rows = int(chunk_rows or 0)
    if chunk_rows == int(entry.head_chunk_rows or 0) and entry.chunked_head == (chunk_rows > 0):
        return entry.chunked_head
    if chunk_rows <= 0:
        try:
            delattr(entry.root, "logits")
        except AttributeError:
            pass
        entry.chunked_head = False
    else:
        entry.chunked_head = _install_chunked_head(entry.root, chunk_rows)
    entry.head_chunk_rows = chunk_rows
    return entry.chunked_head


def _ensure_resident(entry, placement):
    """确保权重真的**完整**在目标设备（缓存命中时模型可能已被 ComfyUI 换回内存）。

    判据不能只看 `layers[0]` 的第一个参数——`partially_unload` 是按模块挑的，可能只把中间
    若干层的量化权重搬回内存，头几层仍在显存上，于是「看起来是好的」但每 token 都在搬权重。
    """
    if torch is None:
        return
    target = placement.load_device
    current = _weights_device(entry.root)
    offloaded = _first_off_device_quantized(entry, target)
    if offloaded is None and (current is None or current.type == target.type):
        return
    try:
        import comfy.model_management as mm
        mm.load_models_gpu([entry.clip.patcher], force_full_load=True)
    except Exception as exc:
        LOGGER.warning("%s：把权重换回 %s 失败：%s", NODE_DISPLAY_NAME, target, exc)
        return
    entry.device = target
    LOGGER.info("%s：缓存权重已换回 %s（此前 %s 不在显存上）", NODE_DISPLAY_NAME, target,
                offloaded or current)


def _free_vram_gb(device):
    """诊断用：设备空闲显存（GB）。"""
    try:
        import comfy.model_management as mm
        return mm.get_free_memory(device) / 1024 ** 3
    except Exception:
        try:
            return torch.cuda.mem_get_info()[0] / 1024 ** 3
        except Exception:
            return -1.0


def module_bytes(module):
    """模块参数占用的字节数（量化张量按打包存储算）。"""
    total = 0
    for parameter in module.parameters():
        if parameter is None:
            continue
        try:
            total += parameter.numel() * parameter.element_size()
        except Exception:
            continue
    return total


def _first_off_device_quantized(entry, target):
    """主干里第一个不在 target 上的量化权重名；全部在目标设备上时返回 None。

    只看 `root.model`（编码器主干：embed_tokens / layers / lm_head），**不含视觉塔**——
    视觉塔按需放在内存是本节点的设计行为，不算「被卸载」。

    ⚠️ 量化主干 6.38GB 只要被搬走一部分，之后每个 token 都要把那些层经 PCIe 搬回显存
    （`MixedPrecisionOps` 的 `comfy_cast_weights` + `cast_bias_weight` 路径），
    实测 0.22s/token → 1.1~1.2s/token，同时显存占用从 ~8GB 掉到 3~5GB。
    """
    if torch is None or target is None or entry is None:
        return None
    model = getattr(getattr(entry, "root", None), "model", None)
    if model is None:
        return None
    target_type = getattr(target, "type", None) or str(target)
    try:
        modules = list(model.named_modules())
    except Exception:
        return None
    for name, module in modules:
        device = getattr(getattr(module, "weight", None), "device", None)
        if device is None:
            continue
        if getattr(device, "type", None) != target_type:
            return name or "<root>"
    return None


def _encoder_loaded_model(entry):
    """ComfyUI 侧代表本模型的那条 **LoadedModel**（`keep_loaded` 必须传它，不能传 patcher）。

    ⚠️ 这就是「显存紧张/带图时每 token 慢到 1.1~1.2s」的根因：旧实现遍历
    `mm.loaded_models()`（它返回的是 **patcher 本身**）却拿 `loaded.model` 去比 `clip.patcher`
    （那是文本编码器模块，永远不相等）→ 拿到 None → `keep_loaded=[]`。

    `free_memory()` 里的判断是 `shift_model not in keep_loaded`，其中 `shift_model` 是
    `current_loaded_models` 里的 `LoadedModel` 对象，比较走 `LoadedModel.__eq__`
    （`self.model is other.model`）。所以 `keep_loaded` 里必须是 **LoadedModel**，
    传裸 patcher 或不传都会让 ComfyUI 有权把自己的量化编码器部分卸载。
    """
    try:
        import comfy.model_management as mm
    except Exception:
        return None
    patcher = getattr(getattr(entry, "clip", None), "patcher", None)
    if patcher is None:
        return None
    candidates = getattr(mm, "current_loaded_models", None)
    if candidates is None:  # 兼容只暴露 loaded_models() 的版本
        try:
            candidates = list(mm.loaded_models())
        except Exception:
            return None
    loader = getattr(mm, "LoadedModel", None)
    for item in list(candidates):
        if item is patcher or getattr(item, "model", None) is patcher:
            if loader is not None and not isinstance(item, loader):
                try:
                    return loader(patcher)
                except Exception:
                    return None
            return item
    return None


def _keep_loaded(entry):
    """要交给 ComfyUI 保住的那条 LoadedModel（拿不到就给空表，但会记一条警告）。"""
    loaded = _encoder_loaded_model(entry)
    if loaded is None:
        LOGGER.warning("%s：ComfyUI 记账里没找到本模型的 LoadedModel，"
                       "本次腾显存无法声明 keep_loaded（有被部分卸载的风险）", NODE_DISPLAY_NAME)
        return []
    return [loaded]


def _reserve_vram(entry, required_bytes, target_device):
    """按 ComfyUI 的账本腾出显存，并**保住我们自己的量化编码器**。"""
    keep = _keep_loaded(entry)
    try:
        import comfy.model_management as mm
        mm.free_memory(int(required_bytes), target_device, keep_loaded=keep)
    except Exception as exc:  # pragma: no cover - 仅环境异常
        LOGGER.warning("%s：腾显存失败：%s", NODE_DISPLAY_NAME, exc)
    return keep


def ensure_encoder_residency(entry, extra_bytes=0):
    """确保量化编码器**完整**驻留目标设备，并为本节点要用的额外显存腾地方。

    ⚠️ 两条硬约束（正式环境 cu130 实测）：

    ① **`keep_loaded` 必须传 `LoadedModel`**（见 `_encoder_loaded_model`）。否则
    `free_memory()` 会挑我们自己的编码器做 `partially_unload()`：一部分量化层回到内存、
    `comfy_cast_weights` 被置 True，之后每个 token 都要经 PCIe 搬回显存，
    实测 0.22s/token → **1.1~1.2s/token**（用户生产环境的实测口径）。

    ② **权重已在目标设备时什么都不做**：多余的 `free_memory` / `soft_empty_cache` 会清掉
    torch 的分配器缓存，让紧随其后的 prefill 每个临时张量都走 cudaMalloc，
    实测 prefill 从 3.5s 涨到 19~27s（空闲显存越少越明显）。
    """
    if torch is None or str(getattr(entry.device, "type", "")) == "cpu":
        return
    try:
        import comfy.model_management as mm
    except Exception:
        return
    headroom = int(extra_bytes) + 512 * 1024 * 1024
    target = entry.device
    current = _weights_device(entry.root)
    offloaded = _first_off_device_quantized(entry, target)
    if offloaded is None and (current is None or current.type == target.type):
        # 主干的量化权重全在目标设备上：**什么都不做**，保住 torch 的分配器缓存
        return
    try:
        mm.free_memory(int(entry.storage_bytes * 1.15) + headroom, target,
                       keep_loaded=_keep_loaded(entry))
        mm.load_models_gpu([entry.clip.patcher], force_full_load=True)
        if offloaded is not None:
            LOGGER.info("%s：检测到 %s 曾被搬离显存，已整体重载回 %s",
                        NODE_DISPLAY_NAME, offloaded, target)
        else:
            LOGGER.info("%s：权重已整体加载到 %s", NODE_DISPLAY_NAME, target)
    except Exception as exc:  # pragma: no cover - 仅环境异常
        LOGGER.warning("%s：整体加载失败：%s", NODE_DISPLAY_NAME, exc)


def generate_without_patcher(entry, tokens, **kwargs):
    """直接调用编码器自身的 `generate`，绕过 `CLIP.generate` 里的 `load_model`。

    `CLIP.generate` 会先 `load_models_gpu([patcher], memory_required=...)`；当显存紧张
    （带图的 8GB 场景）它会尝试**部分卸载我们的量化权重**从而崩在
    `QuantizedTensor._to_copy` 上。权重驻留由 `ensure_encoder_residency` 负责，
    这里只做 `CLIP.generate` 剩下的部分：设置 clip 选项 + 设备上下文 + 量化矩阵乘开关。
    """
    inner = entry.inner
    if inner is None:  # 结构异常（或测试替身）时退回原生路径
        return entry.clip.generate(tokens, **kwargs)
    try:
        import comfy.model_management as mm
        import comfy.ops as comfy_ops
    except Exception:
        return entry.clip.generate(tokens, **kwargs)  # 退化到原生路径
    device = entry.device
    inner.reset_clip_options()
    inner.set_clip_options({"layer": None})
    inner.set_clip_options({"execution_device": device})
    with mm.cuda_device_context(device), comfy_ops.use_quantized_matmul(inner, device):
        return inner.generate(tokens, **kwargs)


def count_image_embeds(tokens):
    """token 序列里 image 占位符的个数（用于判断视觉塔何时可以下卡）。"""
    total = 0
    try:
        for batch in tokens.values():
            for row in batch:
                for item in row:
                    if item and isinstance(item[0], dict):
                        total += 1
    except Exception:
        return 0
    return total


@contextlib.contextmanager
def release_vision_after_prefill(root, image_embeds, visual):
    """视觉塔只在 prefill 编码图像时用一次，编完立刻让它下卡，把 0.85GB 还给解码阶段。

    `Qwen35.preprocess_embed` 只在图像 embed 上被调用，且都发生在 decode 循环之前，
    所以按 image 占位符个数计数，最后一个编码完就撤。

    ⚠️ 下卡后**不要** `soft_empty_cache()`：0.85GB 留在 torch 的分配器缓存里，
    解码阶段的临时张量（分块词表 128MB、注意力 workspace 等）可以直接复用；
    还给驱动的话解码每一步都要重新 cudaMalloc，显存紧张时会明显变慢。
    """
    if visual is None or int(image_embeds) <= 0:
        yield
        return
    previous = root.__dict__.get("preprocess_embed") if hasattr(root, "__dict__") else None
    original = root.preprocess_embed
    state = {"left": int(image_embeds)}

    def preprocess_embed(embed, device):
        out = original(embed, device)
        state["left"] -= 1
        if state["left"] <= 0:
            try:
                visual.to("cpu")
                LOGGER.info("%s：视觉塔 prefill 用完已下卡，显存还给解码", NODE_DISPLAY_NAME)
            except Exception as exc:  # pragma: no cover - 仅环境异常
                LOGGER.warning("%s：视觉塔下卡失败：%s", NODE_DISPLAY_NAME, exc)
        return out

    root.preprocess_embed = preprocess_embed
    try:
        yield
    finally:
        if previous is not None:
            root.preprocess_embed = previous
        else:
            try:
                del root.preprocess_embed
            except AttributeError:
                pass


def _place_vision(entry, want_gpu):
    """视觉塔只在带图时占用显存（0.85GB bf16）。

    ⚠️ `visual.to("cuda")` 是**绕过 ComfyUI 显存管理**的裸分配，所以：

    - 上卡前必须 `free_memory(..., keep_loaded=[我们的 LoadedModel])`：不带 keep 时
      ComfyUI 会拿我们自己的量化编码器开刀（`partially_unload`），带图跑一次就把编码器
      拖成「每 token 搬权重的慢模式」（见 `_encoder_loaded_model`）。
    - 显存真放不下时**退回内存**（慢但正确）并明确日志，不静默劣化、也不让工作流 OOM。
    - 下卡后**不要** `soft_empty_cache()`：0.85GB 留在分配器缓存里给解码复用更划算。
    """
    visual = entry.visual
    if visual is None or torch is None:
        return
    target = entry.device if (want_gpu and str(getattr(entry.device, "type", "")) != "cpu") else torch.device("cpu")
    try:
        current = next(visual.parameters()).device
    except StopIteration:
        return
    if current.type == target.type:
        entry.vision_on_gpu = target.type != "cpu"
        return
    if target.type != "cpu":
        required = int(module_bytes(visual) * 1.05) + 128 * 1024 * 1024
        _reserve_vram(entry, required, target)
        try:
            visual.to(target)
        except Exception as exc:
            LOGGER.warning("%s：视觉塔上显存失败（%s），本次改为在内存里做视觉编码（会明显变慢）；"
                           "可调小「参考图最长边」，或先卸载同工作流里其他占显存的模型",
                           NODE_DISPLAY_NAME, exc)
            try:
                visual.to(torch.device("cpu"))
            except Exception:  # pragma: no cover - 仅环境异常
                pass
            entry.vision_on_gpu = False
            return
    else:
        visual.to(target)
    entry.vision_on_gpu = target.type != "cpu"
    LOGGER.info("%s：视觉塔已移到 %s（空闲显存 %.2fGB）", NODE_DISPLAY_NAME, target,
                _free_vram_gb(target))


# ============================== 节点 ==============================


class TextGenerateQwen21PromptNode:
    """本地 Qwen-Image-2.1 PE-I2I 提示词改写（W4A8 量化，8GB 显存特化）。"""

    CATEGORY = "YTmmi/text"
    DESCRIPTION = ('生成Qwen2.1提示词：用本地 Qwen-Image-2.1 PE-I2I（Qwen3.5-9B 微调 + W4A8 量化，'
                   '模型放 models/LLM）把提示词改写为 Qwen-Image 2.1 提示词，并可带参考图做「图像编辑」改写；'
                   '内置中文精简版系统提示词（t2i 八步法 / edit 语言决策+ratio_follow 判定表，token 仅为官方英文原文的 52%），'
                   '参考原生 TextGenerateLTX2Prompt 的两段式输出（生成文本 / 思考内容，含思考预算），'
                   '针对 8GB 显存做静态独占加载、分块词表投影、视觉塔按需上显存、算子后端自适应与模型缓存')

    @classmethod
    def INPUT_TYPES(cls):
        # 下拉选项每次重新扫描（COMBO 动态选项约定）；空列表时用 ["") 占位，避免 Value not in list
        try:
            models = list_llm_models()
        except Exception:
            models = []
        return {
            "required": {
                "模型": (models or [""], {"default": models[0] if models else "",
                                          "tooltip": "models/LLM 下的量化权重（comfyui-quantized 格式的 .safetensors）"}),
                "提示词": ("STRING", {"default": "", "multiline": True,
                                      "placeholder": "输入要改写的提示词（可用中文）"}),
                "任务类型": ([TASK_AUTO, TASK_T2I, TASK_EDIT], {"default": TASK_AUTO,
                                                               "tooltip": "自动：接了参考图按「图像编辑」改写，否则按「文生图」"}),
                "最大长度": ("INT", {"default": 1024, "min": 1, "max": 32768,
                                     "tooltip": "最多生成的 token 数（不含提示词本身）。改写结果是 JSON，"
                                                "实测约需 300~400 token；默认 1024 足够，压到 256 会在 JSON 中间被截断"}),
                "采样模式": ([SAMPLING_ON, SAMPLING_OFF], {"default": SAMPLING_ON,
                                                           "tooltip": "off 时贪心解码（忽略种子）"}),
                "温度": ("FLOAT", {"default": 0.7, "min": 0.01, "max": 2.0, "step": 0.01}),
                "top_k候选数": ("INT", {"default": 64, "min": 0, "max": 1000}),
                "top_p累积概率": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "min_p概率下限": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "重复惩罚": ("FLOAT", {"default": 1.05, "min": 0.0, "max": 5.0, "step": 0.01}),
                # 与原生 TextGenerate 采样参数对齐（原生 presence_penalty 默认 0.0，等价于不启用；
                # 只有「重复惩罚」保持 1.05 时惩罚链本来就是激活的，故默认值不改变任何既有行为）
                "存在惩罚": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.01,
                                       "tooltip": "每出现一次就把该 token 的 logits 减掉这个值（原生 presence_penalty）；"
                                                  "0 = 不启用"}),
                # 官方 control_after_generate：前端自动生成「生成后控制」下拉，后端不参与种子推进
                "种子": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True,
                                 "tooltip": "旁边的「生成后控制」可让种子在每次生成后自动变化"}),
                "思考": ("BOOLEAN", {"default": False,
                                     "tooltip": "打开后模型先输出思考再给提示词（更慢，但便于核对）"}),
                "运行设备": ([DEVICE_AUTO, DEVICE_VRAM, DEVICE_RAM], {"default": DEVICE_AUTO,
                                                                      "tooltip": "自动：按打包体积判断能否独占显存；内存：6.4GB 权重全在内存（很慢，仅兜底）"}),
            },
            "optional": {
                "图像": ("IMAGE",),
                "思考预算": ("INT", {
                    "default": THINKING_BUDGET_DEFAULT, "min": 0, "max": 8192, "step": 16,
                    "tooltip": "仅「思考」打开时生效：思考最多用多少个 token，用满就强制结束思考块转入正式答案"
                               "（0 = 不限）。不设预算时模型可能把「最大长度」全花在思考上而返回空答案"}),
                "参考图最长边": ("INT", {"default": VISION_MAX_SIDE_DEFAULT, "min": 64, "max": 4096,
                                         "step": VISION_PATCH_MULTIPLE,
                                         "tooltip": "参考图缩放到该最长边，并取 32 的倍数（视觉塔 patch=16 × merge=2）。"
                                                    "最长边越大视觉 token 越多、参考细节越足，但 prefill 明显变慢"
                                                    "（实测 1024px 比 512px 多花约 15~25s）；显存紧张时调小它也能让视觉塔有地方上卡"}),
                "系统提示词": ("STRING", {"multiline": True, "default": "", "forceInput": True,
                                          "tooltip": "留空则按「任务类型」使用内置的**官方提示词原文**"
                                                     "（内置已是**中文精简版**：实测 t2i 2427→1283 token、edit 4510→2349 token，"
                                                     "token 只要官方英文原文的 52%；"
                                                     "官方英文原文仍逐字保存在 skills/qwen-image-*-prompt/references/ 下，"
                                                     "需要时可复制过来）；接更短的版本能进一步减少 prefill 时间"}),
                "词表分块行数": ("INT", {"default": HEAD_CHUNK_ROWS_DEFAULT, "min": 0, "max": 262144,
                                         "step": 4096,
                                         "tooltip": "词表投影分块行数（0 = 不分块）。显存紧张时保持默认；调小更省显存、略慢"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("生成文本", "思考内容")
    FUNCTION = "generate"
    OUTPUT_NODE = False
    SEARCH_ALIASES = ["qwen", "提示词改写", "qwen-image", "2.1", "扩写", "本地大模型", "w4a8",
                      "qwen35", "prompt enhance"]

    def generate(self, **kwargs):
        prompt = kwargs.get("提示词", "")
        prompt = "" if prompt is None else str(prompt)
        if not prompt.strip():
            raise ValueError("{}：提示词不能为空".format(NODE_DISPLAY_NAME))

        model_name = kwargs.get("模型", "")
        model_path = resolve_model_path(model_name)
        if model_path is None:
            raise ValueError(
                "{}：未找到模型 {}，请把量化权重放到 models/LLM 目录（目录名大小写不敏感）".format(
                    NODE_DISPLAY_NAME, model_name))

        device_preference = kwargs.get("运行设备", DEVICE_AUTO)
        chunk_rows = int(kwargs.get("词表分块行数", HEAD_CHUNK_ROWS_DEFAULT) or 0)
        entry = load_qwen35_clip(model_path, device_preference=device_preference,
                                 head_chunk_rows=chunk_rows)

        image = kwargs.get("图像")
        has_image = image is not None
        task = kwargs.get("任务类型", TASK_AUTO)
        if task == TASK_AUTO:
            task = TASK_EDIT if has_image else TASK_T2I

        system_prompt = kwargs.get("系统提示词", "")
        system_prompt = "" if system_prompt is None else str(system_prompt).strip()
        if not system_prompt:
            system_prompt = QWEN21_EDIT_SYSTEM_PROMPT if task == TASK_EDIT else QWEN21_T2I_SYSTEM_PROMPT

        if has_image:
            image = _resize_for_vision(image, kwargs.get("参考图最长边", VISION_MAX_SIDE_DEFAULT))
        # 带图时要额外占 0.85GB 视觉塔：先按 ComfyUI 的账本腾地方，再把它搬上卡；
        # 不带图则确保视觉塔已下卡（把显存留给编码器）
        vision_bytes = module_bytes(entry.visual) if (has_image and entry.visual is not None) else 0
        ensure_encoder_residency(entry, extra_bytes=vision_bytes)
        _place_vision(entry, want_gpu=has_image)

        thinking = bool(kwargs.get("思考", False))
        budget = int(kwargs.get("思考预算", THINKING_BUDGET_DEFAULT) or 0)
        sampling = str(kwargs.get("采样模式", SAMPLING_ON)) != SAMPLING_OFF
        clip = entry.clip

        # 思考预算：软提示（让模型自觉简短）+ 硬截断（用满预算就强制 `</think>`）
        think_end_id = None
        force_close = None
        if thinking and budget > 0:
            system_prompt = with_thinking_hint(system_prompt, budget)
            think_end_id = _think_end_token_id(clip)
            if think_end_id is None:
                LOGGER.warning("%s：查不到 `</think>` 的 token id，思考预算只保留软提示",
                               NODE_DISPLAY_NAME)

        tokens = clip.tokenize(
            prompt, image=image, thinking=thinking, min_length=1, system_prompt=system_prompt)

        generate_kwargs = dict(
            do_sample=sampling,
            max_length=int(kwargs.get("最大长度", 1024)),
            temperature=float(kwargs.get("温度", 0.7)),
            top_k=int(kwargs.get("top_k候选数", 64)),
            top_p=float(kwargs.get("top_p累积概率", 0.95)),
            min_p=float(kwargs.get("min_p概率下限", 0.05)),
            repetition_penalty=float(kwargs.get("重复惩罚", 1.05)),
            presence_penalty=float(kwargs.get("存在惩罚", 0.0)),
            seed=int(kwargs.get("种子", 0)),
            mtp=False,
        )
        image_embeds = count_image_embeds(tokens) if has_image else 0
        with release_vision_after_prefill(entry.root, image_embeds, entry.visual if has_image else None):
            if think_end_id is not None:
                sampler = sample_token_with_thinking_budget(
                    entry.root.sample_token, think_end_id, budget)
                with temporary_sample_token(entry.root, sampler):
                    generated = generate_without_patcher(entry, tokens, **generate_kwargs)
            else:
                generated = generate_without_patcher(entry, tokens, **generate_kwargs)
        if has_image:
            _place_vision(entry, want_gpu=False)
        text = clip.decode(generated)

        # 与原生 TextGenerate 一致：思考块要么在生成文本里，要么被 max_length 截断而没有结束标记
        reasoning, closed, answer = text.partition("</think>")
        if not reasoning.lstrip().startswith("<think>") and not prompt.rstrip().endswith("<think>"):
            reasoning, closed, answer = "", "", text
        answer = answer.strip()
        if thinking and not closed and reasoning:
            LOGGER.warning("%s：思考块没有正常闭合（「最大长度」%s 可能被思考吃满），"
                           "建议调小「思考预算」或调大「最大长度」",
                           NODE_DISPLAY_NAME, kwargs.get("最大长度", 1024))
        if not answer and reasoning:
            LOGGER.warning("%s：答案为空而思考非空——「思考」打开时模型会先消耗 token，"
                           "请调大「最大长度」或调小「思考预算」", NODE_DISPLAY_NAME)
        return (answer, reasoning.replace("<think>", "", 1).strip())


NODE_CLASS_MAPPINGS = {
    "TextGenerateQwen21Prompt": TextGenerateQwen21PromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextGenerateQwen21Prompt": NODE_DISPLAY_NAME,
}

__all__ = [
    "TextGenerateQwen21PromptNode",
    "LoadedModel",
    "Placement",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "HEAD_CHUNK_ROWS_DEFAULT",
    "THINKING_BUDGET_DEFAULT",
    "EDIT_INSTRUCTION_CUE",
    "VISION_MAX_SIDE_DEFAULT",
    "QWEN21_T2I_SYSTEM_PROMPT",
    "QWEN21_EDIT_SYSTEM_PROMPT",
    "sample_token_with_thinking_budget",
    "with_thinking_hint",
]
