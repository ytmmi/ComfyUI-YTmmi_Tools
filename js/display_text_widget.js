import { app } from "../../scripts/app.js";

/**
 * 展示文本节点前端扩展。
 *
 * Python 端在 show() 中返回 {"ui": {"文本": [展示文本]}, "result": ...}，
 * 前端在 onExecuted 中读取该值并回填到节点上的「文本」控件，实现文本展示。
 */
app.registerExtension({
  name: "YTmmi.DisplayText",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "DisplayTextNode") return;

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
