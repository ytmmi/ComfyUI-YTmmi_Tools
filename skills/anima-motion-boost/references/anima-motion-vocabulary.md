# Anima 动作词表（Motion Vocabulary）

`anima-motion-boost` 的完整词表与配方。所有条目都是**英文**、**全小写**、多词词条分隔（`mid-air` 这类
原生连字符保留），可直接粘进提示词的 general 区段。

## 0. 用法总则

1. 一张图 = 一个瞬间。先选节拍（起势 / 最高点 / 收招落地 / 情绪拍），再挑词。
2. 主动作动词 ≤2 个；体态标签可以多，但每个都要有明确的空间含义。
3. 运动暗示优先用**被带动的静物**（风、布料、碎片、线条），`motion blur` 只用在背景或非身份部位。
4. 权重需要比 SDXL 更高：`(mid-air:1.4)`、`(dynamic pose:1.3)`、`(speed lines:1.2)`；
   写字面值 1 以下的权重基本等于没写。
5. Anima 用 tag dropout 训练，**同义词堆叠不提升强度，只稀释语义**。

## 1. 动作族（Action families）

### 1.1 位移 locomotion

`walking` `running` `dashing` `sprinting` `charging` `jumping` `leaping` `hopping` `crawling` `climbing`
`sliding` `skating` `swimming` `flying` `riding` `on horseback` `diving` `crouching` `kneeling`
`getting up` `standing up` `turning around` `walking away` `walking towards viewer` `stride` `running towards viewer`

### 1.2 空中 airborne

`mid-air` `airborne` `in the air` `floating` `levitating` `falling` `free fall` `hovering` `suspended`
`upside down` `backflip` `somersault` `spinning` `twirling` `floating in air` `wind lift`

### 1.3 战斗 combat

`fighting` `fighting stance` `sword swing` `slashing` `stabbing` `thrusting` `parrying` `blocking`
`holding sword` `holding weapon` `two-handed sword` `dual wielding` `drawing sword` `sheathing sword`
`punching` `kicking` `headbutt` `grappling` `throwing` `dodging` `back-to-back` `battle` `duel`
`aiming` `holding gun` `shooting` `reloading` `nocking arrow` `drawing bow` `whip` `spear thrust`
`shield up` `guard` `damaged` `injured`

### 1.4 法术 / 异能 magic

`casting spell` `magic circle` `incantation` `chanting` `summoning` `raising hand` `outstretched hand`
`glowing hand` `energy blast` `beam` `barrier` `shield magic` `floating runes` `hex` `curse`
`transformation` `powering up` `aura` `lightning`

### 1.5 表演 / 舞蹈 performance

`dancing` `ballet` `idol` `singing` `playing guitar` `playing piano` `playing violin` `conducting`
`microphone` `stage` `pose` `dramatic pose` `stretching` `yoga` `martial arts` `spin` `hair flip`
`fingertips to chest` `hands on hips` `salute`

### 1.6 日常手势 gesture

`waving` `beckoning` `pointing` `pointing at viewer` `reaching out` `reaching towards viewer`
`hand up` `hand on own cheek` `hand on own hip` `hand on own chest` `hands on own face` `hands in pockets`
`arms crossed` `arms behind back` `arms up` `shrugging` `thumbs up` `peace sign` `v sign` `ok sign`
`holding cup` `holding book` `holding umbrella` `holding bag` `eating` `drinking` `writing` `reading`
`typing` `phone` `adjusting hair` `adjusting glasses` `tying hair` `buttoning`

### 1.7 情绪拍 emotional beat

`looking back` `looking over shoulder` `turning head` `glancing back` `reaching out` `clenching fist`
`hugging own knees` `covering face` `hands over own mouth` `tearing up` `crying` `laughing` `shouting`
`smug` `surprised` `embarrassed` `determined` `serious` `biting lip` `holding back tears`

### 1.8 双人 / 多人互动 interaction

`back-to-back` `holding hands` `hugging` `embracing` `carrying` `piggyback` `bridal carry` `princess carry`
`headpat` `leaning on person` `arm around waist` `arm around shoulder` `facing each other` `eye contact`
`sword fight` `high five` `shaking hands` `dancing together` `protecting` `standing back to back`

> 双人动作必须写清**左右与朝向**（`A on the left facing right, B on the right facing left`），
> 否则两个角色会互相揉成一团。多角色身份一致性见 `anima-prompt-character`。

## 2. 身体部位与体态（Body language）

### 2.1 躯干

`leaning forward` `leaning back` `arched back` `bent over` `bending forward` `straight posture`
`contrapposto` `twisted torso`（慎用，崩坏高发）`off-balance` `poised` `relaxed`

### 2.2 手臂与手

`outstretched arm` `arm up` `arm behind back` `arm at side` `raised arm` `bent arm` `hand on ground`
`outstretched hand` `open hand` `clenched hand` `fist` `claw pose` `holding X in right hand`
`holding X in left hand` `two hands on X`

> **左右手分工必须写死**：`holding sword in right hand, left arm extended back`。
> 只写 `holding sword` 时，模型常自行发明第三只手或把刀插进手肘。
> 负面固定加 `extra arms, extra limbs, fused fingers`。

