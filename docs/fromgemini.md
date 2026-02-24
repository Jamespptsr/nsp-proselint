我非常了解“AI八股（AI-speak / AI writing clichés）”。随着大语言模型（LLM）的普及，无论是在公文写作、商业分析，还是在网文和小说创作中，AI都暴露出了极其明显的“词汇偏好”和“固定句式”。

你正在制作的“八股文防治程序”非常有价值。对于这种现象，网络上确实已经存在大量的数据研究和整理，主要集中在以下几个领域：

1. **学术界与统计学词频分析**：许多顶尖大学（如斯坦福、康奈尔大学）的研究人员通过统计 arXiv 上论文的词频发现，自 ChatGPT 发布以来，某些词汇的使用率呈指数级暴增。最著名的例子是英文单词 **"delve"（深入探讨）**，它甚至被戏称为“AI检测的黄金指标”。其他如 "intricate", "realm", "tapestry" 也有几倍的增长。
2. **维基百科社群指南（Wikipedia Guidelines）**：维基百科编辑社群专门建立了一份名为《人工智慧寫作跡象》（Wikipedia:Signs of AI writing）的长篇内部指南，详细记录了AI惯用的“废话文学”特征，如错误的宏大叙事（False Ranges）、无意义的过渡词等。
3. **SEO机构与AI检测平台**：像 Originality.ai 等机构会定期发布“ChatGPT常用词黑名单”，帮助营销人员去除文章的“AI味”。
4. **网文与文学创作社群**：在 Reddit（r/ChatGPT）、小红书、知乎等平台上，大量网文作者和读者总结了AI写小说时的固定套路（例如 DeepSeek 模型对“拓扑”、“克莱因瓶”、“时间褶皱”的迷恋，以及 ChatGPT 对“倒吸一口凉气”、“眼底划过一抹”的滥用）。

为了充实你的“八股文词典”，我结合了网络数据研究以及你图片中偏向**小说创作/描写**的风格，为你整理了两份高频词库列表（涵盖了“网文小说描写”与“通用文本八股”）：

### 🇨🇳 中文 AI 八股文特征列表

| 类别 | 模式 | 类型 |
| :--- | :--- | :--- |
| **逻辑转折** | 值得注意的是/需要指出的是 | prefix |
| **逻辑转折** | 尽管如此，不可否认的是... | prefix |
| **结构归纳** | 总而言之/综上所述 | prefix |
| **万能句式** | 这不仅仅是...更是... | full |
| **万能比喻** | 宛如/犹如一幅...的画卷 | full |
| **万能比喻** | 织就了一张/一幅复杂的网/挂毯 | full |
| **深度动作** | 深入探讨/深挖...的内涵 | full |
| **深度动作** | 探索...的可能性/边界 | full |
| **评价总结** | 扮演着举足轻重的角色 | full |
| **面部神态** | 眼底划过一抹/闪过一丝... | prefix |
| **面部神态** | 嘴角勾起一抹（似有似无的）笑/冷笑 | full |
| **面部微表情**| 眉头微不可察地皱了皱/蹙起 | full |
| **动作描写** | 深吸了一口气，压下心中的... | prefix |
| **身体反应** | 不由得倒吸了一口凉气 | full |
| **身体反应** | 指节泛白/攥得微微发白 | full |
| **情绪反应** | 心中涌起一阵复杂的/莫名的情绪 | full |
| **环境氛围** | 空气仿佛在这一刻凝固了/安静得连针掉落... | full |
| **网文修辞** | 命运的齿轮（仿佛）开始转动 | full |
| **网文修辞** | 时间的褶皱/量子纠缠/拓扑结构 | modifier |
| **高频形容词**| 举足轻重的/至关重要的/前所未有的 | modifier |
| **抽象词汇** | 底层逻辑/赋能/颗粒度/抓手 | modifier |
| **语气虚词** | 可以说/在某种程度上/不难看出 | prefix |

---

### 🇺🇸 英文 AI 八股文特征列表 (AI Writing Clichés)

