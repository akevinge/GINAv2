import sys
from typing import List, Dict, Tuple, Optional, Callable, Any

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
    QStyleOptionGraphicsItem,
)
from PySide6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QTimer,
)
from PySide6.QtGui import (
    QPainter,
    QColor,
    QBrush,
    QPen,
    QPolygonF,
    QFont,
    QPainterPath,
    QPainterPathStroker,
)

# ==========================================
#        CONSTANTS & CONFIGURATION
# ==========================================

COLOR_BG = Qt.black
COLOR_TEXT = Qt.white
COLOR_GOX_PIPE_DIM = QColor("#441111")
COLOR_FUEL_PIPE_DIM = QColor("#112244")
COLOR_N2_PIPE_DIM = QColor("#442200")
FLUID_GOX = QColor("#FF5252")
FLUID_FUEL = QColor("#2979FF")
FLUID_N2 = QColor("#FFD600")
COLOR_VALVE_CLOSED = Qt.white
COLOR_VALVE_OPEN = QColor("#FF0000")

# ==========================================
#           TYPE DEFINITIONS
# ==========================================

# Forward reference for ValveItem to be used in the logic callable
ValveDict = Dict[str, "ValveItem"]
# The logic function returns a Tuple of (Active Color, Is Flowing Bool)
PipeLogicFunc = Callable[[ValveDict], Tuple[Optional[QColor], bool]]


# ==========================================
#           P&ID GRAPHICS ITEMS
# ==========================================


class ValveItem(QGraphicsItem):
    def __init__(
        self, key: str, name: str, x: float, y: float, vertical: bool = False
    ) -> None:
        super().__init__()
        self.key: str = key
        self.name: str = name
        self.is_open: bool = False
        self.vertical: bool = vertical
        self.setPos(x, y)
        self.setZValue(20)

    def boundingRect(self) -> QRectF:
        return QRectF(-35, -35, 70, 70)

    def paint(
        self,
        painter: Optional[QPainter],
        option: Optional[QStyleOptionGraphicsItem],
        widget: Optional[QWidget] = None,
    ) -> None:
        if not painter:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill_color = COLOR_VALVE_OPEN if self.is_open else COLOR_VALVE_CLOSED
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(Qt.GlobalColor.black, 2))

        poly: QPolygonF
        if not self.vertical:
            poly = QPolygonF(
                [
                    QPointF(-15, -10),
                    QPointF(-15, 10),
                    QPointF(0, 0),
                    QPointF(15, 10),
                    QPointF(15, -10),
                    QPointF(0, 0),
                ]
            )
        else:
            poly = QPolygonF(
                [
                    QPointF(-10, -15),
                    QPointF(10, -15),
                    QPointF(0, 0),
                    QPointF(10, 15),
                    QPointF(-10, 15),
                    QPointF(0, 0),
                ]
            )
        painter.drawPolygon(poly)

        painter.setPen(QPen(COLOR_TEXT))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        label_y = -35 if not self.vertical else -45
        painter.drawText(
            QRectF(-50, label_y, 100, 20), Qt.AlignmentFlag.AlignCenter, self.name
        )

    def set_state(self, is_open: bool) -> None:
        self.is_open = is_open
        self.update()


class SensorItem(QGraphicsItem):
    def __init__(self, key: str, name: str, x: float, y: float) -> None:
        super().__init__()
        self.key: str = key
        self.name: str = name
        self.psi_value: float = 0.0
        self.setPos(x, y)
        self.setZValue(25)

    def boundingRect(self) -> QRectF:
        return QRectF(-35, -25, 70, 50)

    def paint(
        self,
        painter: Optional[QPainter],
        option: Optional[QStyleOptionGraphicsItem],
        widget: Optional[QWidget] = None,
    ) -> None:
        if not painter:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(-25, -15, 50, 30)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawRoundedRect(rect, 4, 4)

        painter.setPen(QPen(Qt.GlobalColor.black))
        font_val = QFont("Courier New", 10, QFont.Weight.Bold)
        painter.setFont(font_val)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.psi_value)}")

        painter.setPen(QPen(COLOR_TEXT))
        font_lbl = QFont("Arial", 8)
        painter.setFont(font_lbl)
        painter.drawText(
            QRectF(-45, -35, 90, 15), Qt.AlignmentFlag.AlignCenter, self.name
        )

    def update_pressure(self, value: float) -> None:
        self.psi_value = value
        self.update()


