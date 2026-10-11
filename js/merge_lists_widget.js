import { app } from "../../scripts/app.js";

/**
 * 「合并列表」输入端口按需显示扩展。
 *
 * 与「视频拼接」同款「删除/添加末尾端口」策略：
 * - 节点创建后只保留前 2 个输入端口（列表0、列表1）；
 * - 当末尾端口被连接时，自动追加下一个端口，依次类推，最多 9 个
 *   （与 Python 端 MAX_INPUTS 一致）；
 * - 断开末尾端口时自动回收；
 * - 加载含链接的工作流时，按已有链接恢复端口数量。
 *
 * 端口名/顺序与 Python 端 INPUT_TYPES 的 列表0 ~ 列表8 一一对应，
 * 增删只发生在末尾，保证端口序号与后端参数名始终对齐（合并顺序 = 端口顺序）。
 */

const MAX_INPUTS = 9; // 与 Python 端保持一致
const INPUT_SLOT = 1; // LiteGraph.INPUT

app.registerExtension({
  name: "YTmmi.MergeListsInputs",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "MergeListsNode") return;

    const computeVisibleCount = function (node) {
      let maxLinked = -1;
      for (let i = 0; i < node.inputs.length; i++) {
        if (node.inputs[i].link != null) maxLinked = i;
      }
      return Math.min(Math.max(2, maxLinked + 2), MAX_INPUTS);
    };

    const syncInputs = function (node) {
      if (!node.inputs) return;
      const target = computeVisibleCount(node);

      while (node.inputs.length > target) {
        const last = node.inputs[node.inputs.length - 1];
        if (last.link != null) break; // 绝不删除已连接的端口
        node.removeInput(node.inputs.length - 1);
      }
      while (node.inputs.length < target) {
        node.addInput(`列表${node.inputs.length}`, "LIST");
      }
      node.setDirtyCanvas?.(true, true);
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = originalOnNodeCreated?.apply(this, arguments);
      const sync = () => syncInputs(this);
      sync();
      setTimeout(sync, 0);
      setTimeout(sync, 100);
      setTimeout(sync, 500);
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
  },
});
