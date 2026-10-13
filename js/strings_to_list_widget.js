import { app } from "../../scripts/app.js";

/**
 * 「字符串到列表」输入端口按需显示扩展。
 *
 * 端口数量在**工作流构建阶段（运行前）**就由连线决定，与本次运行结果无关：
 * - 节点创建后只保留前 MIN_INPUTS 个输入端口（字符串0、字符串1）；
 * - 当**末尾端口被连接**时自动追加下一个端口（字符串2、字符串3……），
 *   即「连一个、出一个」，最多 MAX_INPUTS（20，与 Python 端一致）；
 * - 断开末尾端口时自动回收该端口；
 * - 加载含链接的工作流时按已有链接恢复端口数量。
 *
 * 端口名/顺序与 Python 端 INPUT_TYPES 的 字符串0 ~ 字符串19 一一对应，
 * 增删只发生在末尾，保证端口序号与后端参数名始终对齐。
 *
 * 节点高度取最小值：
 * - Python 端一次性声明了 20 个输入，节点创建时会被撑成 20 行高；
 *   而 LiteGraph 的 removeInput() 并不会把高度缩回，必须显式收敛到
 *   「当前端口数所需的最小高度」，否则节点会一直留着一大片空白。
 * - 收敛用**直接赋值 node.size**（与官方 autogrow 同款）而非 setSize()，
 *   这样不会触发 onResize，从而能与「用户手动拖拽高度」区分开；
 * - 用户手动拖大过高度时尊重该高度（会话内拖拽由 onResize 识别，
 *   保存后载入则比较保存高度与当前端口数所需的最小高度）。
 */

const MAX_INPUTS = 20; // 与 Python 端 MAX_INPUTS 保持一致
const MIN_INPUTS = 2;
const INPUT_SLOT = 1; // LiteGraph.INPUT

app.registerExtension({
  name: "YTmmi.StringsToListInputs",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "StringsToListNode") return;

    // 该输入端口是否已连线。
    // 优先用非废弃 API（isInputConnected），避免读取 input.link 触发弃用告警。
    const isLinked = function (node, index) {
      if (!node.inputs?.[index]) return false;
      if (node.graph && typeof node.isInputConnected === "function") {
        return node.isInputConnected(index);
      }
      return node.inputs[index].link != null;
    };

    // 目标端口数：至少 MIN_INPUTS；末尾端口已连接时再多留 1 个空端口供继续连接
    const computeVisibleCount = function (node) {
      let lastLinked = -1;
      const count = node.inputs?.length ?? 0;
      for (let i = 0; i < count; i++) {
        if (isLinked(node, i)) lastLinked = i;
      }
      return Math.min(Math.max(MIN_INPUTS, lastLinked + 2), MAX_INPUTS);
    };

    // 当前端口数所需的最小高度（LiteGraph computeSize 不传参即得最小尺寸）
    const minimalHeight = function (node) {
      const computed = node.computeSize?.();
      return computed ? Math.max(1, computed[1]) : null;
    };

    // 把节点高度收敛到最小值（用户手动调整过则跳过）
    const applyMinimalHeight = function (node) {
      if (node.__ytmmiUserResized) return;
      const targetHeight = minimalHeight(node);
      if (targetHeight === null) return;
      if (Math.abs((node.size?.[1] ?? 0) - targetHeight) < 0.5) return;
      // 直接赋值而非 setSize()：不触发 onResize，避免被误判为用户手动调整
      node.size = [node.size?.[0] ?? node.computeSize?.()[0] ?? 0, targetHeight];
    };

    // 只增删末尾端口，保证序号对齐。
    // convergeHeight=false 用于「载入工作流」时先摆好端口、再由调用方判定高度。
    const syncInputs = function (node, convergeHeight = true) {
      if (!node.inputs) return;
      const target = computeVisibleCount(node);

      // addInput() 内部会 expandToFitContent() → setSize() → onResize()，
      // 用标记表明这是端口同步引起的尺寸变化，不算用户手动调整。
      node.__ytmmiAutoSizing = true;
      try {
        while (node.inputs.length > target) {
          // 绝不删除已连接的端口
          if (isLinked(node, node.inputs.length - 1)) break;
          node.removeInput(node.inputs.length - 1);
        }
        while (node.inputs.length < target) {
          node.addInput(`字符串${node.inputs.length}`, "STRING");
        }
      } finally {
        node.__ytmmiAutoSizing = false;
      }

      if (convergeHeight) applyMinimalHeight(node);
      node.setDirtyCanvas?.(true, true);
    };

    // 用户手动拖拽高度后不再自动收敛
    const originalOnResize = nodeType.prototype.onResize;
    nodeType.prototype.onResize = function () {
      const r = originalOnResize?.apply(this, arguments);
      if (!this.__ytmmiAutoSizing) this.__ytmmiUserResized = true;
      return r;
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      // 构造期的初始尺寸（按 20 个端口算出）不算用户调整，重置标记
      this.__ytmmiUserResized = false;
      const r = originalOnNodeCreated?.apply(this, arguments);
      const sync = () => syncInputs(this);
      // 多个时机刷新，兼容不同前端版本的端口填充时机
      sync();
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      setTimeout(sync, 500);
      return r;
    };

    const originalOnConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const r = originalOnConfigure?.apply(this, arguments);
      // 先按已有链接摆好端口（暂不收敛高度），再比较「保存高度」与
      // 「当前端口数所需的最小高度」：明显更高说明用户当时手动拖大过，尊重该高度。
      const savedHeight = this.size?.[1] ?? 0;
      this.__ytmmiUserResized = false;
      syncInputs(this, false);
      const targetHeight = minimalHeight(this);
      if (targetHeight !== null && savedHeight > targetHeight + 1) {
        this.__ytmmiUserResized = true;
      }
      applyMinimalHeight(this);
      // 兼容不同前端版本的端口填充时机，稍后再同步一次
      const sync = () => syncInputs(this);
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      return r;
    };

    // 整图载入完成后所有连线都已就位，再做一次收敛（保证端口数量与链接一致）
    const originalOnAfterGraphConfigured = nodeType.prototype.onAfterGraphConfigured;
    nodeType.prototype.onAfterGraphConfigured = function () {
      const r = originalOnAfterGraphConfigured?.apply(this, arguments);
      syncInputs(this);
      return r;
    };

    const originalOnConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function (type, slot, change, linkInfo) {
      const r = originalOnConnectionsChange?.apply(this, arguments);
      // 输入端口连线变化即在工作流构建阶段同步端口数量（不依赖运行结果）
      if (type === INPUT_SLOT) {
        syncInputs(this);
      }
      return r;
    };
  },
});