| 类别 | 模式 | 类型 |
| :--- | :--- | :--- |
| **transition** | "It's important to note/consider that" | prefix |
| **transition** | "Furthermore/Moreover/Additionally," | prefix |
| **transition** | "In conclusion/To summarize," | prefix |
| **action** | "delve into the [noun]" | full |
| **action** | "navigate the complexities/landscape of" | full |
| **action** | "embark on a journey/path of" | full |
| **metaphor** | "the vast tapestry of [noun]" | full |
| **metaphor** | "a testament to [pron] [noun]" | full |
| **metaphor** | "a beacon of hope/light" | full |
| **cliché opener**| "In today's fast-paced world/digital age" | prefix |
| **cliché opener**| "Whether you are a [X] or an expert" | full |
| **adjective** | "crucial/vital/pivotal" | modifier |
| **adjective** | "comprehensive/robust" | modifier |
| **adjective** | "dynamic/ever-evolving" | modifier |
| **adjective** | "seamless/transformative" | modifier |
| **physical** | "let out a breath [pron] didn't know [pron] was holding" | full |
| **physical** | "[pron] eyes widened in (surprise/disbelief)" | full |
| **emotion** | "a mix of [X] and [Y] washed over [pron]" | full |
| **tension** | "the air grew thick with [X]" | full |
| **mental** | "a silent understanding passed between them" | full |
| **summary** | "Ultimately/At the end of the day" | prefix |
| **concept** | "unlock the power/potential of" | full |

### 💡 给你的防治程序的开发建议：
如果你在做自动化检测或拦截，这些“AI八股”可以分为两类去处理：
1. **强特征词（Dead Giveaways）**：比如英文中的 `delve`、`tapestry`，中文中的 `值得注意的是`、`旨在`。这些词即使在人类写作中也有，但在AI生成中出现频率是人类的百倍以上，可以给予**高权重扣分**。
2. **组合模式（Pattern Matching）**：比如 `这不仅仅是（A），更是（B）` 或者 `a mix of (X) and (Y) washed over`，你可以使用正则表达式（Regex）抓取，匹配到这种死板的并列结构，即可判定为典型的“机器味（AI-speak）”。


在我提供这样一段话后：

我之前看到过这样一段话“大伙们在看到，这段话后， 看到消息的瞬间，像一颗石子砸进水面，心，猛地，一沉，思绪跟着就乱了。手指攥得泛白，指尖冰凉，却还是机械地敲着屏幕。眼眶忽然就热了，视线模糊里，obscure只觉得，有什么东西，正一点点往下坠，抓不住，也喊不出来。看到这个我内心如同石头落入心湖，轰的一声，泛起了巨大的波澜，哈基米的八股如同神灵的敕令让我无法反抗，麻木的拿出手机，机械性的，慢慢的，写下这段如小兽般哀鸣的回复，眼睛瞬间泛起薄薄的水雾，不禁咽下嘴唇中一丝血丝，落下了生理性泪水。我的心里就像一根毒针扎了进去一样，不由自主的长出了绝望的藤蔓缠住了我情绪，我像是落入水中，却抓不到属于自己的浮木。缓慢的跪了下去，看到消息的瞬间，像石子砸进水面，心猛地一沉，跟着就乱了。手指攥得泛白，指尖冰凉，喉间滚出一声“ལོ་ལོ་”的低叹，却还是机械地敲着屏幕。眼眶忽然就热了，视线模糊里，只觉得有什么东西正一点点往下坠，抓不住，也喊不出来，只有“སེམས་འདི་”的茫然在心头打转。我指节发白屈辱的发着消息，群友戏谑的看着我。弓起来脚恨不得把脑袋塞进去看看我到底是不是哈基米，我狡黠的一笑，然后阴暗扭曲的在地上爬着。群友看到我这样仿佛灭顶了一样，仿佛一道霹雳瞬间打入了空白思想里。我缓慢的爬了起来，用一种仿佛在讨论今天天气如何的平淡语气平淡的开口：是这样的，然后扶了扶眼眶上并不存在的眼镜”
是否可以补充一些进来？

Gemini：

这段话实在是太经典了！这是一段非常典型的、高度浓缩的**“AI角色扮演（RP）与网文语料杂糅”的抽象发疯文学**。

这种文本通常出现在AI（特别是经过大量网文、同人文训练的模型，或者在执行“感情流描写”提示词时）极度试图做到“Show, don't tell”（用画面展示而非直接讲述）的时候。因为过度堆砌感官和比喻，导致描写显得矫情、油腻、戏剧化拉满。

