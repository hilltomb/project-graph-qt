#!/bin/bash

# Check root
if [ $EUID -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

rm -rf /tmp/project-graph* /usr/local/bin/project-graph /usr/share/applications/project-graph.desktop /usr/share/icons/hicolor/64x64/apps/project-graph.png

echo "Download binary file"
curl -L -o /tmp/project-graph.zip https://nightly.link/LiRenTech/project-graph-qt/workflows/package/master/project-graph_linux.zip
if [ $? -ne 0 ]; then
    echo "Download failed"
    exit 1
fi

echo "Unzip binary file"
unzip -d /tmp/project-graph /tmp/project-graph.zip
if [ $? -ne 0 ]; then
    echo "Unzip failed"
    exit 1
fi

echo "Copy binary file to /usr/local/bin"
cp /tmp/project-graph/project-graph /usr/local/bin/project-graph
if [ $? -ne 0 ]; then
    echo "Copy failed"
    exit 1
fi

echo "Set execute permission"
chmod +x /usr/local/bin/project-graph
if [ $? -ne 0 ]; then
    echo "Set permission failed"
    exit 1
fi

echo "Download icon"
curl -L -o /usr/share/icons/hicolor/64x64/apps/project-graph.png https://raw.githubusercontent.com/LiRenTech/project-graph-qt/master/src/project_graph/assets/favicon.png
if [ $? -ne 0 ]; then
    echo "Download icon failed"
    exit 1
fi

echo "Create desktop file"
cat > /usr/share/applications/project-graph.desktop <<EOF
[Desktop Entry]
Name=Project Graph
Exec=project-graph
Icon=project-graph
Type=Application
Categories=Utility;
Comment=快速绘制各种节点图
GenericName=节点图绘制工具
EOF
if [ $? -ne 0 ]; then
    echo "Create desktop file failed"
    exit 1
fi

echo "Install finished!"
