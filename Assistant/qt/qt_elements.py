
"""
This module contains the elements of the
graphic interface belonging to the
QtAssistant

Copyright (C) 2020
David Josué Marcial Quero
"""

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

import webbrowser
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QMainWindow, QScrollArea,
                             QVBoxLayout, QDialog, QMessageBox,
                             QFileDialog, QDialogButtonBox)

from Assistant import DownloadState, AssistantWarning, CertState


class AssetPath():
    def getQtAsset(path_root, asset_file):
        return (path_root / 'qt' / f"{asset_file}.ui").resolve()

    def getAsset(path_root, icon):
        return str((path_root / 'assets' / icon).resolve())


class AssistantWindow(QMainWindow):
    _window_title = "Assistant - Download Assistant"
    _icon_filename = "Assistant.png"

    close_app = pyqtSignal()

    def __init__(self, path_root):
        super().__init__()
        uic.loadUi(AssetPath.getQtAsset(path_root, 'AssistantWindow'), self)

        self.path_root = path_root
        self._window_icon = AssetPath.getAsset(path_root, self._icon_filename)
        self.about = AboutWindow(path_root)
        self.open_about.triggered.connect(self.about.show)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self._window_title)
        self.setWindowIcon(QIcon(self._window_icon))

        main_scroll = QScrollArea()
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setWidgetResizable(True)

        downloads_widget = QWidget()
        self.downloads_layout = QVBoxLayout()
        self.downloads_layout.setAlignment(Qt.AlignTop)
        downloads_widget.setLayout(self.downloads_layout)

        main_scroll.setWidget(downloads_widget)
        self.setCentralWidget(main_scroll)

    def closeEvent(self, event):
        self.close_app.emit()

    def appendDownload(self, widget):
        self.downloads_layout.addWidget(widget)

    def removeDownload(self, widget):
        self.downloads_layout.removeWidget(widget)

    def displayWarning(self, event):
        messages = {AssistantWarning.MAX_REACHED:
                    {"msg": "You have reached the maximum amount of simultanious dowloads",
                     "title": "Download couldn't be added"},
                    AssistantWarning.DOWNLOAD_EXISTS:
                    {"msg": "There already exists the same download",
                     "title": "Download couldn't be added"},
                    AssistantWarning.NOT_SELECTED:
                    {"msg": "Dowload not selected",
                     "title": "Dowload couldn't be eliminated"},
                    AssistantWarning.FOLDER_NOT_EXISTS:
                    {"msg": "The download location does not exist",
                     "title": "Invalid download location"},
                    AssistantWarning.NOT_A_FOLDER:
                    {"msg": "The download location must be a folder",
                     "title": "Invalid download location"},
                    AssistantWarning.INVALID_NAME:
                    {"msg": "Download name format is invalid",
                     "title": "Download couldn't be saved"}}

        dialog_config = messages[event]
        warning = QMessageBox()
        warning.setIcon(QMessageBox.Warning)

        warning.setText(dialog_config["msg"])
        warning.setWindowTitle(dialog_config["title"])
        warning.setStandardButtons(QMessageBox.Ok)
        return (warning.exec())