### 2.3 腿与脚

`one leg extended` `legs apart` `legs together` `crossed legs` `tucked legs` `knees bent` `standing on one leg`
`tiptoe` `barefoot` `bent knee` `walking on air` `kicking leg up` `leg up` `split`

### 2.4 头与视线

`looking down` `looking up` `looking back` `looking away` `looking at viewer` `looking to the side`
`head tilted` `head down` `chin up` `eye contact`

### 2.5 头发与尾巴

`floating hair` `hair blowing` `wind lift` `hair between eyes` `ahoge` `ponytail swaying`
`long hair flowing` `tail swaying` `animal ears twitching` `ribbon fluttering`

## 3. 镜头 × 动作配对

| 动作强度 | 镜头标签 | 说明 |
|---|---|---|
| 跳跃 / 下落 / 下劈 | `low angle`, `from below`, `foreshortening`, `looking down at viewer` | 高度与压迫 |
| 冲击 / 必杀 / 爆发 | `dutch angle`, `impact frame`, `wide shot`, `dynamic angle` | 失衡表达冲击 |
| 冲刺 / 迎面移动 | `from side`, `front view`, `perspective`, `speed lines`, `running towards viewer` | 位移方向可读 |
| 情绪拍 / 转身 / 回望 | `close-up`, `upper body`, `portrait`, `depth of field`, `looking back` | 保住表情 |
| 蓄力 / 对峙 | `cowboy shot`, `medium shot`, `silhouette`, `backlighting` | 张力优先于细节 |

**切忌**：超广角 + 大爆炸 + 全身动作 → 角色被场面吞掉。冲击镜头请用 `medium shot` 保住角色可读性。

## 4. 运动证据（Implied motion，替代模糊）

### 4.1 风与布料

`wind` `wind lift` `strong wind` `clothes fluttering` `coat flapping` `floating skirt` `dress lift`
`scarf flying` `ribbon` `cape flowing` `hair blowing`

### 4.2 粒子与碎片

`droplets` `water splash` `splash` `debris` `pebbles` `rock fragments` `dust cloud` `dust`
`smoke` `sparks` `embers` `petals` `falling leaves` `broken glass` `feathers`

### 4.3 线条类

`speed lines` `motion lines` `action lines` `afterimage` `impact frame` `shockwave` `radial lines`
`concentration lines` `zoom lines`

> 漫画式 `speed lines` / `concentration lines` 会把画面推向漫画语言；写实取向的图里慎用。

### 4.4 光与冲击

`rim light` `backlighting` `lens flare` `glowing` `energy` `lightning` `flash` `bloom`

### 4.5 模糊（限用）

`motion blur on background` `blurry background` `motion blur on legs` `panning blur`

不要在正面写裸 `motion blur`；它同时糊脸、糊手、糊线稿，是"动作增强"最常见的自伤。

## 5. 组合配方（Recipes）

| 目标 | 标签串 |
|---|---|
| 空中下劈 | `mid-air, jumping, falling, holding sword in right hand, outstretched arm, one leg extended, looking down, low angle, foreshortening, wind, coat flapping, speed lines, dust cloud` |
| 迎面冲刺 | `running towards viewer, dashing, leaning forward, arms behind back, speed lines, dust cloud, perspective, from side` |
| 冲击落地 | `landing, impact, kneeling, one hand on ground, dust cloud, debris, shockwave, dutch angle, motion blur on background` |
| 施法 | `casting spell, magic circle, outstretched hand, glowing hand, floating runes, wind lift, floating hair, backlighting, low angle` |
| 静中带动（情绪拍） | `looking back, turning head, reaching out, hair blowing, clothes fluttering, close-up, depth of field, rim light` |
| 双人对峙 | `back-to-back, facing each other, arms crossed, sword in right hand, wind, coat flapping, medium shot, dutch angle` |
| 舞台表演 | `dancing, mid-air, arms up, one leg extended, floating skirt, confetti, stage lights, rim light, low angle` |

## 6. 反模式（Anti-patterns）

| 反模式 | 后果 | 修正 |
|---|---|---|
| `running, jumping, flying, dancing` 同框 | action soup：一个都画不全 | 只留 1 个主动作动词 |
| 只有 `jumping`，无躯干/四肢说明 | 四肢数量与朝向随机 | 补 `one leg extended` 等锚点 |
| `motion blur` 进正面主区 | 脸与手糊掉 | 换成 `speed lines`，模糊留给背景 |
| `twisted torso` 高频使用 | 腰腹结构崩坏 | 只在真正扭转时用，并加 `bad anatomy` 负面 |
| 低角度 + 静态 `standing` | 动作与镜头互不相干 | 换镜头或换动作 |
| `(action:1)` 之类的权重 | 权重比 SDXL 需求低，等于没写 | 用 `(mid-air:1.4)` |
| 正面 `speed lines` + 负面 `speed lines` | 两边抵消 | 负面只写真正不想要的项 |
| 双人不写左右与朝向 | 角色融合、换装 | 明确 `left` / `right` / `facing` |
