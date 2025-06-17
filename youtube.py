import os
import sys
import googleapiclient.discovery
import googleapiclient.errors
from collections import Counter
import webbrowser
import traceback
import requests

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QScrollArea, QFrame,
    QSizePolicy, QStackedWidget, QGraphicsDropShadowEffect, QLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QRunnable, QThreadPool, QRect, QSize, QPoint
from PyQt6.QtGui import QFont, QColor, QPixmap

API_KEY = os.environ.get('YOUTUBE_API_KEY', 'AIzaSyCH-nEjWQW4yr1jRdmIsNTO9KL-g-ypbDo')


# --- Custom FlowLayout Class ---
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().left(), 2 * self.contentsMargins().top())
        return size

    def _doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        spaceX = self.spacing()
        spaceY = self.spacing()

        for item in self.itemList:
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


# --- Worker Class for API Calls (for main data, not thumbnails) ---
class YouTubeWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, youtube_service, topic, parent=None):
        super().__init__(parent)
        self.youtube_service = youtube_service
        self.topic = topic

    def run(self):
        try:
            if not self.youtube_service:
                self.error.emit("YouTube API service not initialized. Check your API key.")
                return
            related_videos = self._search_youtube_videos(self.youtube_service, self.topic, max_results=20)
            if related_videos:
                suggestions = self._analyze_video_data(related_videos)
                self.finished.emit(suggestions)
            else:
                self.finished.emit({})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self.error.emit(error_message)

    def _search_youtube_videos(self, youtube_service, query, max_results=10):
        try:
            search_request = youtube_service.search().list(
                q=f'"{query}"',
                part="id,snippet",
                type="video",
                maxResults=max_results,
                safeSearch="none"
            )
            search_response = search_request.execute()
            video_ids = [item['id']['videoId'] for item in search_response.get('items', []) if 'videoId' in item['id']]
            if not video_ids:
                return []
            videos_data = []
            details_request = youtube_service.videos().list(
                part="snippet,statistics",
                id=",".join(video_ids)
            )
            details_response = details_request.execute()
            for item in details_response.get("items", []):
                snippet = item["snippet"]
                statistics = item.get("statistics", {})
                video_data = {
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "channel_title": snippet["channelTitle"],
                    "thumbnail_high": snippet["thumbnails"]["high"]["url"],
                    "view_count": statistics.get("viewCount", "N/A"),
                    "tags": snippet.get("tags", [])
                }
                videos_data.append(video_data)
            return videos_data
        except googleapiclient.errors.HttpError as e:
            error_message = f"YouTube API Error: {e.resp.status} - {e.content.decode()}"
            raise Exception(error_message)
        except Exception as e:
            raise Exception(f"An unexpected error occurred during Youtube: {str(e)}")

    def _analyze_video_data(self, videos):
        all_titles_info = []
        all_thumbnail_urls = []
        all_video_tags = []
        for video in videos:
            all_titles_info.append((video["title"], video["view_count"], video["channel_title"]))
            all_thumbnail_urls.append(video["thumbnail_high"])
            all_video_tags.extend(video["tags"])
        all_titles_info.sort(key=lambda x: int(x[1]) if str(x[1]).isdigit() else 0, reverse=True)
        unique_titles_seen = set()
        title_suggestions_list = []
        for title, views, channel in all_titles_info:
            if title not in unique_titles_seen:
                unique_titles_seen.add(title)
                title_suggestions_list.append((title, views, channel))
        title_suggestions = title_suggestions_list[:min(10, len(title_suggestions_list))]
        relevant_tags = [tag.lower() for tag in all_video_tags if tag and len(tag.strip()) > 1]
        keyword_counts = Counter(relevant_tags)
        keyword_suggestions = [word for word, count in keyword_counts.most_common(15)]
        thumbnail_urls = list(set(all_thumbnail_urls))
        return {
            "title_suggestions": title_suggestions,
            "keyword_suggestions": keyword_suggestions,
            "thumbnail_urls": thumbnail_urls
        }

def format_view_count(view_count):
    if isinstance(view_count, str) and view_count.isdigit():
        return f"{int(view_count):,}"
    elif isinstance(view_count, int):
        return f"{view_count:,}"
    else:
        return str(view_count)