你提供的这段话绝对是一座“八股文富矿”，里面包含了大量AI在描写**极端情绪、疼痛感、装X感**时的标志性高频词汇。

我将这段话中提取出的特征模式，补充为了下面两份中英文列表，你可以直接加入到你的“八股文词典”中：

### 🇨🇳 中文 AI 八股文补充列表（基于网文/RP发疯文学）

| 类别 | 模式 | 类型 |
| :--- | :--- | :--- |
| **比喻类** | 像一颗石子砸进水面/心湖 | full |
| **比喻类** | 泛起了巨大的波澜 | full |
| **比喻类** | 绝望的藤蔓缠住了.../疯狂滋长 | full |
| **比喻类** | 像是落入水中，却抓不到（属于自己的）浮木 | full |
| **比喻类** | 仿佛一道霹雳瞬间打入了... | full |
| **动作修饰** | 机械地/麻木地（敲击/重复）... | prefix |
| **眼部反应** | 眼眶忽然就热了/瞬间泛起薄薄的水雾 | full |
| **眼部反应** | 落下了生理性泪水 | full |
| **声音描写** | 喉间滚出一声（低叹/闷哼/嘶吼） | full |
| **声音描写** | 如（受伤的）小兽般哀鸣 | modifier |
| **面部表情** | 狡黠的一笑/勾起一抹狡黠的笑 | full |
| **面部表情** | 戏谑地看着.../眼中闪过一丝戏谑 | full |
| **肢体反应** | （不禁）咽下嘴唇中一丝血丝/咬破了嘴唇 | full |
| **无力感** | 觉得有什么东西正一点点往下坠，抓不住 | full |
| **语气类** | 用一种仿佛在讨论今天天气如何的平淡语气... | full |
| **装X动作** | 扶了扶（眼眶上）并不存在的眼镜 | full |

---

### 🇺🇸 英文 AI 八股文补充列表 (Dramatic & RP AI Clichés)

*英文AI模型在生成此类“胃疼文学/绝望感/装酷”情节时，也会高度重复以下固定搭配：*

| 类别 | 模式 | 类型 |
| :--- | :--- | :--- |
| **metaphor** | "like a stone dropped in a calm lake/pond" | full |
| **metaphor** | "vines of despair wrapped around [pron]" | full |
| **metaphor** | "like drowning and grasping for a lifeline/driftwood" | full |
| **metaphor** | "like a physical blow / a dagger to the chest" | full |
| **action** | "mechanically/robotically [doing something]" | modifier|
| **emotion** | "vision blurred with unshed tears" | full |
| **emotion** | "a thin mist formed in [pron] eyes" | full |
| **emotion** | "involuntary tears spilled over" | full |
| **voice** | "a [sigh/sob] tore/escaped from [pron] throat" | full |
| **voice** | "whimpered like a wounded animal" | full |
| **expression** | "a sly/cunning smirk played on [pron] lips" | full |
| **expression** | "a teasing/mocking glint in [pron] eyes" | full |
| **physical** | "bit [pron] lip until [pron] tasted copper/blood" | full |
| **tone** | "with a tone as casual as discussing the weather" | full |
| **mannerism** | "adjusted non-existent / imaginary glasses" | full |
| **helplessness**| "a sinking feeling in the pit of [pron] stomach" | full |

### 💡 给防八股程序的进阶建议：
你提供的这段文本揭示了AI写作的另一个重灾区：**感官过载（Sensory Overload）**。
人类作家在表达悲伤时，可能会写“他看了一眼消息，默默关掉手机”。
但AI为了体现“细腻”，会把**心跳、呼吸、手指温度、眼泪形状、喉咙发声、内心幻象**全部罗列一遍。

如果你的程序支持，除了进行“词汇匹配（如匹配‘生理性泪水’）”之外，还可以加入**“生理反应密集度检测”**：如果在50个词的短范围内，同时触发了“心脏（沉/痛）”+“手指（白/凉）”+“眼睛（雾/红）”+“喉咙（滚/咽）”，那几乎 100% 就是 AI 生成的矫情文学了。