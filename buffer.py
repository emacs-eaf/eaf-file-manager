#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Andy Stewart
#
# Author:     Andy Stewart <lazycat.manatee@gmail.com>
# Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import QUrl, QThread, QMimeDatabase
from PyQt5.QtGui import QColor, QIcon
from PyQt5 import QtCore, QtWidgets
from core.webengine import BrowserBuffer
from core.utils import get_emacs_var, interactive, message_to_emacs
from pathlib import Path
from functools import cmp_to_key
from core.utils import eval_in_emacs, PostGui, get_emacs_var
import codecs
import os
import json
import shutil

class AppBuffer(BrowserBuffer):
    def __init__(self, buffer_id, url, arguments):
        BrowserBuffer.__init__(self, buffer_id, url, arguments, False)

        self.arguments = arguments

        self.load_index_html(__file__)

        self.show_hidden_file = get_emacs_var("eaf-file-manager-show-hidden-file")

        self.mime_db = QMimeDatabase()
        self.icon_cache_dir = os.path.join(os.path.dirname(__file__,), "src", "assets", "icon_cache")
        if not os.path.exists(self.icon_cache_dir):
            os.makedirs(self.icon_cache_dir)

        self.fetch_preview_info_thread = None

    def init_app(self):
        self.buffer_widget.execute_js('''initIconCacheDir(\"{}\", \"{}\")'''.format(self.icon_cache_dir, os.path.sep))

        if get_emacs_var("eaf-emacs-theme-mode") == "dark":
            if get_emacs_var("eaf-emacs-theme-background-color") == "#000000":
                select_color = get_emacs_var("eaf-file-manager-dark-select-color")
            else:
                select_color = QColor(get_emacs_var("eaf-emacs-theme-background-color")).darker(120).name()

            self.buffer_widget.execute_js('''initColors(\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\")'''.format(
                get_emacs_var("eaf-emacs-theme-background-color"),
                get_emacs_var("eaf-emacs-theme-foreground-color"),
                get_emacs_var("eaf-file-manager-dark-header-color"),
                get_emacs_var("eaf-file-manager-dark-directory-color"),
                get_emacs_var("eaf-file-manager-dark-symlink-color"),
                get_emacs_var("eaf-file-manager-dark-mark-color"),
                select_color
            ))
        else:
            if get_emacs_var("eaf-emacs-theme-background-color") == "#FFFFFF":
                select_color = get_emacs_var("eaf-file-manager-light-select-color")
            else:
                select_color = QColor(get_emacs_var("eaf-emacs-theme-background-color")).darker(110).name()

            self.buffer_widget.execute_js('''initColors(\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\")'''.format(
                get_emacs_var("eaf-emacs-theme-background-color"),
                get_emacs_var("eaf-emacs-theme-foreground-color"),
                get_emacs_var("eaf-file-manager-light-header-color"),
                get_emacs_var("eaf-file-manager-light-directory-color"),
                get_emacs_var("eaf-file-manager-light-symlink-color"),
                get_emacs_var("eaf-file-manager-light-mark-color"),
                select_color
            ))

        if self.arguments != "":
            if self.arguments.startswith("search:"):
                search_regex = self.arguments.split("search:")[1]
                if search_regex != "":
                    self.search_directory(self.url, search_regex)
                else:
                    self.change_directory(self.url, "")
            elif self.arguments.startswith("jump:"):
                jump_file = self.arguments.split("jump:")[1]
                self.change_directory(self.url, jump_file)
        else:
            self.change_directory(self.url, "")

    def search_directory(self, dir, search_regex):
        file_infos = []
        for p in Path(os.path.expanduser(dir)).rglob(search_regex):
            if self.filter_file(p.name):
                file_infos.append(self.get_file_info(str(p.absolute())))

        file_infos.sort(key=cmp_to_key(self.file_compare))

        print(file_infos)

        select_index = 0

        self.buffer_widget.execute_js('''changePath(\"{}\", {}, {});'''.format(
            self.url,
            json.dumps(file_infos),
            select_index))

        if file_infos == []:
            self.update_preview("")
        else:
            self.update_preview(file_infos[select_index]["path"])

    def get_file_mime(self, file_path):
        if os.path.isdir(file_path):
            return "directory"
        else:
            file_info = QtCore.QFileInfo(file_path)
            return self.mime_db.mimeTypeForFile(file_info).name().replace("/", "-")

    def generate_file_icon(self, file_path):
        file_mime = self.get_file_mime(file_path)
        icon_name = "{}.{}".format(file_mime, "png")
        icon_path = os.path.join(self.icon_cache_dir, icon_name)

        if not os.path.exists(icon_path):
            if file_mime == "directory":
                icon = QIcon.fromTheme("folder")
            else:
                icon = QIcon.fromTheme(file_mime, QIcon("text-plain"))

                # If nothing match, icon size is empty.
                # Then we use fallback icon.
                if icon.availableSizes() == []:
                    icon = QIcon.fromTheme("text-plain")

            icon.pixmap(64, 64).save(icon_path)

        return icon_name

    def get_file_info(self, file_path):
        file_type = ""
        file_size = ""

        if os.path.isfile(file_path):
            file_type = "file"
            file_size = self.file_size_format(os.path.getsize(file_path))
        elif os.path.isdir(file_path):
            file_type = "directory"
            file_size = str(self.get_dir_file_number(file_path))
        elif os.path.islink(file_path):
            file_type = "symlink"
            file_size = "1"

        file_info = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "type": file_type,
            "size": file_size,
            "mark": "",
            "icon": self.generate_file_icon(file_path)
        }

        return file_info

    def get_file_infos(self, path):
        file_infos = []
        for p in Path(os.path.expanduser(path)).glob("*"):
            if self.filter_file(p.name):
                file_infos.append(self.get_file_info(str(p.absolute())))

        file_infos.sort(key=cmp_to_key(self.file_compare))

        return file_infos

    def filter_file(self, file_name):
        return self.show_hidden_file or (not file_name.startswith("."))

    def file_size_format(self, num, suffix='B'):
        for unit in ['','K','M','G','T','P','E','Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def get_dir_file_number(self, dir):
        try:
            return len(list(filter(lambda f: self.filter_file(f), (os.listdir(dir)))))
        except PermissionError:
            return 0

    def file_compare(self, a, b):
        type_sort_weights = ["directory", "file", "symlink", ""]

        a_type_weights = type_sort_weights.index(a["type"])
        b_type_weights = type_sort_weights.index(b["type"])

        if a_type_weights == b_type_weights:
            if a["name"] < b["name"]:
                return -1
            elif a["name"] > b["name"]:
                return 1
            else:
                return 0
        else:
            return a_type_weights - b_type_weights

    @QtCore.pyqtSlot(str, str)
    def change_directory(self, dir, current_dir):
        self.url = dir

        eval_in_emacs('eaf--change-default-directory', [dir])
        self.change_title(os.path.basename(dir))

        file_infos = self.get_file_infos(dir)

        if current_dir == "" and len(file_infos) == 0:
            eval_in_emacs("message", ["Nothing in {}, no need to enter directory.".format(dir)])
        else:
            select_index = 0

            if current_dir != "":
                files = list(map(lambda file: file["path"], file_infos))
                select_index = files.index(current_dir)

            self.buffer_widget.execute_js('''changePath(\"{}\", {}, {});'''.format(
                self.url,
                json.dumps(file_infos),
                select_index))

            if file_infos == []:
                self.update_preview("")
            else:
                self.update_preview(file_infos[select_index]["path"])

    @QtCore.pyqtSlot(str)
    def change_up_directory(self, file):
        current_dir = os.path.dirname(file)
        up_directory_path = Path(current_dir).parent.absolute()
        if up_directory_path != current_dir:
            self.change_directory(up_directory_path, current_dir)
        else:
            eval_in_emacs("message", ["Already in root directory"])

    @QtCore.pyqtSlot(str)
    def update_preview(self, file):
        self.exit_preview_thread()

        self.fetch_preview_info_thread = FetchPreviewInfoThread(file, self.get_file_infos, self.get_file_mime)
        self.fetch_preview_info_thread.fetch_finish.connect(self.update_preview_info)
        self.fetch_preview_info_thread.start()

    def exit_preview_thread(self):
        if self.fetch_preview_info_thread != None and self.fetch_preview_info_thread.isRunning():
            # We need call "quit" and then call "wait" function to quit thread safely.
            # Otherwise will cause crash.
            self.fetch_preview_info_thread.quit()
            self.fetch_preview_info_thread.wait()

    def update_preview_info(self, file, file_type, file_infos):
        self.buffer_widget.execute_js('''setPreview(\"{}\", \"{}\", {});'''.format(file, file_type, file_infos))

    def destroy_buffer(self):
        self.exit_preview_thread()

    @interactive
    def delete_selected_files(self):
        if self.buffer_widget.execute_js("getMarkFileNumber();") == 0:
            message_to_emacs("No deletions requested")
        else:
            self.send_input_message("Are you sure you want to delete selected files?", "delete_file",  "yes-or-no")

    @interactive
    def delete_current_file(self):
        self.send_input_message("Are you sure you want to delete current file?", "delete_current_file",  "yes-or-no")

    @interactive
    def new_file(self):
        self.send_input_message("Create file: ", "create_file")

    @interactive
    def new_directory(self):
        self.send_input_message("Create directory: ", "create_directory")

    @interactive
    def copy_dir_path(self):
        eval_in_emacs("kill-new", [self.url])
        message_to_emacs("Copy '{}'".format(self.url))

    @interactive
    def move_current_or_mark_file(self):
        mark_number = self.buffer_widget.execute_js("getMarkFileNumber();")
        if mark_number > 0:
            self.move_files = self.buffer_widget.execute_js("getMarkFiles();")
            self.send_input_message("Move mark files to: ", "move_files", "file", self.url)
        else:
            self.move_file = self.buffer_widget.execute_js("getCurrentFile();")
            self.send_input_message("Move '{}' to: ".format(self.move_file["name"]), "move_file", "file", self.url)

    @interactive
    def copy_current_or_mark_file(self):
        mark_number = self.buffer_widget.execute_js("getMarkFileNumber();")
        if mark_number > 0:
            self.copy_files = self.buffer_widget.execute_js("getMarkFiles();")
            self.send_input_message("Copy mark files to: ", "copy_files", "file", self.url)
        else:
            self.copy_file = self.buffer_widget.execute_js("getCurrentFile();")
            self.send_input_message("Copy '{}' to: ".format(self.copy_file["name"]), "copy_file", "file", self.url)

    @interactive
    def batch_rename(self):
        self.batch_rename_files = self.buffer_widget.execute_js("getAllFiles();")
        files = "\n".join(map(lambda file: file["name"], self.batch_rename_files))
        eval_in_emacs("eaf-file-manager-rename-edit-buffer", [self.buffer_id, os.path.basename(os.path.normpath(self.url)), files])

    @interactive
    def toggle_hidden_file(self):
        if self.show_hidden_file:
            message_to_emacs("Show hidden file")
        else:
            message_to_emacs("Hide hidden file")

        self.show_hidden_file = not self.show_hidden_file

        self.change_directory(self.url, "")

    @interactive
    def find_files(self):
        self.send_input_message("Find file with regexp: ", "find_files", "string")

    @interactive
    def refresh_dir(self):
        self.change_directory(self.url, "")
        message_to_emacs("Refresh current directory done.")

    def batch_rename_confirm(self, new_file_string):
        new_files = new_file_string.split("\n")

        file_index = 0
        for old_file in self.batch_rename_files:
            old_file_path = old_file["path"]
            old_file_dir = os.path.dirname(old_file_path)
            new_file_name = new_files[file_index]
            new_file_path = os.path.join(old_file_dir, new_file_name)

            os.rename(old_file_path, new_file_path)

            self.batch_rename_files[file_index]["name"] = new_file_name
            self.batch_rename_files[file_index]["path"] = new_file_path

            file_index += 1

        self.buffer_widget.execute_js('''renameFiles({})'''.format(json.dumps(self.batch_rename_files)))

    def handle_input_response(self, callback_tag, result_content):
        if callback_tag == "delete_file":
            self.handle_delete_file()
        elif callback_tag == "delete_current_file":
            self.handle_delete_current_file()
        elif callback_tag == "rename_file":
            self.handle_rename_file(result_content)
        elif callback_tag == "create_file":
            self.handle_create_file(result_content)
        elif callback_tag == "create_directory":
            self.handle_create_directory(result_content)
        elif callback_tag == "move_file":
            self.handle_move_file(result_content)
        elif callback_tag == "move_files":
            self.handle_move_files(result_content)
        elif callback_tag == "copy_file":
            self.handle_copy_file(result_content)
        elif callback_tag == "copy_files":
            self.handle_copy_files(result_content)
        elif callback_tag == "open_link":
            self.buffer_widget._open_link(result_content.strip())
        elif callback_tag == "find_files":
            self.handle_find_files(result_content)

    def cancel_input_response(self, callback_tag):
        ''' Cancel input message.'''
        if callback_tag == "open_link":
            self.buffer_widget.cleanup_links_dom()

    def delete_files(self, file_infos):
        for file_info in file_infos:
            self.delete_file(file_info)

    def delete_file(self, file_info):
        if file_info["type"] == "file":
            os.remove(file_info["path"])
        elif file_info["type"] == "directory":
            shutil.rmtree(file_info["path"])

    @QtCore.pyqtSlot(str)
    def rename_file(self, file_path):
        self.rename_file_path = file_path
        self.rename_file_name = os.path.basename(file_path)
        self.send_input_message("Rename file name '{}' to: ".format(self.rename_file_name), "rename_file", "string", self.rename_file_name)

    def handle_delete_file(self):
        self.delete_files(self.buffer_widget.execute_js("getMarkFiles();"))
        self.buffer_widget.eval_js("removeMarkFiles();")

        message_to_emacs("Delete selected files success.")

    def handle_delete_current_file(self):
        file_info = self.buffer_widget.execute_js("getSelectFile();")
        self.delete_file(file_info)
        self.buffer_widget.eval_js("removeSelectFile();")

        message_to_emacs("Delete file {} success.".format(file_info["path"]))

    def handle_rename_file(self, new_file_name):
        if new_file_name == self.rename_file_name:
            message_to_emacs("Same as original name, the file name remains unchanged.")
        elif new_file_name in os.listdir(os.path.dirname(self.rename_file_path)):
            self.send_input_message("File name '{}' exists, choose different name: ".format(self.rename_file_name), "rename_file", "string", new_file_name)
        else:
            try:
                new_file_path = os.path.join(os.path.dirname(self.rename_file_path), new_file_name)
                os.rename(self.rename_file_path, new_file_path)

                self.buffer_widget.eval_js("rename(\"{}\", \"{}\", \"{}\");".format(self.rename_file_path, new_file_path, new_file_name))

                message_to_emacs("Rename to '{}'".format(new_file_name))
            except:
                import traceback
                message_to_emacs("Error in rename file: " + str(traceback.print_exc()))

    def handle_create_file(self, new_file):
        if new_file in os.listdir(os.path.dirname(self.url)):
            self.send_input_message("File '{}' exists, choose different name: ".format(new_file), "create_file")
        else:
            new_file_path = os.path.join(self.url, new_file)
            with open(new_file_path, "a"):
                os.utime(new_file_path)

            print("Create file: ", new_file_path)

            self.buffer_widget.execute_js('''addNewFile({})'''.format(json.dumps(self.get_file_info(new_file_path))))

    def handle_create_directory(self, new_directory):
        if new_directory in os.listdir(os.path.dirname(self.url)):
            self.send_input_message("Directory '{}' exists, choose different name: ".format(new_directory), "create_directory")
        else:
            new_directory_path = os.path.join(self.url, new_directory)
            os.makedirs(new_directory_path)

            print("Create directory: ", new_directory_path)

            self.buffer_widget.execute_js('''addNewDirectory({})'''.format(json.dumps(self.get_file_info(new_directory_path))))

    def handle_move_file(self, new_file):
        if new_file == self.url:
            message_to_emacs("The directory has not changed, file '{}' not moved.".format(self.move_file["name"]))
        else:
            try:
                shutil.move(self.move_file["path"], new_file)
                self.buffer_widget.eval_js("removeSelectFile();")

                message_to_emacs("Move '{}' to '{}'".format(self.move_file["name"], new_file))
            except:
                import traceback
                message_to_emacs("Error in move file: " + str(traceback.print_exc()))

    def handle_move_files(self, new_dir):
        if new_dir == self.url:
            message_to_emacs("The directory has not changed, mark files not moved.")
        elif os.path.isdir(new_dir):
            try:
                for move_file in self.move_files:
                    shutil.move(move_file["path"], new_dir)

                self.buffer_widget.eval_js("removeMarkFiles();")

                message_to_emacs("Move mark files to '{}'".format(new_dir))
            except:
                import traceback
                message_to_emacs("Error in move files: " + str(traceback.print_exc()))
        else:
            message_to_emacs("'{}' is not directory, abandon movement.")

    def handle_copy_file(self, new_file):
        if new_file == self.url:
            message_to_emacs("The directory has not changed, file '{}' not copyd.".format(self.copy_file["name"]))
        else:
            try:
                if os.path.isdir(self.copy_file["path"]):
                    shutil.copytree(src=self.copy_file["path"], dst=new_file, dirs_exist_ok=True)
                else:
                    shutil.copy(self.copy_file["path"], new_file)

                message_to_emacs("Copy '{}' to '{}'".format(self.copy_file["name"], new_file))
            except:
                import traceback
                message_to_emacs("Error in copy file: " + str(traceback.print_exc()))

    def handle_copy_files(self, new_dir):
        if new_dir == self.url:
            message_to_emacs("The directory has not changed, mark files not copyd.")
        elif os.path.isdir(new_dir):
            try:
                for copy_file in self.copy_files:
                    if os.path.isdir(copy_file["path"]):
                        shutil.copytree(src=copy_file["path"], dst=new_dir, dirs_exist_ok=True)
                    else:
                        shutil.copy(copy_file["path"], new_dir)

                message_to_emacs("Copy mark files to '{}'".format(new_dir))
            except:
                import traceback
                message_to_emacs("Error in copy files: " + str(traceback.print_exc()))
        else:
            message_to_emacs("'{}' is not directory, abandon copy.")

    def handle_find_files(self, regex):
        eval_in_emacs("eaf-open", [self.url, "file-manager", "search:{}".format(regex), "always-new"])

class FetchPreviewInfoThread(QThread):

    fetch_finish = QtCore.pyqtSignal(str, str, str)

    def __init__(self, file, get_files_callback, get_file_mime_callback):
        QThread.__init__(self)

        self.file = file
        self.get_files_callback = get_files_callback
        self.get_file_mime_callback = get_file_mime_callback

    def run(self):
        path = ""
        file_type = ""
        file_infos = []

        if self.file != "":
            path = Path(self.file)

            if path.is_file():
                mime = self.get_file_mime_callback(str(path.absolute()))

                content = ""
                if mime.startswith("text-") and mime != "text-html":
                    with codecs.open(str(path.absolute()), 'r', encoding='utf-8', errors='ignore') as f:
                        # Limit read 50kb
                        content = f.read(1024 * 50)

                file_type = "file"
                file_infos = [{
                    "mime": mime,
                    "content": content
                }]
            elif path.is_dir():
                file_type = "directory"
                file_infos = self.get_files_callback(self.file)
            elif path.is_symlink():
                file_type = "symlink"

        self.fetch_finish.emit(self.file, file_type, json.dumps(file_infos))
