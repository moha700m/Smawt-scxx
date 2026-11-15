from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import mss
from PySide6.QtCore import Qt, QTimer, QPointF, QStandardPaths
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QFont, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QMessageBox, QFrame, QComboBox, QSlider,
    QGroupBox
)


APP_NAME = "SMAET REC"
APP_DIR = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)) / "SMAET-REC"
APP_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = APP_DIR / "session.json"


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 360)
        self.setStyleSheet("background:#090d14;border:1px solid #263244;border-radius:16px;")
        self.frame: QImage | None = None
        self.strokes: list[list[tuple[float, float]]] = []
        self.current: list[tuple[float, float]] = []
        self.pen_color = QColor("#ffcc55")
        self.pen_width = 4
        self.drawing = False

    def set_frame(self, image: QImage):
        self.frame = image
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.frame is not None:
            self.drawing = True
            p = self._image_point(event.position())
            self.current = [(p.x(), p.y())]
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            p = self._image_point(event.position())
            self.current.append((p.x(), p.y()))
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            if len(self.current) > 1:
                self.strokes.append(self.current)
            self.current = []
            self.update()

    def _image_rect(self):
        if self.frame is None:
            return self.rect()
        scaled = self.frame.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x = (self.width() - scaled.width()) / 2
        y = (self.height() - scaled.height()) / 2
        return self.rect().__class__(int(x), int(y), scaled.width(), scaled.height())

    def _image_point(self, point: QPointF):
        rect = self._image_rect()
        x = max(0.0, min(1.0, (point.x() - rect.x()) / max(1, rect.width())))
        y = max(0.0, min(1.0, (point.y() - rect.y()) / max(1, rect.height())))
        return QPointF(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#090d14"))
        if self.frame is None:
            painter.setPen(QColor("#8b9bb0"))
            painter.setFont(QFont("Segoe UI", 15))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "معاينة شاشة الكمبيوتر ستظهر هنا")
            return
        target = self._image_rect()
        painter.drawImage(target, self.frame)
        for stroke in self.strokes + ([self.current] if self.current else []):
            if len(stroke) < 2:
                continue
            pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            points = [QPointF(target.x() + x * target.width(),
                              target.y() + y * target.height()) for x, y in stroke]
            for a, b in zip(points, points[1:]):
                painter.drawLine(a, b)

    def clear_drawing(self):
        self.strokes.clear()
        self.current.clear()
        self.update()

    def export_strokes(self):
        return self.strokes

    def import_strokes(self, strokes):
        self.strokes = strokes if isinstance(strokes, list) else []
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 780)
        self.setMinimumSize(900, 620)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.recorder: subprocess.Popen | None = None
        self.record_started = 0.0
        self.last_output: Path | None = None
        self.capture = mss.mss()
        self.output_dir = Path.home() / "Videos" / "SMAET REC"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._build_ui()
        self._load_session()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_preview)
        self.timer.start(100)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.update_record_time)
        self.clock.start(250)
        self.update_preview()
        self._set_status("جاهز — لم يتم توصيل iPhone")

    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background:#101722; color:#edf3fb; font-family:'Segoe UI'; }
            QLabel#muted { color:#91a2b8; }
            QFrame#panel, QGroupBox { background:#172231; border:1px solid #28384c; border-radius:14px; }
            QPushButton { background:#26364b; border:0; border-radius:10px; padding:11px 16px; color:#f5f8fc; font-size:14px; }
            QPushButton:hover { background:#344a64; }
            QPushButton:disabled { color:#748195; background:#202a37; }
            QPushButton#record { background:#d94d59; font-weight:700; }
            QPushButton#record:hover { background:#ec6470; }
            QPushButton#stop { background:#38485d; }
            QComboBox, QSlider { background:#202d3e; padding:6px; border-radius:8px; }
        """)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("SMAET REC")
        title.setStyleSheet("font-size:25px;font-weight:800;color:#ffffff;")
        header.addWidget(title)
        header.addStretch()
        self.connection = QLabel("● الكمبيوتر جاهز  |  iPhone غير متصل")
        self.connection.setStyleSheet("color:#f0bd65;font-size:13px;")
        header.addWidget(self.connection)
        settings_btn = QPushButton("الإعدادات")
        settings_btn.clicked.connect(self.show_settings)
        header.addWidget(settings_btn)
        layout.addLayout(header)

        self.preview = Preview()
        layout.addWidget(self.preview, 1)

        tools = QHBoxLayout()
        tools.addWidget(QLabel("أداة الرسم"))
        self.tool = QComboBox()
        self.tool.addItems(["قلم", "تمييز"])
        self.tool.currentIndexChanged.connect(self.change_tool)
        tools.addWidget(self.tool)
        tools.addWidget(QLabel("السُمك"))
        self.thickness = QSlider(Qt.Orientation.Horizontal)
        self.thickness.setRange(2, 14)
        self.thickness.setValue(4)
        self.thickness.setFixedWidth(120)
        self.thickness.valueChanged.connect(lambda v: setattr(self.preview, "pen_width", v))
        tools.addWidget(self.thickness)
        clear_btn = QPushButton("مسح الرسم")
        clear_btn.clicked.connect(self.preview.clear_drawing)
        tools.addWidget(clear_btn)
        tools.addStretch()
        layout.addLayout(tools)

        actions = QHBoxLayout()
        self.pc_btn = QPushButton("عرض شاشة الكمبيوتر")
        self.pc_btn.clicked.connect(self.update_preview)
        actions.addWidget(self.pc_btn)
        self.iphone_btn = QPushButton("توصيل iPhone")
        self.iphone_btn.clicked.connect(self.iphone_help)
        actions.addWidget(self.iphone_btn)
        self.save_btn = QPushButton("حفظ المشروع")
        self.save_btn.clicked.connect(self.save_project)
        actions.addWidget(self.save_btn)
        self.open_btn = QPushButton("فتح مشروع")
        self.open_btn.clicked.connect(self.open_project)
        actions.addWidget(self.open_btn)
        actions.addStretch()
        self.record_btn = QPushButton("● تسجيل")
        self.record_btn.setObjectName("record")
        self.record_btn.clicked.connect(self.start_recording)
        actions.addWidget(self.record_btn)
        self.stop_btn = QPushButton("■ إيقاف")
        self.stop_btn.setObjectName("stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_recording)
        actions.addWidget(self.stop_btn)
        layout.addLayout(actions)

        footer = QHBoxLayout()
        self.status = QLabel("جاهز")
        self.status.setObjectName("muted")
        footer.addWidget(self.status)
        footer.addStretch()
        self.duration = QLabel("00:00")
        self.duration.setStyleSheet("font-size:17px;font-weight:700;")
        footer.addWidget(self.duration)
        open_folder = QPushButton("مجلد الفيديوهات")
        open_folder.clicked.connect(self.open_output_folder)
        footer.addWidget(open_folder)
        layout.addLayout(footer)

    def _set_status(self, message: str):
        self.status.setText(message)

    def change_tool(self, index: int):
        self.preview.pen_color = QColor("#ffd45f" if index == 1 else "#ffcc55")
        self.preview.pen_width = 9 if index == 1 else self.thickness.value()

    def update_preview(self):
        try:
            monitor = self.capture.monitors[1]
            shot = self.capture.grab(monitor)
            image = QImage(shot.rgb, shot.width, shot.height, shot.width * 3,
                           QImage.Format.Format_RGB888).copy()
            self.preview.set_frame(image)
        except Exception as exc:
            self._set_status(f"تعذر التقاط الشاشة: {exc}")

    def _ffmpeg(self):
        path = shutil.which("ffmpeg")
        if not path:
            QMessageBox.warning(self, "FFmpeg غير موجود",
                                "ثبّت FFmpeg وأضف ffmpeg.exe إلى PATH ثم أعد تشغيل التطبيق.")
        return path

    def start_recording(self):
        if self.recorder is not None:
            return
        ffmpeg = self._ffmpeg()
        if not ffmpeg:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output = self.output_dir / f"SMAET_REC_{stamp}.mp4"
        command = [
            ffmpeg, "-y", "-f", "gdigrab", "-framerate", "30",
            "-draw_mouse", "1", "-i", "desktop", "-an",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(output)
        ]
        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.recorder = subprocess.Popen(command, stdin=subprocess.PIPE,
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL,
                                              creationflags=creation_flags)
            time.sleep(0.25)
            if self.recorder.poll() is not None:
                self.recorder = None
                QMessageBox.critical(self, "فشل التسجيل",
                                     "تعذر بدء FFmpeg. تحقق من دعم gdigrab و libx264 في نسخة FFmpeg المثبتة.")
                return
            self.record_started = time.monotonic()
            self.last_output = output
            self.record_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self._set_status(f"جاري التسجيل: {output.name}")
        except Exception as exc:
            self.recorder = None
            QMessageBox.critical(self, "خطأ", str(exc))

    def stop_recording(self):
        proc = self.recorder
        if proc is None:
            return
        try:
            proc.stdin.write(b"q\n")
            proc.stdin.flush()
            proc.wait(timeout=15)
        except Exception:
            proc.kill()
            proc.wait(timeout=5)
        self.recorder = None
        self.record_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.duration.setText("00:00")
        if self.last_output and self.last_output.exists() and self.last_output.stat().st_size > 0:
            self._set_status(f"تم حفظ الفيديو: {self.last_output}")
        else:
            self._set_status("انتهى التسجيل لكن لم يتم إنشاء ملف صالح.")

    def update_record_time(self):
        if self.recorder is not None:
            elapsed = int(time.monotonic() - self.record_started)
            self.duration.setText(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
            if self.recorder.poll() is not None:
                self.recorder = None
                self.record_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self._set_status("توقف التسجيل بشكل غير متوقع. تحقق من FFmpeg.")

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "حفظ المشروع", str(Path.home() / "SMAET-REC-Project.json"), "SMAET REC (*.json)")
        if not path:
            return
        data = {"version": 1, "strokes": self.preview.export_strokes(),
                "output_dir": str(self.output_dir), "layout": "desktop"}
        try:
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self._set_status(f"تم حفظ المشروع: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "تعذر الحفظ", str(exc))

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "فتح المشروع", str(Path.home()), "SMAET REC (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.preview.import_strokes(data.get("strokes", []))
            if data.get("output_dir"):
                self.output_dir = Path(data["output_dir"])
            self._set_status(f"تم فتح المشروع: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "تعذر فتح المشروع", str(exc))

    def show_settings(self):
        QMessageBox.information(self, "الإعدادات",
            f"مجلد الحفظ:\n{self.output_dir}\n\nالتسجيل الحالي: سطح المكتب الأساسي، 1080p حسب دقة الشاشة، 30 إطاراً/ثانية، H.264.\nالصوت غير مفعّل في هذا الإصدار.\nواجهة التحكم تعمل محلياً داخل تطبيق Windows ولا تفتح منفذاً شبكياً.")

    def iphone_help(self):
        QMessageBox.information(self, "توصيل iPhone",
            "لم يتم تفعيل استقبال iPhone في هذا الإصدار، لذلك لن نعرض اتصالاً وهمياً.\n\nUSB: لا توفر iOS واجهة عامة لنسخ الشاشة إلى Windows عبر USB؛ يلزم مكوّن استقبال متوافق.\nAirPlay: يحتاج مستقبلاً متوافقاً مستقلاً على الشبكة المحلية. لم يتم تضمين مستقبل بعد.")

    def open_output_folder(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(self.output_dir)])
        else:
            QMessageBox.information(self, "مجلد الحفظ", str(self.output_dir))

    def _load_session(self):
        try:
            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                if data.get("output_dir"):
                    self.output_dir = Path(data["output_dir"])
        except Exception:
            pass

    def closeEvent(self, event):
        if self.recorder is not None:
            answer = QMessageBox.question(self, "التسجيل مستمر",
                "هل تريد إيقاف التسجيل والخروج؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.stop_recording()
        try:
            SETTINGS_FILE.write_text(json.dumps({"output_dir": str(self.output_dir)}, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        try:
            self.capture.close()
        except Exception:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