class FlowPipeItem(QGraphicsItem):
    def __init__(
        self, path_points: List[QPointF], dim_color: QColor, width: int = 4
    ) -> None:
        super().__init__()
        self.path_points: List[QPointF] = path_points
        self.dim_color: QColor = dim_color
        self.width: int = width
        self.active_color: Optional[QColor] = None
        self.is_flowing: bool = False
        self.dash_offset: int = 0
        self.setZValue(1)

    def boundingRect(self) -> QRectF:
        return self.shape().boundingRect()

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        if len(self.path_points) > 1:
            path.moveTo(self.path_points[0])
            for p in self.path_points[1:]:
                path.lineTo(p)
        stroker = QPainterPathStroker()
        stroker.setWidth(self.width)
        return stroker.createStroke(path)

    def paint(
        self,
        painter: Optional[QPainter],
        option: Optional[QStyleOptionGraphicsItem],
        widget: Optional[QWidget] = None,
    ) -> None:
        if not painter:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        base_color = self.active_color if self.active_color else self.dim_color

        painter.setPen(
            QPen(
                base_color,
                self.width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        if len(self.path_points) > 1:
            painter.drawPolyline(self.path_points)

        if self.is_flowing:
            pen_stripe = QPen(
                Qt.GlobalColor.black,
                self.width - 1,
                Qt.PenStyle.CustomDashLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            pen_stripe.setDashPattern([10.0, 10.0])
            pen_stripe.setDashOffset(float(self.dash_offset))
            painter.setPen(pen_stripe)
            painter.drawPolyline(self.path_points)

    def update_state(self, active_color: Optional[QColor], is_flowing: bool) -> None:
        if self.active_color != active_color or self.is_flowing != is_flowing:
            self.active_color = active_color
            self.is_flowing = is_flowing
            self.update()

    def update_animation(self) -> None:
        if self.is_flowing:
            self.dash_offset -= 1
            self.update()


class RocketPlumbingWidget(QGraphicsView):
    def __init__(self, valve_press_callback: Callable[[str, bool], None] = {}) -> None:
        super().__init__()
        self.valve_press_callback = valve_press_callback

        self.scene: QGraphicsScene = QGraphicsScene(0, 0, 800, 600)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(COLOR_BG))
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self.valves: Dict[str, ValveItem] = {}
        self.sensors: Dict[str, SensorItem] = {}
        # List of tuples containing the Pipe Item and its logic lambda
        self.pipe_segments: List[Tuple[FlowPipeItem, PipeLogicFunc]] = []

        self.setup_diagram()

        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(50)

    def setup_diagram(self) -> None:
        def add_v(
            key: str, name: str, x: float, y: float, vertical: bool = False
        ) -> None:
            v = ValveItem(key, name, x, y, vertical)
            self.scene.addItem(v)
            self.valves[key] = v

        def add_s(key: str, name: str, x: float, y: float) -> None:
            s = SensorItem(key, name, x, y)
            self.scene.addItem(s)
            self.sensors[key] = s

        def add_pipe(
            points: List[QPointF], dim_color: QColor, logic_func: PipeLogicFunc
        ) -> None:
            pipe = FlowPipeItem(points, dim_color)
            self.scene.addItem(pipe)
            self.pipe_segments.append((pipe, logic_func))

        # --- Static Elements ---
        self.add_tank("GOX", 600, 70, 150, 60, COLOR_GOX_PIPE_DIM)
        self.add_tank("N2", 600, 170, 150, 60, COLOR_N2_PIPE_DIM)
        self.add_tank("Eth", 350, 420, 200, 60, COLOR_FUEL_PIPE_DIM)
        self.add_tank("N2", 600, 420, 150, 60, COLOR_N2_PIPE_DIM)

        self.scene.addRect(
            100,
            250,
            100,
            100,
            QPen(Qt.GlobalColor.white, 3),
            QBrush(Qt.GlobalColor.black),
        )
        lbl = self.scene.addText("Inj")
        lbl.setPos(135, 285)
        lbl.setDefaultTextColor(Qt.GlobalColor.white)
        lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        # --- PIPING LOGIC ---
        p_gox_1 = [QPointF(600, 100), QPointF(420, 100)]
        add_pipe(
            p_gox_1, COLOR_GOX_PIPE_DIM, lambda v: (FLUID_GOX, v["gox_preslug"].is_open)
        )

        p_gox_prv = [QPointF(420, 100), QPointF(350, 100), QPointF(350, 70)]
        add_pipe(
            p_gox_prv, COLOR_GOX_PIPE_DIM, lambda v: (FLUID_GOX, v["gox_prv"].is_open)
        )

        p_n2_top = [QPointF(600, 200), QPointF(350, 200), QPointF(350, 150)]
        add_pipe(
            p_n2_top, COLOR_N2_PIPE_DIM, lambda v: (FLUID_N2, v["gox_n2_purge"].is_open)
        )

        p_n2_inj = [QPointF(350, 150), QPointF(350, 100)]
        add_pipe(
            p_n2_inj,
            COLOR_N2_PIPE_DIM,
            lambda v: (
                FLUID_N2 if v["gox_n2_purge"].is_open else None,
                v["gox_n2_purge"].is_open,
            ),
        )

        p_gox_mid = [QPointF(420, 100), QPointF(150, 100), QPointF(150, 180)]

        def gox_mid_logic(v: ValveDict) -> Tuple[Optional[QColor], bool]:
            if v["gox_n2_purge"].is_open:
                return (FLUID_N2, v["gox_release"].is_open)
            elif v["gox_preslug"].is_open:
                return (FLUID_GOX, v["gox_release"].is_open)
            return (None, False)

        add_pipe(p_gox_mid, COLOR_GOX_PIPE_DIM, gox_mid_logic)

        p_gox_final = [QPointF(150, 180), QPointF(150, 250)]

        def gox_final_logic(v: ValveDict) -> Tuple[Optional[QColor], bool]:
            if v["gox_release"].is_open:
                if v["gox_n2_purge"].is_open:
                    return (FLUID_N2, True)
                elif v["gox_preslug"].is_open:
                    return (FLUID_GOX, True)
            return (None, False)

        add_pipe(p_gox_final, COLOR_GOX_PIPE_DIM, gox_final_logic)

        p_fuel_1 = [QPointF(350, 450), QPointF(220, 450)]
        add_pipe(
            p_fuel_1,
            COLOR_FUEL_PIPE_DIM,
            lambda v: (FLUID_FUEL, v["fuel_preslug"].is_open),
        )

        p_n2_bot = [QPointF(600, 450), QPointF(580, 450)]
        add_pipe(p_n2_bot, COLOR_N2_PIPE_DIM, lambda v: (FLUID_N2, True))

        p_n2_purge_line = [QPointF(580, 450), QPointF(580, 380), QPointF(300, 380)]
        add_pipe(
            p_n2_purge_line,
            COLOR_N2_PIPE_DIM,
            lambda v: (FLUID_N2, v["fuel_n2_purge"].is_open),
        )

        p_n2_purge_drop = [QPointF(300, 380), QPointF(300, 450)]
        add_pipe(
            p_n2_purge_drop,
            COLOR_N2_PIPE_DIM,
            lambda v: (
                FLUID_N2 if v["fuel_n2_purge"].is_open else None,
                v["fuel_n2_purge"].is_open,
            ),
        )

        p_fuel_mid = [QPointF(220, 450), QPointF(150, 450), QPointF(150, 400)]

        def fuel_mid_logic(v: ValveDict) -> Tuple[Optional[QColor], bool]:
            if v["fuel_n2_purge"].is_open:
                return (FLUID_N2, v["fuel_release"].is_open)
            elif v["fuel_preslug"].is_open:
                return (FLUID_FUEL, v["fuel_release"].is_open)
            return (None, False)

        add_pipe(p_fuel_mid, COLOR_FUEL_PIPE_DIM, fuel_mid_logic)

        p_fuel_final = [QPointF(150, 400), QPointF(150, 350)]

        def fuel_final_logic(v: ValveDict) -> Tuple[Optional[QColor], bool]:
            if v["fuel_release"].is_open:
                if v["fuel_n2_purge"].is_open:
                    return (FLUID_N2, True)
                elif v["fuel_preslug"].is_open:
                    return (FLUID_FUEL, True)
            return (None, False)

        add_pipe(p_fuel_final, COLOR_FUEL_PIPE_DIM, fuel_final_logic)

        p_n2_press_feed = [QPointF(580, 450), QPointF(565, 450)]
        add_pipe(
            p_n2_press_feed,
            COLOR_N2_PIPE_DIM,
            lambda v: (FLUID_N2, v["fuel_press"].is_open),
        )

        p_n2_press_tank = [QPointF(565, 450), QPointF(550, 450)]
        add_pipe(
            p_n2_press_tank,
            COLOR_N2_PIPE_DIM,
            lambda v: (
                FLUID_N2 if v["fuel_press"].is_open else None,
                v["fuel_press"].is_open,
            ),
        )

        p_fuel_prv = [QPointF(580, 450), QPointF(580, 480)]
        add_pipe(
            p_fuel_prv, COLOR_N2_PIPE_DIM, lambda v: (FLUID_N2, v["fuel_prv"].is_open)
        )

        # --- Add Valves ---
        add_v("gox_preslug", "GOX Preslug", 420, 100)
        add_v("gox_release", "GOX Release", 150, 180, True)
        add_v("gox_n2_purge", "GOX N2 Purge", 350, 150, True)
        add_v("gox_prv", "PRV", 350, 70, True)

        add_v("fuel_preslug", "Fuel Preslug", 325, 450)
        add_v("fuel_release", "Fuel Release", 150, 400, True)
        add_v("fuel_n2_purge", "Fuel N2 Purge", 300, 380)
        add_v("fuel_press", "Fuel Pressurization", 565, 450)
        add_v("fuel_prv", "PRV", 580, 480, True)

        # --- Add Sensors ---
        add_s("gox_reg_pt", "GOX Reg PT", 550, 80)
        add_s("gox_line_pt", "GoxLinePT", 280, 120)
        add_s("gox_inj_pt", "GOX Inj PT", 220, 270)
        add_s("fuel_n2_pt", "Fuel N2 PT", 580, 400)
        add_s("fuel_line_pt", "Fuel Line PT", 280, 470)
        add_s("fuel_inj_pt", "Fuel Inj PT", 220, 310)
        add_s("chamber_pt", "Chamber PT", 220, 350)

    def add_tank(
        self, name: str, x: float, y: float, w: float, h: float, border_color: QColor
    ) -> None:
        rect = QRectF(x, y, w, h)
        self.scene.addRect(rect, QPen(border_color, 2), QBrush(Qt.GlobalColor.black))
        text = self.scene.addText(name)
        text.setDefaultTextColor(border_color)
        text.setPos(x + 10, y + 10)
        text.setFont(QFont("Arial", 10, QFont.Weight.Bold))

    def set_valve_state(self, key: str, is_open: bool) -> None:
        if key in self.valves:
            self.valves[key].set_state(is_open)
            self.check_flow_logic()

    def set_sensor_value(self, key: str, value: float) -> None:
        if key in self.sensors:
            self.sensors[key].update_pressure(value)

    def check_flow_logic(self) -> None:
        for pipe, logic_func in self.pipe_segments:
            active_color, flowing = logic_func(self.valves)
            pipe.update_state(active_color, flowing)

    def game_loop(self) -> None:
        for pipe, _ in self.pipe_segments:
            pipe.update_animation()

    def mousePressEvent(self, event: Any) -> None:
        # Simple click interaction to toggle valves for testing
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, ValveItem):
            self.set_valve_state(item.key, not item.is_open)
            self.valve_press_callback(item.key, item.is_open)
        super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RocketPlumbingWidget()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