class DownloadDialog(QDialog):
    _window_title = "Start new download"
    _icon_filename = "Assistant.png"

    def __init__(self, path_root, batch_size, filename_format):
        super().__init__(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        uic.loadUi(AssetPath.getQtAsset(path_root, 'DownloadDialog'), self)

        self._window_icon = AssetPath.getAsset(path_root, self._icon_filename)
        self.setWindowIcon(QIcon(self._window_icon))

        self._batch_size = batch_size
        self._filename_format = filename_format

        self.updateRange()
        self.batch_no_spin.valueChanged.connect(self.updateRange)

    def updateRange(self):
        current_value = self.batch_no_spin.value()

        r_start = (current_value - 1) * self._batch_size
        r_end = current_value * self._batch_size - 1

        range_text = f"Download certificates {r_start} - {r_end}"
        self.range_label.setText(range_text)


class DownloadItem(QWidget):
    _icon_filename = "Assistant.png"
    _t_icon_filename = "flame.png"
    _details_open = False
    _selected = False

    selected_event = pyqtSignal()
    double_clicked = pyqtSignal()

    def __init__(self, path_root, title, threading=True):
        super().__init__()
        uic.loadUi(AssetPath.getQtAsset(path_root, 'DownloadItem'), self)

        self._window_icon = AssetPath.getAsset(path_root, self._icon_filename)
        self._mt_icon = AssetPath.getAsset(path_root, self._t_icon_filename)

        self.title_label.setText(title)
        self._threaded = threading
        self.initUI()

    def initUI(self):
        self.setObjectName("DownloadItem")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowIcon(QIcon(self._window_icon))

        threading_pixmap = QPixmap(self._mt_icon)
        self.thread_icon.setPixmap(threading_pixmap)

        if not self._threaded:
            self.thread_icon.setHidden(True)

    def mousePressEvent(self, event):
        self.selected_event.emit()
        self.selected = True

    def mouseDoubleClickEvent(self, event):
        if not self.details_open:
            self.openDetails()
            self.double_clicked.emit()

    @property
    def details_open(self):
        return self._details_open

    def closeDetails(self):
        self._details_open = False

    def openDetails(self):
        self._details_open = True

    def setDownloadEvent(self, event):
        outcome = {DownloadState.CREATED: "Download workload created",
                   DownloadState.STARTED: "Initializing download",
                   DownloadState.COMPLETED: "Download completed",
                   DownloadState.SAVED: "Data saved on disc",
                   DownloadState.STOPPED: "Download cancelled"}

        self.setProgressText(outcome[event])

        if event is DownloadState.COMPLETED:
            self.setProgress(99)
            self.setETA('0:00:01')
        elif event is DownloadState.SAVED:
            self.setProgress(100)
            self.setETA('0:00:00')

    def setProgress(self, progress):
        self.progress_bar.setValue(progress)

    def setProgressText(self, text):
        self.progress_label.setText(text)

    def setETA(self, eta):
        self.eta_label.setText(eta)

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, selected):
        self._selected = selected

        if selected:
            self.setStyleSheet("""
                QWidget#DownloadItem {
                    border-radius: 4px;
                    background-color: #03A9F4
                }""")
        else:
            self.setStyleSheet("")

    def deselect(self):
        self.selected = False

    def askOverwrite(self):
        proceed = QMessageBox()
        proceed.setIcon(QMessageBox.Question)

        proceed.setText("Overwrite existing namesake file?")

        proceed.setWindowTitle("Confirm overwritting")
        proceed.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        return(proceed.exec())


class DownloadDetails(QWidget):
    _window_title = "Download details"
    _icon_filename = "Assistant.png"

    closed_window = pyqtSignal()

    def __init__(self, path_root):
        super().__init__()
        uic.loadUi(AssetPath.getQtAsset(path_root, 'DownloadDetails'), self)
        self._window_icon = AssetPath.getAsset(path_root, self._icon_filename)
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon(self._window_icon))

    def updateElapsed(self, elapsed):
        self.elapsed_time.setText(elapsed)

    def initOpTab(self, start_time, remaining_time=None, completion_time=None,
                  avg_speed=None):
        self.start_time.setText(start_time)
        self.remaining_time.setText(remaining_time or 'N/A')
        self.completion_time.setText(completion_time or 'N/A')
        self.speed.setText(avg_speed or 'N/A')

    def initBatchTab(self, batch_size, log,
                     downloaded, failed, not_found):
        display_log = []

        for record_no, record in log:
            record_msg = ""
            if record is CertState.NOT_FOUND:
                record_msg = "Does not exist"
            elif record is CertState.FAILED:
                record_msg = "Download failed"

            if record is not CertState.DOWNLOADED:
                display_log.append(f"Certificate {record_no}: {record_msg}")

        self.download_log.setPlainText('\n'.join(display_log))

        total_certs = failed + not_found + downloaded
        self.not_found.setText(f"{not_found}/{batch_size}")
        self.failed.setText(f"{failed}/{batch_size}")
        self.downloaded.setText(f"{downloaded}/{batch_size}")
        self.fetched.setText(f"{total_certs}/{batch_size}")

    def initFileTab(self, file_name=None, file_location=None,
                    file_size=None, sha_one=None, md5=None):
        self.filename.setText(file_name or 'N/A')
        self.location.setText(file_location or 'N/A')
        self.size.setText(file_size or 'N/A')
        self.sha_one.setText(sha_one or 'N/A')
        self.md5.setText(md5 or 'N/A')

    def closeEvent(self, event):
        self.closed_window.emit()


