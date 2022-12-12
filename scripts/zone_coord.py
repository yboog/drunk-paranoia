import json
from PySide6 import QtWidgets, QtCore, QtGui


def get_stair_line(rect, inclination):
    mult = rect.width()
    x = rect.left()
    y = rect.center().y() - (mult * (inclination / 2))
    p1 = QtCore.QPointF(x, y)
    x = rect.right()
    y = rect.center().y() - (mult * (-inclination / 2))
    p2 = QtCore.QPointF(x, y)
    line = QtCore.QLineF(p1, p2)
    offset = rect.center().y() - line.center().y()
    line.setP1(QtCore.QPointF(rect.left(), p1.y() + offset))
    line.setP2(QtCore.QPointF(rect.right(), p2.y() + offset))
    return line


class StairModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['stairs'])

    def columnCount(self, *_):
        return 2

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation != QtCore.Qt.Horizontal:
            return
        return ('Zone', 'Inclination')[section]

    def setData(self, index, value, role):
        try:
            data = json.loads(value)
        except ValueError:
            return False
        if index.column() == 0:
            if not is_zone(data):
                return False
            self.model.data['stairs'][index.row()]['zone'] = data
            self.changed.emit()
            return True
        if index.column() == 1:
            if not isinstance(value, (int, float)):
                return False
            self.model.data['stairs'][index.row()]['inclination'] = float(data)
            self.changed.emit()
            return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        row, col = index.row(), index.column()
        stair = self.model.data['stairs'][row]
        if col == 0:
            return str(stair['zone'])
        if col == 1:
            return str(stair['inclination'])


class InteractionModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['interactions'])

    def columnCount(self, *_):
        return 4

    def flags(self, index):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        row, col = index.row(), index.column()
        if col == 0:
            if value not in ['poker', 'piano', 'bet', 'rob', 'balcony']:
                return False
            self.model.data['interactions'][row]['action'] = value
            self.changed.emit()
            return True
        elif col == 2:
            try:
                data = json.loads(value)
                if not is_zone(data):
                    raise TypeError()
                self.model.data['interactions'][row]['zone'] = data
                self.changed.emit()
                return True
            except TypeError:
                return False
        elif col == 1:
            try:
                data = [v.strip(" ") for v in value.strip('[]').split(',')]
                data = [
                    int(data[0]) if data[0] != 'None' else None,
                    int(data[1]) if data[1] != 'None' else None]
                self.model.data['interactions'][row]['target'] = data
                self.changed.emit()
                return True
            except BaseException as e:
                print(e)
                return False
        elif col == 3:
            directions = ['left', 'right', 'up', 'down']
            if value not in directions:
                return False
            self.model.data['interactions'][row]['direction'] = value
            self.changed.emit()
            return True

    def headerData(self, section, orientation, role):
        if orientation != QtCore.Qt.Horizontal or role != QtCore.Qt.DisplayRole:
            return
        return ["Action", "Target", "Zone", "Direction"][section]

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        interaction = self.model.data['interactions'][index.row()]
        k = ["action", "target", "zone", "direction"][index.column()]
        return str(interaction[k])


def is_zone(data):
    return False if len(data) != 4 else all(isinstance(n, int) for n in data)


def is_point(data):
    if len(data) != 2:
        return False
    return all(isinstance(n, (int, float)) for n in data)


class PopspotsModel(QtCore.QAbstractListModel):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return len(self.model.data['popspots'])

    def data(self, index, role):
        if not index.isValid():
            return

        if role == QtCore.Qt.DisplayRole:
            return str(self.model.data['popspots'][index.row()])


class WallsModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, *_):
        return (
            len(self.model.data['no_go_zones']) +
            len(self.model.data['walls']))

    def columnCount(self, *_):
        return 2

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, data, role):
        try:
            data = json.loads(data)
        except TypeError:
            return False
        if self.type(index.row()) == 'rectangle':
            if not is_zone(data):
                return False
            self.model.data['no_go_zones'][index.row()] = data
            self.changed.emit()
            return True
        if len(data) < 3:
            return False
        if not all(len(p) == 2 for p in data):
            return False
        if not all(isinstance(n, int) for p in data for n in p):
            return False
        row = index.row() - (len(self.model.data['no_go_zones']))
        self.model.data['walls'][row] = data
        self.changed.emit()
        return True

    def type(self, row):
        zones = self.model.data['no_go_zones']
        return 'rectangle' if row < len(zones) else 'polygon'

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        type_ = self.type(row)
        if col == 0:
            return type_
        item = (self.model.data['no_go_zones'] + self.model.data['walls'])[row]
        return str(item)


class LevelCanvasModel:
    def __init__(self, gameroot, data):
        self.data = data
        self.backgrounds = []

        for background in data['backgrounds']:
            img = QtGui.QImage(f'{gameroot}/{background["file"]}')
            self.backgrounds.append(img)

        self.walls = True
        self.popspots = True
        self.interactions = True
        self.props = True
        self.stairs = True
        self.targets = True
        self.selected_target = None

    def size(self):
        w = max(b.size().width() for b in self.backgrounds)
        h = max(b.size().height() for b in self.backgrounds)
        return QtCore.QSize(w, h)


