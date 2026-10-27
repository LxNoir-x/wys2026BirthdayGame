#target photoshop

var sources = [
    "流星飞.psd",
    "剑圣.psd",
    "里雪.psd",
    "萧然.psd",
    "霍里.psd",
    "时差.psd",
    "子龙.psd"
];
var sourceDir = new Folder("D:/yuanshan/re/_materials/files/v2/部分关卡/关卡/关卡源文件");
var report = new File("D:/yuanshan/re/tools/v2_annotation_layers.txt");
report.encoding = "UTF-8";
report.open("w");

function writeLayers(layers, prefix) {
    for (var i = 0; i < layers.length; i++) {
        var layer = layers[i];
        report.writeln(prefix + layer.name + " | type=" + layer.typename + " | visible=" + layer.visible);
        if (layer.typename === "LayerSet") {
            writeLayers(layer.layers, prefix + "  ");
        }
    }
}

for (var i = 0; i < sources.length; i++) {
    var file = new File(sourceDir.fsName + "/" + sources[i]);
    var document = app.open(file);
    report.writeln("=== " + sources[i] + " ===");
    writeLayers(document.layers, "");
    report.writeln("");
    document.close(SaveOptions.DONOTSAVECHANGES);
}

report.close();
