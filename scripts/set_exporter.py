""" this script is an help to export all the child of a selected layer in krita
https://krita.org/ which is the free software used to paint the graphics and
animations.
It does export a json containing the level data as well.
"""

import krita
from PyQt5 import QtCore, QtGui
import os
import json


SRGB_PROFILE = "sRGB-elle-V2-srgbtrc.icc"
ROOT = "C:/perso/drunk-paranoia/drunkparanoia"
LEVEL_FOLDER = "resources/sets/saloon"
IMAGES_FOLDER = f"{ROOT}/{LEVEL_FOLDER}"
LEVEL_FILE = "resources/scenes/saloon.json"


def check_name_clash(nodes):
    names = [n.name() for n in nodes]
    if len(names) == len(set(names)):
        return
    clashes = [name for name in names if names.count(name) > 1]
    raise ValueError(f"multiple name as the same name: {set(clashes)}")


def node_bounds(node, document):
    rect = node.bounds()
    width, height = document.width(), document.height()
    rect.setLeft(max(rect.left(), 0))
    rect.setTop(max(rect.top(), 0))
    rect.setRight(rect.right() if rect.right() <= width else width)
    rect.setBottom(rect.bottom() if rect.bottom() <= height else height)
    return rect.x(), rect.y(), rect.width(), rect.height()


def node_to_qimage(node, document):
    """
    Returns an QImage 8-bit sRGB
    """
    x, y, w, h = node_bounds(node, document)

    canvas = QtGui.QImage(QtCore.QSize(w, h), QtGui.QImage.Format_ARGB32)
    canvas.fill(QtGui.QColor(0, 255, 0))

    is_srgb = (
        node.colorModel() == "RGBA" and
        node.colorDepth() == "U8" and
        node.colorProfile().lower() == SRGB_PROFILE.lower())

    if is_srgb:
        pixel_data = node.projectionPixelData(x, y, w, h).data()
    else:
        temp_node = node.duplicate()
        temp_node.setColorSpace("RGBA", "U8", SRGB_PROFILE)
        pixel_data = temp_node.projectionPixelData(x, y, w, h).data()

    image = QtGui.QImage(pixel_data, w, h, QtGui.QImage.Format_ARGB32)
    painter = QtGui.QPainter(canvas)
    painter.drawImage(0, 0, image)

    return canvas


def update_or_layer(filename, data, node):
    bounds = node_bounds(node, document)
    for element in data['elements']:
        if element['file'] == filename:
            element["position"] = bounds
            return
    x = bounds[0] + (bounds[2] / 2)
    y = bounds[1] + bounds[3]
    element = {
        "type": "prop",
        "file": filename,
        "position": bounds[:2],
        "center": [x, y],
        "box": None}

    data['elements'].append(element)
    return element


json_filename = f'{ROOT}/{LEVEL_FILE}'
with open(json_filename, "r") as f:
    data = json.load(f)


soft = krita.Krita()
document = soft.activeDocument()
nodes = document.activeNode().childNodes()
check_name_clash(nodes)
for node in nodes:
    if not node.visible():
        continue
    filename = node.name() + '.png'
    path = os.path.join(IMAGES_FOLDER, filename)
    image = node_to_qimage(node, document)
    image.save(path, "PNG")
    file = os.path.join(LEVEL_FOLDER, filename).replace("\\", "/")
    update_or_layer(file, data, node)


with open(json_filename, "w") as f:
    json.dump(data, f, indent=4)
