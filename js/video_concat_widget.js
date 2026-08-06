import { app } from "../../scripts/app.js";

/**
 * 视频拼接节点动态输入扩展。
 *
 * 新版 ComfyUI 前端（Vue GraphView）中，输入端口总会渲染圆点，无法通过
 * 清空 input.name 隐藏端口。因此这里改用「删除/添加端口」策略：
 * - 节点创建后只保留前 2 个视频输入接口（视频0、视频1）；
 * - 当末尾接口被连接（如 视频1）时，自动添加下一个接口（视频2），
 *   依次类推，最多 视频9（与 Python 端 MAX_INPUTS 一致）；
 * - 断开末尾接口时自动回收该接口；
 * - 加载含链接的工作流时，会根据已有链接恢复对应接口。
 *
 * 端口名/顺序与 Python 端 INPUT_TYPES 的 视频0 ~ 视频9 一一对应，
 * 删除/添加仅发生在端口数组末尾，保证接口序号与后端参数名始终对齐。
 */

const MAX_INPUTS = 10; // 与 Python 端保持一致
const INPUT_SLOT = 1; // LiteGraph.INPUT

app.registerExtension({
  name: "YTmmi.VideoConcatInputs",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "VideoConcatNode") return;

    // 计算当前应显示的端口数量：
    // 至少 2 个；最后一个有链接的接口后面再保留 1 个空接口供继续连接
    const computeVisibleCount = function (node) {
      let maxLinked = -1;
      for (let i = 0; i < node.inputs.length; i++) {
        if (node.inputs[i].link != null) {
          maxLinked = i;
        }
      }
      return Math.min(Math.max(2, maxLinked + 2), MAX_INPUTS);
    };

    // 只增删端口数组末尾的无链接端口，保证序号对齐
    const syncInputs = function (node) {
      if (!node.inputs) return;
      const target = computeVisibleCount(node);

      // 删除末尾多余端口（绝不删除有链接的端口，且至少保留 2 个）
      while (node.inputs.length > target) {
        const last = node.inputs[node.inputs.length - 1];
        if (last.link != null) break;
        node.removeInput(node.inputs.length - 1);
      }
      // 追加缺失端口（只加到末尾，序号 = 当前长度）
      while (node.inputs.length < target) {
        node.addInput(`视频${node.inputs.length}`, "VIDEO");
      }
      node.setDirtyCanvas?.(true, true);
    };

    const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = originalOnNodeCreated?.apply(this, arguments);
      // 节点创建/加载后多次刷新，兼容不同前端版本的输入填充时机
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
