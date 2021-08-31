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

from PyQt5.QtCore import QUrl, QThread, QMimeDatabase, QFileSystemWatcher
from PyQt5.QtGui import QColor, QIcon
from PyQt5 import QtCore, QtWidgets
from core.webengine import BrowserBuffer
from pathlib import Path
from functools import cmp_to_key
from core.utils import eval_in_emacs, PostGui, get_emacs_vars, interactive, message_to_emacs, get_emacs_func_result
import codecs
import os
import json
import shutil
import time
import copy
import subprocess

def get_fd_command():
    if shutil.which("fd"):
        return "fd"
    elif shutil.which("fdfind"):
        return "fdfind"
    else:
        return ""

class AppBuffer(BrowserBuffer):
    def __init__(self, buffer_id, url, arguments):
        BrowserBuffer.__init__(self, buffer_id, url, arguments, False)

        self.arguments = arguments

        self.vue_files = []
        self.vue_current_index = 0

        self.search_regex = ""
        self.search_start_index = 0

        self.load_index_html(__file__)

        self.show_hidden_file = None
        self.show_preview = None

        self.search_files = []
        self.search_files_index = 0

        self.file_changed_wacher = QFileSystemWatcher()
        self.file_changed_wacher.directoryChanged.connect(lambda path: self.refresh())

        self.mime_db = QMimeDatabase()
        self.icon_cache_dir = os.path.join(os.path.dirname(__file__,), "src", "assets", "icon_cache")
        if not os.path.exists(self.icon_cache_dir):
            os.makedirs(self.icon_cache_dir)

        self.preview_file = None
        self.fetch_preview_info_threads = []
        self.search_file_threads = []
        self.fetch_git_log_threads = []

    def monitor_current_dir(self):
        if len(self.file_changed_wacher.directories()) > 0:
            self.file_changed_wacher.removePaths(self.file_changed_wacher.directories())
        self.file_changed_wacher.addPath(self.url)

    def init_app(self):
        self.init_vars()

        if self.arguments != "":
            if self.arguments.startswith("search:"):
                self.search_regex = self.arguments.split("search:")[1]
                if self.search_regex != "":
                    self.search_directory(self.url, self.search_regex)
                else:
                    self.change_directory(self.url, "")
            elif self.arguments.startswith("jump:"):
                jump_file = self.arguments.split("jump:")[1]
                self.change_directory(self.url, jump_file)
        else:
            self.change_directory(self.url, "")

    def init_first_file_preview(self):
        if self.file_infos == []:
            self.update_preview("")
        else:
            self.update_preview(self.file_infos[self.select_index]["path"])

    def init_vars(self):
        (directory_color, symlink_color, header_color, mark_color, search_match_color, search_keyword_color) = get_emacs_func_result(
            "get-emacs-face-foregrounds",
            ["font-lock-builtin-face",
             "font-lock-keyword-face",
             "font-lock-function-name-face",
             "error",
             "font-lock-string-face",
             "warning"])

        (self.show_hidden_file, self.show_preview) = get_emacs_vars(["eaf-file-manager-show-hidden-file", "eaf-file-manager-show-preview"])

        if self.theme_mode == "dark":
            if self.theme_background_color == "#000000":
                select_color = "#333333"
            else:
                select_color = QColor(self.theme_background_color).darker(120).name()
        else:
            if self.theme_background_color == "#FFFFFF":
                select_color = "#EEEEEE"
            else:
                select_color = QColor(self.theme_background_color).darker(110).name()

        self.buffer_widget.eval_js('''init(\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\")'''.format(
            self.theme_background_color, self.theme_foreground_color, header_color, directory_color, symlink_color, mark_color, select_color, search_match_color, search_keyword_color,
            self.icon_cache_dir, os.path.sep,
            "true" if self.show_preview else "false",
            self.theme_mode))

    @PostGui()
    def handle_append_search(self, file_paths, first_search):
        self.buffer_widget.eval_js('''appendSearch({});'''.format(
            json.dumps(list(map(lambda file_path: self.get_file_info(file_path, self.url), file_paths)))))

        if first_search:
            self.update_preview(file_paths[0])

    @PostGui()
    def handle_finish_search(self, search_dir, search_regex, match_number):
        self.buffer_widget.eval_js('''finishSearch()''')

        if match_number > 0:
            message_to_emacs("Find {} files that matched '{}'".format(match_number, search_regex))
        else:
            message_to_emacs("No file matched '{}'".format(search_regex))

    def search_directory(self, dir, search_regex):
        self.url = dir

        fd_command = get_fd_command()

        if fd_command != "":
            self.buffer_widget.eval_js('''initSearch(\"{}\", \"{}\");'''.format(dir, "{} {}".format(fd_command, search_regex)))
            thread = FdSearchThread(os.path.expanduser(dir), search_regex, self.filter_file)
        else:
            self.buffer_widget.eval_js('''initSearch(\"{}\", \"{}\");'''.format(dir, search_regex))
            thread = PythonSearchThread(os.path.expanduser(dir), search_regex, self.filter_file)
        thread.append_search.connect(self.handle_append_search)
        thread.finish_search.connect(self.handle_finish_search)
        self.search_file_threads.append(thread)
        thread.start()

    def get_file_mime(self, file_path):
        if os.path.isdir(file_path):
            return "directory"
        else:
            file_info = QtCore.QFileInfo(file_path)
            if file_path.endswith(".vue"):
                return "text-plain"
            else:
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

    def get_file_info(self, file_path, current_dir = False):
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

        if current_dir:
            current_dir = os.path.abspath(current_dir)
            name = os.path.abspath(file_path).replace(current_dir, "", 1)[1:]
        else:
            name = os.path.basename(file_path)

        file_info = {
            "path": file_path,
            "name": self.limit_file_name_length(name),
            "type": file_type,
            "size": file_size,
            "mark": "",
            "match": "",
            "icon": self.generate_file_icon(file_path)
        }

        return file_info

    def limit_file_name_length(self, file_name):
        if self.search_regex != "":
            limit_length = 15

            base_name = os.path.basename(file_name)
            new_base_name = base_name
            if len(base_name) > limit_length * 2:
                new_base_name = base_name[:limit_length] + "..." + base_name[len(base_name) - limit_length:]

            if file_name == base_name:
                return new_base_name
            else:
                return os.path.join(os.path.dirname(file_name), new_base_name)
        else:
            return file_name

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

        self.monitor_current_dir()

        eval_in_emacs('eaf--change-default-directory', [dir])
        self.change_title(os.path.basename(dir))

        self.file_infos = self.get_file_infos(dir)

        self.select_index = 0

        if current_dir != "":
            files = list(map(lambda file: file["path"], self.file_infos))
            self.select_index = files.index(current_dir) if current_dir in files else 0

        self.buffer_widget.eval_js('''changePath(\"{}\", {}, {});'''.format(
            self.url,
            json.dumps(self.file_infos),
            self.select_index))

        if len(self.file_infos) > 0:
            self.init_first_file_preview()

        thread = GitCommitThread(dir)
        thread.fetch_command_result.connect(self.update_git_log)
        self.fetch_git_log_threads.append(thread)
        thread.start()

    @PostGui()
    def update_git_log(self, log):
        self.buffer_widget.eval_js('''updateGitLog(\"{}\");'''.format(log))

    @QtCore.pyqtSlot(str)
    def change_up_directory(self, file):
        current_dir = os.path.dirname(file)
        up_directory_path = str(Path(current_dir).parent.absolute())

        if file == self.url:
            # If current directory is empty directory, file will same as current directory.
            self.change_directory(current_dir, file)
        elif up_directory_path != current_dir:
            self.change_directory(up_directory_path, current_dir)
        else:
            eval_in_emacs("message", ["Already in root directory"])

    @QtCore.pyqtSlot(str)
    def update_preview(self, file):
        if self.show_preview:
            self.preview_file = file

            thread = FetchPreviewInfoThread(file, self.get_preview_file, self.get_file_infos, self.get_file_mime)
            thread.fetch_finish.connect(self.update_preview_info)

            self.fetch_preview_info_threads.append(thread)
            thread.start()

    def get_preview_file(self):
        return self.preview_file

    def update_preview_info(self, file, file_type, file_infos):
        self.buffer_widget.eval_js('''setPreview(\"{}\", \"{}\", {});'''.format(file, file_type, file_infos))

    @interactive
    def search_file(self):
        self.search_start_index = self.vue_current_index
        self.send_input_message("Search: ", "search_file", "search")

    @interactive
    def delete_selected_files(self):
        if len(self.vue_get_mark_files()) == 0:
            message_to_emacs("No deletions requested")
        else:
            self.send_input_message("Are you sure you want to delete selected files? ", "delete_file",  "yes-or-no")

    @interactive
    def delete_current_file(self):
        self.send_input_message("Are you sure you want to delete current file? ", "delete_current_file",  "yes-or-no")

    @interactive
    def new_file(self):
        if self.search_regex == "":
            self.send_input_message("Create file: ", "create_file")
        else:
            message_to_emacs("Search page not support new file opeartion.")

    @interactive
    def new_directory(self):
        if self.search_regex == "":
            self.send_input_message("Create directory: ", "create_directory")
        else:
            message_to_emacs("Search page not support new directory opeartion.")

    @interactive
    def copy_dir_path(self):
        eval_in_emacs("kill-new", [self.url])
        message_to_emacs("Copy '{}'".format(self.url))

    @interactive
    def move_current_or_mark_file(self):
        mark_number = len(self.vue_get_mark_files())
        if mark_number > 0:
            self.move_files = self.vue_get_mark_files()
            self.send_input_message("Move mark files to: ", "move_files", "file", self.url)
        else:
            self.move_file = self.vue_get_select_file()
            if self.move_file != None:
                self.send_input_message("Move '{}' to: ".format(self.move_file["name"]), "move_file", "file", self.url)

    @interactive
    def copy_current_or_mark_file(self):
        mark_number = len(self.vue_get_mark_files())
        if mark_number > 0:
            self.copy_files = self.vue_get_mark_files()
            self.send_input_message("Copy mark files to: ", "copy_files", "file", self.url)
        else:
            self.copy_file = self.vue_get_select_file()
            if self.copy_file != None:
                self.send_input_message("Copy '{}' to: ".format(self.copy_file["name"]), "copy_file", "file", self.url)

    @interactive
    def batch_rename(self):
        directory = os.path.basename(os.path.normpath(self.url))

        all_files = []
        marked_files = []
        index = 0

        for f in self.vue_get_all_files():
            f["index"] = index
            all_files.append(f)
            if f["mark"] == "mark":
                marked_files.append(f)
            index += 1

        self.batch_rename_files = all_files

        pending_files = marked_files
        if len(pending_files) == 0:
            pending_files = all_files

        output = []
        for f in pending_files:
            output.append([len(pending_files), f["index"], f["path"], f["name"], f["type"]])
        eval_in_emacs("eaf-file-manager-rename-edit-buffer", [self.buffer_id, directory, json.dumps(output)])

    @interactive
    def toggle_hidden_file(self):
        if self.show_hidden_file:
            message_to_emacs("Hide hidden file")
        else:
            message_to_emacs("Show hidden file")

        self.show_hidden_file = not self.show_hidden_file

        self.refresh()

    @interactive
    def toggle_preview(self):
        if self.show_preview:
            message_to_emacs("Hide file preview.")
        else:
            message_to_emacs("Show file preview.")

        self.show_preview = not self.show_preview

        self.buffer_widget.eval_js('''setPreviewOption(\"{}\")'''.format("true" if self.show_preview else "false"))

        if self.show_preview:
            current_file = self.vue_get_select_file()
            if current_file != None:
                self.update_preview(current_file["path"])

    @interactive
    def find_files(self):
        fd_command = get_fd_command()
        if fd_command != "":
            self.send_input_message("Find file with '{}': ".format(fd_command), "find_files", "string")
        else:
            self.send_input_message("Find file with '*?[]' glob pattern: ", "find_files", "string")

    @interactive
    def refresh_dir(self):
        self.refresh()
        message_to_emacs("Refresh current directory done.")

    @interactive
    def open_current_file_in_new_tab(self):
        current_file = self.vue_get_select_file()
        if current_file != None:
            eval_in_emacs("eaf-open-in-file-manager", [current_file["path"]])

    @interactive
    def open_file(self):
        self.send_input_message("Open file: ", "open_file", "file", self.url)

    def refresh(self):
        current_file = self.vue_get_select_file()
        if current_file != None:
            self.change_directory(self.url, current_file["path"])

    def batch_rename_confirm(self, new_file_string):
        new_files = json.loads(new_file_string)

        for [total, index, path, old_file_name, new_file_name] in new_files:
            file_dir = os.path.dirname(path)
            # when run find_files, old and new file name may include "/" or "\".
            old_file_path = os.path.join(file_dir, os.path.basename(old_file_name))
            new_file_path = os.path.join(file_dir, os.path.basename(new_file_name))

            os.rename(old_file_path, new_file_path)

            for i, f in enumerate(self.batch_rename_files):
                if f["index"] == index:
                    self.batch_rename_files[i]["name"] = new_file_name
                    self.batch_rename_files[i]["path"] = new_file_path
                    break

        self.buffer_widget.eval_js('''renameFiles({})'''.format(json.dumps(self.batch_rename_files)))

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
            self.handle_open_link(result_content)
        elif callback_tag == "find_files":
            self.handle_find_files(result_content)
        elif callback_tag == "open_file":
            self.handle_open_file(result_content)
        elif callback_tag == "search_file":
            self.handle_search_file(result_content)

    def cancel_input_response(self, callback_tag):
        ''' Cancel input message.'''
        if callback_tag == "open_link":
            self.buffer_widget.cleanup_links_dom()
        elif callback_tag == "search_file":
            self.buffer_widget.eval_js('''selectFileByIndex({})'''.format(self.search_start_index))
            self.buffer_widget.eval_js('''setSearchMatchFiles({})'''.format(json.dumps([])))

    def handle_search_forward(self, callback_tag):
        if callback_tag == "search_file":
            if len(self.search_files) > 0:
                if self.search_files_index >= len(self.search_files) - 1:
                    self.search_files_index = 0
                else:
                    self.search_files_index += 1

                self.buffer_widget.eval_js('''selectFileByIndex({})'''.format(self.search_files[self.search_files_index][0]))

    def handle_search_backward(self, callback_tag):
        if callback_tag == "search_file":
            if len(self.search_files) > 0:
                if self.search_files_index <= 0:
                    self.search_files_index = len(self.search_files) - 1
                else:
                    self.search_files_index -= 1

                self.buffer_widget.eval_js('''selectFileByIndex({})'''.format(self.search_files[self.search_files_index][0]))

    def handle_search_finish(self, callback_tag):
        if callback_tag == "search_file":
            self.buffer_widget.eval_js('''setSearchMatchFiles({})'''.format(json.dumps([])))

    def delete_files(self, file_infos):
        for file_info in file_infos:
            self.delete_file(file_info)

    def delete_file(self, file_info):
        if file_info["type"] == "file":
            os.remove(file_info["path"])
        elif file_info["type"] == "directory":
            shutil.rmtree(file_info["path"])

    def vue_get_mark_files(self):
        return list(filter(lambda file: file["mark"] == "mark", self.vue_files)).copy()

    def vue_get_all_files(self):
        return self.vue_files.copy()

    def vue_get_select_file(self):
        try:
            return copy.deepcopy(self.vue_files[self.vue_current_index])
        except:
            return None

    @QtCore.pyqtSlot(list)
    def vue_update_files(self, vue_files):
        self.vue_files = vue_files

    @QtCore.pyqtSlot(int)
    def vue_update_current_index(self, inex):
        self.vue_current_index = inex

    @QtCore.pyqtSlot(str)
    def rename_file(self, file_path):
        self.rename_file_path = file_path
        self.rename_file_name = os.path.basename(file_path)
        self.send_input_message("Rename file name '{}' to: ".format(self.rename_file_name), "rename_file", "string", self.rename_file_name)

    def handle_delete_file(self):
        self.delete_files(self.vue_get_mark_files())
        self.buffer_widget.eval_js("removeMarkFiles();")

        message_to_emacs("Delete selected files success.")

    def handle_delete_current_file(self):
        file_info = self.vue_get_select_file()
        if file_info != None:
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

            self.buffer_widget.eval_js('''addNewFile({})'''.format(json.dumps(self.get_file_info(new_file_path))))

    def handle_create_directory(self, new_directory):
        if new_directory in os.listdir(os.path.dirname(self.url)):
            self.send_input_message("Directory '{}' exists, choose different name: ".format(new_directory), "create_directory")
        else:
            new_directory_path = os.path.join(self.url, new_directory)
            os.makedirs(new_directory_path)

            self.buffer_widget.eval_js('''addNewDirectory({})'''.format(json.dumps(self.get_file_info(new_directory_path))))

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

                self.refresh()

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

    def handle_open_link(self, result_content):
        marker = result_content.strip()
        file_name = self.buffer_widget.execute_js("Marker.getMarkerText('%s')" % str(marker))
        class_name = self.buffer_widget.execute_js("Marker.getMarkerClass('%s')" % str(marker))

        if class_name == "eaf-file-manager-file-name":
            self.buffer_widget.eval_js('''openFileByName(\"{}\")'''.format(file_name))
        elif class_name == "eaf-file-manager-preview-file-name":
            self.buffer_widget.eval_js('''openPreviewFileByName(\"{}\")'''.format(file_name))

        self.buffer_widget.cleanup_links_dom()

    def handle_find_files(self, regex):
        eval_in_emacs("eaf-open", [self.url, "file-manager", "search:{}".format(regex), "always-new"])

    def handle_open_file(self, new_file):
        if os.path.exists(new_file):
            if os.path.isfile(new_file):
                eval_in_emacs("find-file", [new_file])
            elif os.path.isdir(new_file):
                eval_in_emacs("eaf-open-in-file-manager", [new_file])
        else:
            message_to_emacs("File '{}' not exists".format(new_file))

    def handle_search_file(self, search_string):
        if search_string == "":
            self.buffer_widget.eval_js('''selectFileByIndex({})'''.format(self.search_start_index))
            self.buffer_widget.eval_js('''setSearchMatchFiles({})'''.format(json.dumps([])))
        else:
            in_minibuffer = get_emacs_func_result("minibufferp", [])

            if in_minibuffer:

                all_files = list(map(self.pick_search_string, self.vue_get_all_files()))
                self.search_files = list(filter(
                    lambda args: not False in list(map(lambda str: self.is_file_match(args[1], str), search_string.split())),
                    enumerate(all_files)
                ))
                self.search_files_index = 0

                self.buffer_widget.eval_js('''setSearchMatchFiles({})'''.format(json.dumps(
                    list(map(lambda args: args[0], self.search_files))
                )))

                if len(self.search_files) > 0:
                    return self.buffer_widget.eval_js('''selectFileByIndex({})'''.format(self.search_files[self.search_files_index][0]))

                # Notify user if no match file found.
                eval_in_emacs("message", ["Did not find a matching file"])
            else:
                message_to_emacs("Select file: {}".format(self.vue_files[self.vue_current_index]['name']))
                self.buffer_widget.eval_js('''setSearchMatchFiles({})'''.format(json.dumps([])))

    def is_file_match(self, file, search_word):
        return ((len(search_word) > 0 and search_word[0] != "!" and search_word.lower() in file.lower()) or
                (len(search_word) > 0 and search_word[0] == "!" and (not search_word.lower()[1:] in file.lower())))

    def marker_offset_x(self):
        return -28

    def marker_offset_y(self):
        return 4

    def pick_search_string(self, file):
        from pypinyin import pinyin, Style

        file_name = file["name"]

        if self.is_contains_chinese(file_name):
            return ''.join(list(map(lambda x: x[0], pinyin(file_name, style=Style.FIRST_LETTER))))
        else:
            return file_name

    def is_contains_chinese(self, string):
        for _char in string:
            if '\u4e00' <= _char <= '\u9fa5':
                return True
        return False

    def destroy_buffer(self):
        ''' Destroy buffer.'''
        for search_file_thread in self.search_file_threads:
            if search_file_thread.isRunning():
                search_file_thread.quit()
                search_file_thread.wait()

        for fetch_preview_info_thread in self.fetch_preview_info_threads:
            if fetch_preview_info_thread.isRunning():
                fetch_preview_info_thread.quit()
                fetch_preview_info_thread.wait()

        if self.buffer_widget is not None:
            self.buffer_widget.deleteLater()

