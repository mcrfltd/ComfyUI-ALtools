import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "Comfy.DynamicTextInputLoader",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "DynamicTextInputLoader") {

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                // 隱藏 json 傳輸欄位
                const jsonWidget = node.widgets.find(w => w.name === "text_list_json");
                if (jsonWidget) {
                    jsonWidget.type = "HIDDEN";
                }

                node.textWidgets = [];

                const serializeTexts = () => {
                    const values = node.textWidgets.map(w => w.value);
                    if (jsonWidget) jsonWidget.value = JSON.stringify(values);
                };

                const addTextInputWidget = (initialValue = "") => {
                    const index = node.textWidgets.length + 1;
                    const widget = node.addWidget("string", `text_${index}`, initialValue, (val) => {
                        serializeTexts();
                    });

                    node.textWidgets.push(widget);
                    serializeTexts();

                    node.setSize(node.computeSize());
                    node.setDirtyCanvas(true, true);
                };

                // 新增按鈕
                node.addWidget("button", "＋ Add Text", null, () => {
                    addTextInputWidget("");
                });

                // 初始化給予兩個框
                setTimeout(() => {
                    if (node.textWidgets.length === 0) {
                        addTextInputWidget("");
                        addTextInputWidget("");
                    }
                }, 50);

                // 讀取 Workflow 還原
                node.onConfigure = function(info) {
                    setTimeout(() => {
                        if (jsonWidget && jsonWidget.value) {
                            try {
                                const values = JSON.parse(jsonWidget.value);
                                node.textWidgets = [];
                                node.widgets = node.widgets.filter(w => w.name === "text_list_json" || w.name === "delimiter" || w.name === "＋ Add Text");
                                values.forEach(val => addTextInputWidget(val));
                            } catch(e) {}
                        }
                    }, 100);
                };

                return r;
            };
        }
    }
});