class LevelCanvas(QtWidgets.QWidget):
    rect_drawn = QtCore.Signal(object)
    point_set = QtCore.Signal(object)
    polygon_drawn = QtCore.Signal(object)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setFixedSize(self.sizeHint())
        self.rect_ = None
        self.point = None
        self.polygon = None
        self.mode = 'None'

    def sizeHint(self):
        return self.model.size()

    def mousePressEvent(self, event):
        if self.mode == 'None':
            return
        if self.mode == 'rectangle':
            self.polygon = None
            self.point = None
            self.rect_ = QtCore.QRect(
                event.position().toPoint(),
                event.position().toPoint())
        elif self.mode == 'point':
            self.rect_ = None
            self.point = None
            self.point = event.position().toPoint()
        elif self.mode == 'polygon' and not self.polygon:
            self.polygon = QtGui.QPolygon([event.position().toPoint()])
            self.point = None
            self.rect_ = None
        elif self.mode == 'polygon':
            self.polygon << event.position().toPoint()
        self.repaint()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return and self.polygon:
            self.polygon_drawn.emit(self.polygon)
            self.polygon = None
            self.repaint()

    def mouseMoveEvent(self, event):
        if self.mode == 'point':
            self.point = event.position().toPoint()
        elif self.mode == 'rectangle':
            self.rect_.setBottomRight(event.position().toPoint())
        elif self.mode == 'polygon':
            self.polygon[-1] = event.position().toPoint()
        self.repaint()

    def mouseReleaseEvent(self, event):
        if self.mode == 'point':
            self.point_set.emit(self.point)
        elif self.mode == 'rectangle':
            self.rect_drawn.emit(self.rect_)
        self.point = None
        self.rect_ = None
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        positions = [bg['position'] for bg in self.model.data['backgrounds']]
        for pos, image in zip(positions, self.model.backgrounds):
            painter.drawImage(QtCore.QPoint(*pos), image)
        if self.rect_ and self.mode == 'rectangle':
            painter.setPen(QtCore.Qt.white)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(self.rect_)
        elif self.point and self.mode == 'point':
            painter.setPen(QtCore.Qt.red)
            painter.setBrush(QtCore.Qt.red)
            painter.drawEllipse(self.point, 2, 2)
        elif self.polygon and self.mode == 'polygon':
            painter.setPen(QtCore.Qt.yellow)
            color = QtGui.QColor(QtCore.Qt.yellow)
            color.setAlpha(100)
            painter.drawPolygon(self.polygon)
        if self.model.popspots:
            painter.setPen(QtCore.Qt.yellow)
            painter.setBrush(QtCore.Qt.yellow)
            for x, y in self.model.data['popspots']:
                painter.drawEllipse(x, y, 2, 2)
        if self.model.walls:
            painter.setPen(QtCore.Qt.red)
            color = QtGui.QColor(QtCore.Qt.red)
            color.setAlpha(50)
            painter.setBrush(color)
            for rect in self.model.data['no_go_zones']:
                painter.drawRect(*rect)
            for polygon in self.model.data['walls']:
                polygon = QtGui.QPolygon([QtCore.QPoint(*p) for p in polygon])
                painter.drawPolygon(polygon)
        if self.model.stairs:
            for stair in self.model.data['stairs']:
                color = QtGui.QColor("#DEABDE")
                painter.setPen(color)
                color.setAlpha(50)
                painter.setBrush(color)
                rect = QtCore.QRect(*stair['zone'])
                painter.drawRect(rect)
                painter.setPen(QtCore.Qt.white)
                line = get_stair_line(rect, stair['inclination'])
                painter.drawLine(line)
        if self.model.targets:
            for i, origin_dsts in enumerate(self.model.data['targets']):
                sel = self.model.selected_target
                if sel is not None and i != sel:
                    continue
                color = QtGui.QColor('#FF00FF')
                painter.setPen(color)
                color.setAlpha(50)
                painter.setBrush(color)
                origin = QtCore.QRect(*origin_dsts['origin'])
                painter.drawRect(origin)
                for dst in origin_dsts['destinations']:
                    color = QtGui.QColor('#FFFF00')
                    painter.setPen(color)
                    color.setAlpha(50)
                    painter.setBrush(color)
                    dst = QtCore.QRect(*dst)
                    painter.drawRect(dst)
                    painter.setPen(QtCore.Qt.white)
                    painter.setBrush(QtCore.Qt.NoBrush)
                    painter.drawLine(origin.center(), dst.center())
        if self.model.interactions:
            color = QtGui.QColor(QtCore.Qt.green)
            color.setAlpha(50)
            painter.setBrush(color)
            align = QtCore.Qt.AlignCenter
            for interaction in self.model.data['interactions']:
                painter.setPen(QtCore.Qt.green)
                painter.setBrush(color)
                rect = QtCore.QRect(*interaction['zone'])
                painter.drawRect(rect)
                text = get_interaction_text(interaction)
                painter.drawText(rect, align, text)
                painter.setPen(QtCore.Qt.white)
                painter.setBrush(QtCore.Qt.white)
                if None not in interaction['target']:
                    painter.drawEllipse(*interaction['target'], 2, 2)
                elif interaction['target'][0] is None:
                    y = interaction['target'][1]
                    p1 = QtCore.QPoint(interaction['zone'][0], y)
                    x = interaction['zone'][0] + interaction['zone'][2]
                    p2 = QtCore.QPoint(x, y)
                    painter.drawLine(p1, p2)
                elif interaction['target'][1] is None:
                    x = interaction['target'][0]
                    p1 = QtCore.QPoint(x, interaction['zone'][1])
                    y = interaction['zone'][1] + interaction['zone'][3]
                    p2 = QtCore.QPoint(x, y)
                    painter.drawLine(p1, p2)
        painter.end()


def get_interaction_text(interaction):
    if interaction['direction'] == 'left':
        return f"<- {interaction['action']}"
    if interaction['direction'] == 'right':
        return f"{interaction['action']} ->"
    if interaction['direction'] == 'up':
        return f"^\n{interaction['action']}"
    if interaction['direction'] == 'down':
        return f"{interaction['action']}\nv"