class FetchPreviewInfoThread(QThread):

    fetch_finish = QtCore.pyqtSignal(str, str, str)

    def __init__(self, file, get_preview_file_callback, get_files_callback, get_file_mime_callback):
        QThread.__init__(self)

        self.file = file
        self.get_preview_file_callback = get_preview_file_callback
        self.get_files_callback = get_files_callback
        self.get_file_mime_callback = get_file_mime_callback

    def run(self):
        # Wait 300 milliseconds, if current preview file is changed, stop fetch thread.
        time.sleep(0.3)
        if self.get_preview_file_callback() == self.file:
            path = ""
            file_type = ""
            file_infos = []

            if self.file != "":
                path = Path(self.file)

                if path.is_file():
                    file_type = "file"
                    file_infos = [{
                        "mime": self.get_file_mime_callback(str(path.absolute())),
                        "size": os.path.getsize(str(path.absolute()))
                    }]
                elif path.is_dir():
                    file_type = "directory"
                    file_infos = self.get_files_callback(self.file)
                elif path.is_symlink():
                    file_type = "symlink"

            self.fetch_finish.emit(self.file, file_type, json.dumps(file_infos))

class GitCommitThread(QThread):

    fetch_command_result = QtCore.pyqtSignal(str)

    def __init__(self, current_dir):
        QThread.__init__(self)

        self.current_dir = current_dir

    def run(self):
        process = subprocess.Popen("cd {}; git log -1 --oneline".format(self.current_dir), shell=True, stdout = subprocess.PIPE)
        process.wait()
        result = process.stdout.readline().decode("utf-8")
        git_log = os.linesep.join([s for s in result.splitlines() if s])

        if git_log.startswith("fatal"):
            git_log = ""
        else:
            git_log = (git_log[:50] + '..') if len(git_log) > 50 else git_log

        self.fetch_command_result.emit(git_log)

