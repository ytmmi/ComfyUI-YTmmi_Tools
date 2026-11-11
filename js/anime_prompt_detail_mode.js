import { app } from "../../scripts/app.js";

/**
 * 「随机提示词(Anime)-beta」节点：按「详细程度」动态显示 / 隐藏槽位控件。
 *
 * 后端一直保留全部 18 个槽位控件（否则旧工作流的 widgets_values 会错位），
 * 但在「简略（8 槽位）」模式下只使用 8 个槽位，其余 10 个槽位对用户没有意义，
 * 因此在前端把它们隐藏，让「详细程度」开关真正可见地生效。
 *
 * 隐藏方式与 ComfyUI 官方扩展一致（frontend 里的
 * `for (let t of e.widgets ?? []) ... t.hidden = true`）：
 * 同时写 `widget.hidden` 与 `widget.options.hidden`。
 * 前端 `deriveWidgetVisibility()` 读 `hidden ?? options.hidden`，
 * `applyLegacyHiddenWrite()` 把它写进 `suppression.byExtension`，
 * `isWidgetRowVisible()` / `occupiesCanvasRow()` 会据此跳过该行（不占位、不绘制）。
 *
 * 简略模式保留的 8 个槽位：质量 / 画师 / 服装 / 姿势 / 场景 / 光影 / 镜头 / 构图。
 * 被隐藏的 10 个槽位：人数 / 发型 / 面部 / 表情 / 体型 / 配饰 / 天气 / 道具 / 文本描述 / 负向。
 */
const NODE_CLASS = "AnimeRandomPromptNode";
const MODE_WIDGET = "详细程度";
const BRIEF_MODE_PREFIX = "简略";

// 简略模式下隐藏的槽位控件名（与后端 BRIEF_SLOTS 互补）
const HIDDEN_IN_BRIEF = [
  "人数",
  "发型",
  "面部",
  "表情",
  "体型",
  "配饰",
  "天气",
  "道具",
  "文本描述",
  "负向",
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

function currentMode(node) {
  const mode = findWidget(node, MODE_WIDGET);
  if (!mode) return "";
  return typeof mode.value === "string" ? mode.value.trim() : "";
}

/** 依据当前模式刷新 10 个非简略槽位控件的可见性。 */
function syncNode(node) {
  if (!node || !node.widgets) return;
  const brief = currentMode(node).startsWith(BRIEF_MODE_PREFIX);
  for (const name of HIDDEN_IN_BRIEF) {
    setVisible(findWidget(node, name), !brief);
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

/** 给「详细程度」控件的 callback 套一层：用户切换后立即刷新可见性。 */
function installNode(node) {
  if (!node || node.__ytmmiAnimeDetailModeInstalled) return;
  node.__ytmmiAnimeDetailModeInstalled = true;

  const mode = findWidget(node, MODE_WIDGET);
  if (mode) {
    const originalCallback = mode.callback;
    mode.callback = function () {
      const result = originalCallback?.apply(this, arguments);
      syncNode(node);
      return result;
    };
  }

  // 部分交互路径（例如画布上的下拉点击）只触发 node.onWidgetChanged，
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

  node.__ytmmiAnimeDetailMode = currentMode(node);
  syncNode(node);
}

app.registerExtension({
  name: "YTmmi.AnimePromptDetailMode",
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
// 只在「详细程度」的值发生变化时才重新同步，避免每 300ms 重绘画布。
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
    if (!node.__ytmmiAnimeDetailModeInstalled) continue;
    const mode = currentMode(node);
    if (mode !== node.__ytmmiAnimeDetailMode) {
      node.__ytmmiAnimeDetailMode = mode;
      syncNode(node);
    }
  }
}

setInterval(scanGraph, 300);