class Editor(QtWidgets.QWidget):
    def __init__(self, gameroot, filename):
        super().__init__()
        self.setMinimumWidth(1100)
        self.filename = filename
        with open(filename, 'r') as f:
            data = json.load(f)
        self.model = LevelCanvasModel(gameroot, data)
        self.canvas = LevelCanvas(self.model)
        self.canvas.point_set.connect(self.add_point)
        self.canvas.rect_drawn.connect(self.add_rectangle)
        self.canvas.polygon_drawn.connect(self.add_polygon)
        self.visibilities = Visibilities(self.model)
        self.visibilities.update_visibilities.connect(self.change_visibilities)

        selection_mode = QtWidgets.QAbstractItemView.ExtendedSelection
        self.popspotsmodel = PopspotsModel(self.model)
        self.popspots = QtWidgets.QListView()
        self.popspots.setSelectionMode(selection_mode)
        self.popspots.setModel(self.popspotsmodel)

        selection_behavior = QtWidgets.QAbstractItemView.SelectRows
        self.walls_model = WallsModel(self.model)
        self.walls_model.changed.connect(self.canvas.repaint)
        self.walls = QtWidgets.QTableView()
        self.walls.setSelectionMode(selection_mode)
        self.walls.setSelectionBehavior(selection_behavior)
        self.walls.setModel(self.walls_model)

        self.interactions_model = InteractionModel(self.model)
        self.interactions_model.changed.connect(self.canvas.repaint)
        self.interactions = QtWidgets.QTableView()
        self.interactions.setSelectionMode(selection_mode)
        self.interactions.setSelectionBehavior(selection_behavior)
        self.interactions.setModel(self.interactions_model)

        self.stairs_model = StairModel(self.model)
        self.stairs_model.changed.connect(self.canvas.repaint)
        self.stairs = QtWidgets.QTableView()
        self.stairs.setSelectionMode(selection_mode)
        self.stairs.setSelectionBehavior(selection_behavior)
        self.stairs.setModel(self.stairs_model)

        self.targets = OriginDestinations(self.model)
        self.targets.changed.connect(self.canvas.repaint)

        self.tab = QtWidgets.QTabWidget()
        self.tab.currentChanged.connect(self.tab_changed)
        self.tab.addTab(self.visibilities, 'Visibilites')
        self.tab.addTab(self.popspots, 'Pop spots')
        self.tab.addTab(self.walls, 'Walls')
        self.tab.addTab(self.interactions, 'Interactions')
        self.tab.addTab(self.stairs, 'Stairs')
        self.tab.addTab(self.targets, 'Origin/Targets')

        self.rect_wall = QtWidgets.QPushButton('Create rect wall')
        self.rect_wall.setCheckable(True)
        self.rect_wall.setChecked(True)
        self.poly_wall = QtWidgets.QPushButton('Create polygonal wall')
        self.poly_wall.setCheckable(True)
        self.poly_wall.setChecked(True)
        self.create_interaction = QtWidgets.QPushButton('Create interaction')
        self.create_interaction.setCheckable(True)
        self.create_interaction.setChecked(True)
        self.create_stair = QtWidgets.QPushButton('Create stair')
        self.create_stair.setCheckable(True)
        self.create_stair.setChecked(True)
        self.add_popspots = QtWidgets.QPushButton('Create pop spot')
        self.add_popspots.setCheckable(True)
        self.create_origin = QtWidgets.QPushButton('Create origin zone')
        self.create_origin.setCheckable(True)
        self.create_destination = QtWidgets.QPushButton('Create destination zone')
        self.create_destination.setCheckable(True)

        self.group = QtWidgets.QButtonGroup()
        self.group.addButton(self.rect_wall, 0)
        self.group.addButton(self.poly_wall, 1)
        self.group.addButton(self.add_popspots, 2)
        self.group.addButton(self.create_interaction, 3)
        self.group.addButton(self.create_stair, 4)
        self.group.addButton(self.create_origin, 5)
        self.group.addButton(self.create_destination, 6)
        self.group.idReleased.connect(self.mode_changed)
        self.group.setExclusive(True)

        self.delete = QtWidgets.QPushButton('delete')

        action1 = QtGui.QAction('💾', self)
        action1.triggered.connect(self.save)
        action2 = QtGui.QAction('📁', self)
        action2.triggered.connect(self.open)
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.addAction(action1)
        self.toolbar.addAction(action2)

        buttons = QtWidgets.QGridLayout()
        buttons.setSpacing(2)
        buttons.addWidget(self.rect_wall, 0, 0)
        buttons.addWidget(self.poly_wall, 1, 0)
        buttons.addWidget(self.add_popspots, 2, 0)
        buttons.addWidget(self.create_interaction, 3, 0)
        buttons.addWidget(self.create_stair, 0, 1)
        buttons.addWidget(self.create_origin, 1, 1)
        buttons.addWidget(self.create_destination, 2, 1)

        right = QtWidgets.QVBoxLayout()
        right.addLayout(buttons)
        right.addWidget(self.tab)
        right.addWidget(self.delete)

        vlayout = QtWidgets.QHBoxLayout()
        vlayout.addWidget(self.canvas)
        vlayout.addLayout(right)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addLayout(vlayout)

    def tab_changed(self, *_):
        for table in (self.walls, self.interactions):
            table.horizontalHeader().resizeSections(
                QtWidgets.QHeaderView.ResizeToContents)

    def mode_changed(self, index):
        self.canvas.mode = (
            'rectangle', 'polygon', 'point', 'rectangle',
            'rectangle', 'rectangle', 'rectangle')[index]
        self.canvas.repaint()

    def add_point(self, point):
        if self.group.checkedId() == 3:
            self.model.data['popspots'].append((point.x(), point.y()))

    def add_rectangle(self, rect):
        if self.group.checkedId() == 0:
            self.walls_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            self.model.data['no_go_zones'].append(rect)
            self.walls_model.layoutChanged.emit()
        if self.group.checkedId() == 3:
            self.interactions_model.layoutAboutToBeChanged.emit()
            target = [rect.center().x(), rect.center().y()]
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            interaction = {
                "action": "poker",
                "direction": "right",
                "zone": rect,
                "target": target}
            self.model.data['interactions'].append(interaction)
            self.interactions_model.layoutChanged.emit()
        if self.group.checkedId() == 4:
            self.stairs_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            stair = {
                "zone": rect,
                "inclination": 1.5}
            self.model.data['stairs'].append(stair)
            self.stairs_model.layoutChanged.emit()
        if self.group.checkedId() == 5:
            self.targets.origin_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            target = {
                "origin": rect,
                "weight": 3,
                "destinations": []}
            self.model.data['targets'].append(target)
            self.targets.origin_model.layoutChanged.emit()
        if self.group.checkedId() == 6:
            if self.model.selected_target is None:
                return
            self.targets.destinations_model.layoutAboutToBeChanged.emit()
            rect = [rect.left(), rect.top(), rect.width(), rect.height()]
            self.model.data['targets'][self.model.selected_target]['destinations'].append(rect)
            self.targets.destinations_model.layoutChanged.emit()

    def add_polygon(self, polygon):
        self.walls_model.layoutAboutToBeChanged.emit()
        data = [(p.x(), p.y()) for p in polygon]
        self.model.data['walls'].append(data)
        self.repaint()
        self.walls_model.layoutChanged.emit()

    def keyPressEvent(self, event):
        self.canvas.keyPressEvent(event)

    def change_visibilities(self):
        self.model.walls = self.visibilities.walls.isChecked()
        self.model.popspots = self.visibilities.popspots.isChecked()
        self.model.interactions = self.visibilities.interactions.isChecked()
        self.model.props = self.visibilities.props.isChecked()
        self.model.stairs = self.visibilities.stairs.isChecked()
        self.model.targets = self.visibilities.targets.isChecked()
        self.repaint()

    def open(self):
        ...

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.model.data, f, indent=2)


