import { app } from "../../scripts/app.js";

/**
 * 「自定义LLM」节点：按「高级」开关动态显示 / 隐藏高级参数控件。
 *
 * 后端一直保留全部控件（否则旧工作流的 widgets_values 会按位置回填错位），
 * 「高级」是追加在 optional 末尾的一个 BOOLEAN 控件，默认关闭，只用来控制
 * 前端显隐，不参与请求体构造（chat() 里所有参数照常读入，行为逐字不变）。
 *
 * 「高级」关闭时保留可见：required 8 项（API密钥/接口地址/选择模型/选择密钥/
 * 系统提示词/提示词/温度/最大token数）+「联网搜索」+「种子」（含官方
 * control_after_generate 下拉）+ 图片输入端口（是端口不是 widget，不受影响）。
 * 打开「高级」后显示全部参数。
 *
 * 隐藏方式与「随机提示词(Anime)」的「详细程度」开关、以及 ComfyUI 官方扩展
 * 一致：同时写 `widget.hidden` 与 `widget.options.hidden`。
 * 前端 `deriveWidgetVisibility()` 读 `hidden ?? options.hidden`，
 * `applyLegacyHiddenWrite()` 把它写进 `suppression.byExtension`，
 * `isWidgetRowVisible()` / `occupiesCanvasRow()` 据此跳过该行（不占位、不绘制）。
 *
 * 切换事件接两处：`widget.callback` 与 `node.onWidgetChanged`（画布上的
 * 勾选/下拉点击只触发后者）；`onConfigure` 里用 setTimeout(…, 0) 在官方回填
 * 控件值之后重同步；再挂 `beforeRegisterNodeDef` 包装 `onNodeCreated` +
 * `nodeCreated` + `loadedGraphNode`，并用 setInterval 兜底扫描。
 */
const NODE_CLASS = "CustomLLMNode";
const MODE_WIDGET = "高级";

// 「高级」关闭时隐藏的控件名（optional 中除「高级」/「联网搜索」/「种子」外
// 的全部 widget；图片0~图片8 是 IMAGE 输入端口、skills 是 forceInput 端口，
// 若某环境里它们没有对应 widget，findWidget 会返回 undefined，直接跳过）。
const HIDDEN_WHEN_BASIC = [
  "skills",
  "skills最大轮数",
  "skills单次读取上限",
  "skills累计上限",
  "核采样（top_p）",
  "输出格式",
  "频率惩罚",
  "存在惩罚",
  "候选数量",
  "top_k",
  "推理强度",
  "超时秒数",
  "空输出重试次数",
  "启用多轮对话",
  "最大会话轮数",
  "图片最长边",
  "图片细节",
];

function findWidget(node, name) {
  return node.widgets?.find((item) => item.name === name);
}

function setVisible(item, visible) {
  if (!item) return;
  item.hidden = !visible;
  if (!item.options) item.options = {};
  item.options.hidden = !visible;
}

/** BOOLEAN 控件的值可能是布尔、字符串或数字，统一判断「高级」是否打开。 */
function isAdvancedOn(node) {
  const mode = findWidget(node, MODE_WIDGET);
  if (!mode) return false;
  const value = mode.value;
  return value === true || value === "true" || value === 1 || value === "1";
}

/** 依据「高级」开关刷新 17 个高级参数控件的可见性。 */
function syncNode(node) {
  if (!node || !node.widgets) return;
  const advanced = isAdvancedOn(node);
  for (const name of HIDDEN_WHEN_BASIC) {
    setVisible(findWidget(node, name), advanced);
  }
  // 收敛节点高度：隐藏的控件不再占行。
  // 只在算出的高度更小时才 setSize，避免某些前端实现把节点撑大。
  try {
    if (typeof node.computeSize === "function" && typeof node.setSize === "function") {
      const size = node.computeSize();
      const height = Array.isArray(size) ? size[1] : undefined;
      if (typeof height === "number" && !Number.isNaN(height) && height < node.size?.[1]) {
        node.setSize([node.size?.[0] ?? size[0], height]);
      }
    }
  } catch (err) {
    // 尺寸计算失败不影响控件可见性，忽略即可
  }
  node.setDirtyCanvas?.(true, true);
}

/** 给「高级」控件的 callback 套一层：用户切换后立即刷新可见性。 */
function installNode(node) {
  if (!node || node.__ytmmiCustomLLMAdvancedInstalled) return;
  node.__ytmmiCustomLLMAdvancedInstalled = true;

  const mode = findWidget(node, MODE_WIDGET);
  if (mode) {
    const originalCallback = mode.callback;
    mode.callback = function () {
      const result = originalCallback?.apply(this, arguments);
      syncNode(node);
      return result;
    };
  }

  // 部分交互路径（例如画布上的勾选点击）只触发 node.onWidgetChanged，
  // 不触发 widget.callback，因此两处都要接。
  const originalOnWidgetChanged = node.onWidgetChanged;
  node.onWidgetChanged = function (name, value, oldValue, widget) {
    const result = originalOnWidgetChanged?.apply(this, arguments);
    if (name === MODE_WIDGET || widget?.name === MODE_WIDGET) {
      syncNode(node);
    }
    return result;
  };

  // 载入工作流时官方会回填控件值，回填完成后需要再同步一次
  const originalOnConfigure = node.onConfigure;
  node.onConfigure = function () {
    const result = originalOnConfigure?.apply(this, arguments);
    setTimeout(() => syncNode(node), 0);
    return result;
  };

  node.__ytmmiCustomLLMAdvancedState = isAdvancedOn(node);
  syncNode(node);
}

app.registerExtension({
  name: "YTmmi.CustomLLMAdvancedMode",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== NODE_CLASS) return;
    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = originalOnNodeCreated?.apply(this, arguments);
      installNode(this);
      return result;
    };
  },
  nodeCreated(node) {
    installNode(node);
  },
  loadedGraphNode(node) {
    installNode(node);
  },
});

// 兜底：扫描已存在的节点（扩展加载较晚、节点先创建的情况），
// 只在「高级」的值发生变化时才重新同步，避免每 300ms 重绘画布。
function nodeClassOf(node) {
  // 官方扩展用 node.constructor.comfyClass 判断节点类型；
  // 部分实现把 comfyClass 只挂在原型上，这里两种都兼容。
  return node?.constructor?.comfyClass || node?.comfyClass || "";
}

function scanGraph() {
  const nodes = app.graph?._nodes;
  if (!Array.isArray(nodes)) return;
  for (const node of nodes) {
    if (nodeClassOf(node) !== NODE_CLASS) continue;
    installNode(node);
    if (!node.__ytmmiCustomLLMAdvancedInstalled) continue;
    const state = isAdvancedOn(node);
    if (state !== node.__ytmmiCustomLLMAdvancedState) {
      node.__ytmmiCustomLLMAdvancedState = state;
      syncNode(node);
    }
  }
}

setInterval(scanGraph, 300);
