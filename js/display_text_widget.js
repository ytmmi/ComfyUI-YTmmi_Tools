import { app } from "../../scripts/app.js";

/**
 * 展示文本（多重）节点前端扩展。
 *
 * 动态输入端口：
 * - 新版 ComfyUI 前端（Vue GraphView）中，输入端口总会渲染圆点，无法通过
 *   清空 input.name 隐藏端口。因此改用「删除/添加末尾端口」策略：
 * - 节点创建后默认只保留「输入0」（1 个输入口）；
 * - 当末尾输入口被连接（如 输入0）时，自动添加下一个输入口（输入1），
 *   依次类推，最多 输入8（与 Python 端 MAX_INPUTS = 9 一致）；
 * - 断开末尾输入口时自动回收该输入口；
 * - 加载含链接的工作流时，会根据已有链接恢复对应输入口。
 *
 * 端口名/顺序与 Python 端 INPUT_TYPES 的 输入0 ~ 输入8 一一对应，
 * 删除/添加仅发生在端口数组末尾，保证输入口序号与后端参数名始终对齐。
 *
 * 展示回填：
 * - Python 端在 show() 中返回 {"ui": {"文本": [合并展示文本]}, "result": ...}，
 *   前端在 onExecuted 中读取该值回填到「文本」控件。
 * - 「文本」控件设为只读（read_only + serialize=false，官方 PreviewText 同款），
 *   避免新版前端把 STRING 文本框当成可连接端口误用。
 */

const MAX_INPUTS = 9; // 与 Python 端 MAX_INPUTS 保持一致
const INPUT_SLOT = 1; // LiteGraph.INPUT

app.registerExtension({
  name: "YTmmi.DisplayText",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "DisplayTextNode") return;

    // 计算当前应显示的端口数量：
    // 默认 1 个（输入0）；最后一个有链接的输入口后面再保留 1 个空输入口供继续连接
    const computeVisibleCount = function (node) {
      let maxLinked = -1;
      for (let i = 0; i < node.inputs.length; i++) {
        if (node.inputs[i].link != null) {
          maxLinked = i;
        }
      }
      return Math.min(Math.max(1, maxLinked + 2), MAX_INPUTS);
    };

    // 只增删端口数组末尾的无链接端口，保证序号对齐
    const syncInputs = function (node) {
      if (!node.inputs) return;
      const target = computeVisibleCount(node);

      // 删除末尾多余端口（绝不删除有链接的端口，且至少保留 1 个）
      while (node.inputs.length > target) {
        const last = node.inputs[node.inputs.length - 1];
        if (last.link != null) break;
        node.removeInput(node.inputs.length - 1);
      }
      // 追加缺失端口（只加到末尾，序号 = 当前长度）
      while (node.inputs.length < target) {
        node.addInput(`输入${node.inputs.length}`, "*");
      }
      node.setDirtyCanvas?.(true, true);
    };

    // 展示控件设为只读，避免用户误当文本输入使用
    const makeReadOnly = function (widget) {
      if (!widget) return;
      widget.options.read_only = true;
      widget.options.serialize = false;
      if (widget.element) {
        widget.element.readOnly = true;
      }
      widget.serialize = false;
    };

    // 新版前端可能把「文本」STRING 展示控件转成可连接端口（含旧工作流中已保存的端口），
    // 未连接时执行会报 Missing connection。主动删除该输入端口，强制保持为纯展示控件。
    const removeTextPort = function (node) {
      if (!node.inputs) return;
      for (let i = node.inputs.length - 1; i >= 0; i--) {
        if (node.inputs[i].name === "文本") {
          node.removeInput(i);
        }
      }
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = originalOnNodeCreated?.apply(this, arguments);
      makeReadOnly(this.widgets?.find((w) => w.name === "文本"));
      // 节点创建/加载后多次刷新，兼容不同前端版本的输入填充时机
      const sync = () => {
        syncInputs(this);
        removeTextPort(this);
      };
      sync();
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      setTimeout(sync, 500);
      return r;
    };

    // 加载工作流（configure）后端口会按保存内容恢复，需再次删除「文本」端口
    const originalOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const r = originalOnConfigure?.apply(this, arguments);
      removeTextPort(this);
      return r;
    };

    const originalOnConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function (type, slot, change, linkInfo) {
      const r = originalOnConnectionsChange?.apply(this, arguments);
      if (type === INPUT_SLOT) {
        syncInputs(this);
      }
      return r;
    };

    const originalOnExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function () {
      originalOnExecuted?.apply(this, arguments);

      const execData = arguments[0];
      if (!execData) return;

      const textValue = execData["文本"]?.[0];
      if (textValue === undefined) return;

      const textWidget = this.widgets?.find((w) => w.name === "文本");
      if (textWidget && textWidget.value !== textValue) {
        textWidget.value = textValue;
        this.setDirtyCanvas(true);
      }
    };
  },
});