class OriginModel(QtCore.QAbstractTableModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, _):
        return len(self.model.data['targets'])

    def columnCount(self, _):
        return 2

    def headerData(self, section, orientation, role):
        if orientation != QtCore.Qt.Horizontal or role != QtCore.Qt.DisplayRole:
            return
        return ('Origin', 'Weight')[section]

    def flags(self, index):
        flags = super().flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        return flags

    def setData(self, index, value, _):
        if not index.isValid():
            return
        try:
            data = json.loads(value)
        except TypeError:
            return False
        if index.column() == 0:
            if is_zone(data):
                self.layoutAboutToBeChanged.emit()
                self.model.data['targets'][index.row()]['origin'] = data
                self.layoutChanged.emit()
                self.changed.emit()
                return True
            return False
        if not isinstance(data, int):
            return False
        self.layoutAboutToBeChanged.emit()
        self.model.data['targets'][index]['weight'] = data
        self.changed.emit()
        self.layoutChanged.emit()
        return True

    def data(self, index, role):
        if not index.isValid():
            return
        if role not in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return
        row, col = index.row(), index.column()
        target = self.model.data['targets'][row]
        if col == 0:
            return str(target['origin'])
        return str(target['weight'])


class DestinationsModel(QtCore.QAbstractListModel):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def rowCount(self, _):
        if self.model.selected_target is None:
            return 0
        index = self.model.selected_target
        return len(self.model.data['targets'][index]['destinations'])

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role):
        if not index.isValid():
            return
        try:
            data = json.loads(value)
        except TypeError:
            return False
        if not is_zone(data):
            return False
        row = index.row()
        self.layoutAboutToBeChanged.emit()
        target = self.model.data['targets'][self.model.selected_target]
        target['destinations'][row] = data
        self.layoutChanged.emit()
        self.changed.emit()
        return True

    def data(self, index, role):
        roles = QtCore.Qt.DisplayRole, QtCore.Qt.EditRole
        if not index.isValid() or role not in roles:
            return

        row = index.row()
        target = self.model.data['targets'][self.model.selected_target]
        return str(target['destinations'][row])