class AssistantSettings(QWidget):
    _icon_filename = "Assistant.png"
    saved_settings = pyqtSignal(str, str, int)

    def __init__(self, path_root, folder, filename, batch_size):
        super().__init__()
        uic.loadUi(AssetPath.getQtAsset(path_root, 'AssistantSettings'), self)
        self._window_icon = AssetPath.getAsset(path_root, self._icon_filename)

        self.folder = folder
        self.absolute_path = Path(folder).resolve()
        self.filename = filename
        self.batch_size = batch_size
        self.initUI()

    def initUI(self):
        self.setWindowFlags(self.windowFlags()
                            | Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(QIcon(self._window_icon))
        self.folder_button.setText(self.folder)
        self.absolute_folder.setText(str(self.absolute_path))
        self.filename_format.setPlainText(self.filename)
        self.batch_size_spin.setValue(self.batch_size)

        self.folder_button.clicked.connect(self.chooseLocation)

        save_button = self.button_box.button(QDialogButtonBox.Save)
        save_button.clicked.connect(self.saveSettings)

    def chooseLocation(self):
        self.file_chooser = QFileDialog()
        self.file_chooser.setFileMode(QFileDialog.Directory)

        if self.file_chooser.exec():
            new_location = self.file_chooser.directory()

            self.absolute_path = Path(new_location.path()).resolve()
            self.folder = self.absolute_path.name

            self.folder_button.setText(self.folder)
            self.absolute_folder.setText(str(self.absolute_path))

    def saveSettings(self):
        self.close()
        self.saved_settings.emit(str(self.absolute_path),
                                 self.filename_format.toPlainText(),
                                 self.batch_size_spin.value())


class AboutWindow(QWidget):
    _window_title = "About Assistant"
    _icon_filename = "about_icon.png"

    _app_name = "Assistant"
    _app_version = "Version 0.4a"
    _app_desc = "An assistant for the download of High School certificates"
    _copyright = "Copyright (C) 2020"
    _copyright_holder = "David Josué Marcial Quero"
    _website = "https://github.com/josue-quero/Assistant"

    def __init__(self, path_root):
        super().__init__()
        uic.loadUi(AssetPath.getQtAsset(path_root, 'AboutWindow'), self)
        self._about_icon = AssetPath.getAsset(path_root, self._icon_filename)
        self.initUI()

    def initUI(self):
        app_info = {self.app_name: self._app_name,
                    self.version_label: self._app_version,
                    self.desc_label: self._app_desc,
                    self.copy_label: self._copyright,
                    self.author_label: self._copyright_holder}

        self.setWindowTitle(self._window_title)
        self.setWindowIcon(QIcon(self._about_icon))

        icon_pixmap = QPixmap(self._about_icon)
        self.icon_label.setPixmap(icon_pixmap)

        for attr in app_info:
            attr.setText(app_info[attr])

        self.siteButton.clicked.connect(self.openWebsite)

    def openWebsite(self):
        webbrowser.open(self._website)