class FileSearchThread(QThread):

    append_search = QtCore.pyqtSignal(list, bool)
    finish_search = QtCore.pyqtSignal(str, str, int)

    def __init__(self, search_dir, search_regex, filter_file_callback):
        QThread.__init__(self)

        self.search_dir = search_dir
        self.search_regex = search_regex
        self.filter_file_callback = filter_file_callback

        self.start_time = time.time()
        self.search_send_duration = 0.3
        self.first_search = True
        self.file_paths = []
        self.match_number = 0

    def run(self):
        pass

    def send_files(self):
        if len(self.file_paths) > 0:
            self.append_search.emit(self.file_paths, self.first_search)
            self.first_search = False

            self.file_paths = []

class PythonSearchThread(FileSearchThread):

    def __init__(self, search_dir, search_regex, filter_file_callback):
        FileSearchThread.__init__(self, search_dir, search_regex, filter_file_callback)

    def run(self):
        for p in Path(self.search_dir).rglob(self.search_regex):
            if self.filter_file_callback(p.name):
                self.file_paths.append(str(p.absolute()))
                self.match_number += 1

                if (time.time() - self.start_time) > self.search_send_duration:
                    self.send_files()
                    self.start_time = time.time()

        self.send_files()

        self.finish_search.emit(self.search_dir, self.search_regex, self.match_number)

class FdSearchThread(FileSearchThread):

    def __init__(self, search_dir, search_regex, filter_file_callback):
        FileSearchThread.__init__(self, search_dir, search_regex, filter_file_callback)

    def run(self):
        fd_command = get_fd_command()

        process = subprocess.Popen("{} -c never --search-path '{}' {}".format(fd_command, self.search_dir, self.search_regex),
                                   shell=True,
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        while True:
            status = process.poll()
            if status is not None:
                break

            output = process.stdout.readline()
            if output:
                self.file_paths.append(output.strip().decode("utf-8"))
                self.match_number += 1

                if (time.time() - self.start_time) > self.search_send_duration:
                    self.send_files()
                    self.start_time = time.time()

        self.send_files()

        self.finish_search.emit(self.search_dir, "{} {}".format(get_fd_command(), self.search_regex), self.match_number)