class OriginDestinations(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.origin_model = OriginModel(self.model)
        self.origin_model.changed.connect(self.changed.emit)
        self.origin = QtWidgets.QTableView()
        behavior = QtWidgets.QAbstractItemView.SelectRows
        self.origin.setSelectionBehavior(behavior)
        self.origin.setModel(self.origin_model)
        method = self.selection_changed
        self.origin.selectionModel().selectionChanged.connect(method)
        self.destinations_model = DestinationsModel(self.model)
        self.destinations_model.changed.connect(self.changed.emit)
        self.destinations = QtWidgets.QListView()
        self.destinations.setSelectionBehavior(behavior)
        self.destinations.setModel(self.destinations_model)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.origin)
        layout.addWidget(self.destinations)

    def selection_changed(self, *_):
        indexes = self.origin.selectionModel().selectedIndexes()
        self.destinations_model.layoutAboutToBeChanged.emit()
        if not indexes:
            self.model.selected_target = None
            self.changed.emit()
            return
        self.model.selected_target = indexes[0].row()
        self.changed.emit()
        self.destinations_model.layoutChanged.emit()


class Visibilities(QtWidgets.QWidget):
    update_visibilities = QtCore.Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.walls = QtWidgets.QCheckBox('Walls', checked=True)
        self.walls.released.connect(self.update_visibilities.emit)
        self.popspots = QtWidgets.QCheckBox('Pop Spots', checked=True)
        self.popspots.released.connect(self.update_visibilities.emit)
        self.interactions = QtWidgets.QCheckBox('Interactions', checked=True)
        self.interactions.released.connect(self.update_visibilities.emit)
        self.props = QtWidgets.QCheckBox('Props', checked=True)
        self.props.released.connect(self.update_visibilities.emit)
        self.stairs = QtWidgets.QCheckBox('Stairs', checked=True)
        self.targets = QtWidgets.QCheckBox('Origin -> Destinations', checked=True)
        self.targets.released.connect(self.update_visibilities.emit)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.walls)
        layout.addWidget(self.popspots)
        layout.addWidget(self.interactions)
        layout.addWidget(self.props)
        layout.addWidget(self.stairs)
        layout.addWidget(self.targets)
        layout.addStretch(1)


app = QtWidgets.QApplication([])
gameroot = 'C:/perso/drunk-paranoia/drunkparanoia'
scene = 'C:/perso/drunk-paranoia/drunkparanoia/resources/scenes/saloon.json'
editor = Editor(gameroot, scene)
editor.show()
app.exec()