class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.setStyleSheet("""
            QFrame#cardFrame {
                background: rgba(40,40,40,0.9);
                border-radius: 16px;
                border: 1px solid #333;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0,0,0,80))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

class ClickableLabel(QLabel):
    def __init__(self, text="", callback=None, parent=None):
        super().__init__(text, parent)
        self.callback = callback
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mousePressEvent(self, event):
        if self.callback:
            self.callback()
        super().mousePressEvent(event)


# --- ResponsiveLayout using a direct, synchronous approach for thumbnails ---
class ResponsiveLayout(QWidget):
    def __init__(self, parent=None): # Removed thread_pool
        super().__init__(parent)
        self.flowLayout = FlowLayout(self, margin=0, spacing=8)

    def _clear_layout(self):
        while self.flowLayout.count():
            item = self.flowLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_thumbnail_sync(self, label, url):
        """Loads a single thumbnail directly. This will block."""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    label.setPixmap(pixmap.scaled(120, 68, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    label.setText("Invalid")
            else:
                label.setText("Failed")
        except Exception:
            label.setText("Error")

    def addItems(self, items_data, item_type="keyword"):
        self._clear_layout()
        if not items_data:
            return

        if item_type == "keyword":
            for keyword in items_data:
                lbl = QLabel(keyword)
                lbl.setStyleSheet("""
                    background: rgba(67,206,162,0.18);
                    color: #43cea2;
                    border-radius: 7px;
                    padding: 8px 12px;
                    margin: 2px;
                """)
                self.flowLayout.addWidget(lbl)

        elif item_type == "thumbnail":
            for url in items_data:
                thumb_label = ClickableLabel(callback=lambda u=url: webbrowser.open(u))
                thumb_label.setFixedSize(120, 68)
                thumb_label.setScaledContents(True)
                thumb_label.setStyleSheet("border: 1px solid #555; border-radius: 4px; background-color: #333;")
                thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.flowLayout.addWidget(thumb_label)
                # Load image directly and synchronously
                self.load_thumbnail_sync(thumb_label, url)
                QApplication.processEvents() # Allow UI to refresh between downloads

class YouTubeOptimizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.youtube_service = self._get_youtube_service()
        # No longer need a thread pool for this specific task
        self.init_ui()

    def _get_youtube_service(self):
        try:
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=API_KEY
            )
            return youtube
        except Exception as e:
            QMessageBox.critical(self, "API Initialization Error",
                f"Error initializing YouTube API service: {e}\n"
                "Please ensure you have a valid API key and internet connection.")
            return None

    def init_ui(self):
        self.setWindowTitle("YouTube Video Optimizer")
        self.setGeometry(100, 100, 1100, 760)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #232526, stop:1 #414345);
                color: #E0E0E0;
                font-family: 'Arial', sans-serif;
                font-size: 15px;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit, QTextEdit {
                background: #232526;
                color: #F0F0F0;
                border: 2px solid #43cea2;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 16px;
            }
            QPushButton {
                background: none;
            }
            QFrame#cardFrame {
                background: rgba(40,40,40,0.9);
                border-radius: 16px;
                border: 1px solid #333;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(0)
        nav_bar.setContentsMargins(0, 24, 0, 24)
        nav_bar.addStretch(1)
        self.drafting_btn = QPushButton("Ideas")
        self.drafting_btn.setCheckable(True)
        self.drafting_btn.setChecked(True)
        self.drafting_btn.setFixedHeight(48)
        self.drafting_btn.setMinimumWidth(180)
        self.drafting_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43cea2, stop:1 #185a9d);
                color: #fff;
                border-radius: 14px;
                padding: 12px 36px;
                font-size: 18px;
                font-weight: bold;
                border: none;
                margin-right: 28px;
                margin-left: 0px;
            }
            QPushButton:checked, QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #185a9d, stop:1 #43cea2);
                color: #fff;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38bfa2, stop:1 #144a7d);
                color: #fff;
            }
        """)
        self.drafting_btn.clicked.connect(lambda: self.switch_panel(0))
        nav_bar.addWidget(self.drafting_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        nav_bar.addSpacing(28)
        self.results_btn = QPushButton("Search Results")
        self.results_btn.setCheckable(True)
        self.results_btn.setChecked(False)
        self.results_btn.setFixedHeight(48)
        self.results_btn.setMinimumWidth(180)
        self.results_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43cea2, stop:1 #185a9d);
                color: #fff;
                border-radius: 14px;
                padding: 12px 36px;
                font-size: 18px;
                font-weight: bold;
                border: none;
                margin-left: 0px;
                margin-right: 0px;
            }
            QPushButton:checked, QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #185a9d, stop:1 #43cea2);
                color: #fff;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38bfa2, stop:1 #144a7d);
                color: #fff;
            }
        """)
        self.results_btn.clicked.connect(lambda: self.switch_panel(1))
        nav_bar.addWidget(self.results_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        nav_bar.addStretch(1)
        main_layout.addLayout(nav_bar)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._drafting_panel())
        self.stack.addWidget(self._results_panel())
        main_layout.addWidget(self.stack)

    def switch_panel(self, idx):
        self.stack.setCurrentIndex(idx)
        self.drafting_btn.setChecked(idx == 0)
        self.results_btn.setChecked(idx == 1)

    def _drafting_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(18)
        title_label = QLabel("YouTube Video Optimizer")
        title_label.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #43cea2; margin: 10px 0 18px 0;")
        l.addWidget(title_label)
        l.addWidget(QLabel("Video Topic:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g., 'Oppo Find X8 Ultra'")
        l.addWidget(self.topic_input)
        l.addWidget(QLabel("Your Draft Video Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Your exciting video title here")
        l.addWidget(self.title_input)
        l.addWidget(QLabel("Your Initial Keywords (comma-separated):"))
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("keyword1, keyword2, keyword3")
        l.addWidget(self.keywords_input)
        l.addWidget(QLabel("Your Video Script (optional):"))
        self.script_input = QTextEdit()
        self.script_input.setPlaceholderText("Paste your video script here...")
        self.script_input.setMaximumHeight(120)
        l.addWidget(self.script_input)
        self.search_button = QPushButton("🔍 Get Optimization Suggestions")
        self.search_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43cea2, stop:1 #185a9d);
                color: #fff;
                border-radius: 10px;
                padding: 14px 28px;
                font-weight: 600;
                font-size: 17px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38bfa2, stop:1 #144a7d);
            }
        """)
        self.search_button.clicked.connect(self.start_optimization)
        l.addWidget(self.search_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.status_label = QLabel("Enter video topic and click 'Get Suggestions'.")
        self.status_label.setStyleSheet("font-weight: bold; color: #64B5F6; qproperty-alignment: AlignCenter;")
        l.addWidget(self.status_label)
        l.addStretch()
        return w

    def _results_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 20, 24, 24)
        l.setSpacing(10)
        self.output_area = QScrollArea()
        self.output_area.setWidgetResizable(True)
        self.output_content = QWidget()
        self.output_layout = QVBoxLayout(self.output_content)
        self.output_area.setWidget(self.output_content)
        l.addWidget(self.output_area)
        return w

    def start_optimization(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Missing Topic", "Please enter a video topic.")
            return
        self.status_label.setText("🔄 Analyzing... Please wait.")
        self.search_button.setEnabled(False)
        
        self._clear_output_layout()

        self.worker_thread = QThread()
        self.worker = YouTubeWorker(self.youtube_service, topic)
        self.worker.moveToThread(self.worker_thread)
        self.worker.finished.connect(self.display_results)
        self.worker.error.connect(self.display_error)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _clear_output_layout(self):
        if self.output_layout is None:
            return
        while self.output_layout.count():
            child = self.output_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def display_results(self, suggestions):
        self.status_label.setText("✅ Suggestions ready!")
        self.search_button.setEnabled(True)
        
        self._clear_output_layout()

        if not suggestions or not suggestions.get("title_suggestions"):
            self.output_layout.addWidget(QLabel("❌ No suggestions found for this topic."))
            self.switch_panel(1)
            return

        self.output_layout.addWidget(QLabel("📹 Top Video Titles (Click to copy):"))
        for title, views, channel in suggestions["title_suggestions"]:
            card = CardFrame()
            card_layout = QVBoxLayout(card)
            title_lbl = ClickableLabel(
                f"{title}",
                callback=lambda t=title: self.copy_to_clipboard(t)
            )
            title_lbl.setWordWrap(True)
            formatted_views = format_view_count(views)
            views_lbl = QLabel(f"👁️ Views: {formatted_views} by {channel}")
            card_layout.addWidget(title_lbl)
            card_layout.addWidget(views_lbl)
            self.output_layout.addWidget(card)

        if suggestions["keyword_suggestions"]:
            self.output_layout.addWidget(QLabel("🏷️ Suggested Keywords:"))
            kw_card = CardFrame()
            kw_card_layout = QVBoxLayout(kw_card)
            kw_responsive = ResponsiveLayout()
            kw_responsive.addItems(suggestions["keyword_suggestions"], "keyword") 
            kw_card_layout.addWidget(kw_responsive)
            self.output_layout.addWidget(kw_card)

        if suggestions["thumbnail_urls"]:
            self.output_layout.addWidget(QLabel("🖼️ Sample Thumbnails (Click to open):"))
            thumb_card = CardFrame()
            thumb_card_layout = QVBoxLayout(thumb_card)
            thumb_responsive = ResponsiveLayout()
            thumb_responsive.addItems(suggestions["thumbnail_urls"][:10], "thumbnail")
            thumb_card_layout.addWidget(thumb_responsive)
            self.output_layout.addWidget(thumb_card)
        
        self.output_content.adjustSize()
        self.switch_panel(1)

    def copy_to_clipboard(self, text):
        try:
            QApplication.clipboard().setText(text)
            self.status_label.setText("📋 Copied to clipboard!")
            QTimer.singleShot(3000, lambda: self.status_label.setText("✅ Suggestions ready!"))
        except Exception as e:
            print(f"Error copying to clipboard: {e}")

    def display_error(self, message):
        self.status_label.setText("❌ Error occurred.")
        self.search_button.setEnabled(True)
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        # We removed the threadpool, so no need to clear it.
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeOptimizerApp()
    window.show()
    sys.exit(app.exec())
