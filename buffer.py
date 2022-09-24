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

from PyQt6 import QtCore
from PyQt6.QtCore import QThread, QMimeDatabase, QFileSystemWatcher, QTimer
from PyQt6.QtGui import QColor, QIcon
from core.utils import eval_in_emacs, PostGui, get_emacs_vars, interactive, message_to_emacs, get_emacs_func_result
from core.webengine import BrowserBuffer
from pathlib import Path
import copy
import json
import os
import shutil
import subprocess
import time

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
        self.show_icon = None
        self.hide_preview_by_width = False

        self.new_select_file = None
        self.inhibit_mark_change_file = False

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
        
        self.sort_key = "name"
        self.sort_reverse = False

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

        (self.show_hidden_file, self.show_preview, self.show_icon) = get_emacs_vars([
            "eaf-file-manager-show-hidden-file",
            "eaf-file-manager-show-preview",
            "eaf-file-manager-show-icon"])

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
                
        
        self.buffer_widget.eval_js_function(
            '''init''', 
            self.theme_background_color, self.theme_foreground_color, 
            header_color, directory_color, symlink_color, mark_color, select_color, search_match_color, search_keyword_color,
            self.icon_cache_dir, os.path.sep,
            "true" if self.show_preview and self.width_enough_to_show_preview() else "false",
            "true" if self.show_icon else "false",
            self.theme_mode)
        
    def width_enough_to_show_preview(self): 
        (frame_width, _) = get_emacs_func_result("eaf-get-render-size", [])                
        return self.buffer_widget.width() > int(frame_width) * 2 / 3

    @PostGui()
    def handle_append_search(self, file_paths, first_search):
        self.buffer_widget.eval_js_function('''appendSearch''', list(map(lambda file_path: self.get_file_info(file_path, self.url), file_paths)))

        if first_search:
            self.update_preview(file_paths[0])

    @PostGui()
    def handle_finish_search(self, search_dir, search_regex, match_number):
        self.buffer_widget.eval_js_function('''finishSearch''')

        if match_number > 0:
            message_to_emacs("Find {} files that matched '{}'".format(match_number, search_regex))
        else:
            message_to_emacs("No file matched '{}'".format(search_regex))

    def search_directory(self, dir, search_regex):
        self.url = dir

        fd_command = get_fd_command()

        if fd_command != "":
            self.buffer_widget.eval_js_function('''initSearch''', dir, "{} {}".format(fd_command, search_regex))
            thread = FdSearchThread(os.path.expanduser(dir), search_regex, self.filter_file)
        else:
            self.buffer_widget.eval_js_function('''initSearch''', dir, search_regex)
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
            file_suffix = file_info.suffix()
            
            if file_suffix == "vue":
                return "eaf-mime-type-code-html"
            elif file_suffix in ["xls", "xlsx"]:
                return "application-vnd.oasis.opendocument.spreadsheet"
            elif file_suffix in ["ppt", "pptx"]:
                return "application-vnd.oasis.opendocument.presentation"
            elif file_suffix in ["doc", "docx"]:
                return "application-vnd.oasis.opendocument.text"
            elif file_suffix in ["org"]:
                return "application-emacs-org"
            elif file_suffix in ["md"]:
                return "text-markdown"
            else:
                mime = self.mime_db.mimeTypeForFile(file_info).name().replace("/", "-")
                
                if (mime.startswith("text-") or
                    mime == "application-json" or
                    mime == "application-x-yaml" or
                    mime == "application-x-shellscript" or
                    mime == "application-javascript"):
                    mime = "eaf-mime-type-code-html"
                elif mime == "application-x-sharedlib" or mime == "application-xmind":
                    mime = "eaf-mime-type-not-support"
                
                return mime

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

    def get_file_info(self, file_path, current_dir = None):
        file_type = ""
        file_size = ""
        file_bytes = 0

        if os.path.isfile(file_path):
            file_type = "file"
            file_bytes = os.path.getsize(file_path)
            file_size = self.file_size_format(file_bytes)
        elif os.path.isdir(file_path):
            file_type = "directory"
            file_bytes = self.get_dir_file_number(file_path)
            file_size = str(file_bytes)
        elif os.path.islink(file_path):
            file_type = "symlink"
            file_size = "1"

        if current_dir != None:
            current_dir = os.path.abspath(current_dir)
            name = os.path.abspath(file_path).replace(current_dir, "", 1)[1:]
        else:
            name = os.path.basename(file_path)

        file_info = {
            "path": file_path,
            "name": name,
            "extension": os.path.splitext(name)[1],
            "type": file_type,
            "bytes": file_bytes,
            "info": file_size,
            "mark": "",
            "changed": "",
            "match": "",
            "icon": self.generate_file_icon(file_path),
            "mtime": self.get_file_mtime(file_path),
            "ctime": self.get_file_ctime(file_path),
            "atime": self.get_file_atime(file_path)
        }

        return file_info

    def get_file_mtime(self, file_path):
        try:
            return os.path.getmtime(file_path)
        except:
            return 0

    def get_file_ctime(self, file_path):
        try:
            return os.path.getctime(file_path)
        except:
            return 0

    def get_file_atime(self, file_path):
        try:
            return os.path.getatime(file_path)
        except:
            return 0

    def get_file_infos(self, path):
        file_infos = []
        for p in Path(os.path.expanduser(path)).glob("*"):
            if self.filter_file(p.name):
                file_infos.append(self.get_file_info(str(p.absolute())))

        from functools import cmp_to_key
        file_infos.sort(key=cmp_to_key(lambda a, b: self.sort_file_by_key(a, b, "name")))

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

    def sort_file_by_key(self, a, b, key):
        type_sort_weights = ["directory", "file", "symlink", ""]

        a_type_weights = type_sort_weights.index(a["type"])
        b_type_weights = type_sort_weights.index(b["type"])

        if a_type_weights == b_type_weights:
            if a[key] < b[key]:
                return -1
            elif a[key] > b[key]:
                return 1
            else:
                return 0
        else:
            return a_type_weights - b_type_weights

    @QtCore.pyqtSlot()
    def open_select_files(self):
        mark_files = list(filter(lambda f: f["mark"] == "mark", self.vue_get_all_files()))
        if len(mark_files) == 0:
            current_select_file = self.vue_files[self.vue_current_index]["path"]
            if os.path.isdir(current_select_file):
                self.change_directory(current_select_file, "")
            else:
                eval_in_emacs("find-file", [current_select_file])
        else:
            for mark_file in mark_files:
                mark_file_path = mark_file["path"]
                if os.path.isdir(mark_file_path):
                    eval_in_emacs("eaf-open-in-file-manager", [mark_file_path])
                else:
                    eval_in_emacs("find-file", [mark_file_path])
    
    @QtCore.pyqtSlot(str, str)
    def change_directory(self, dir, current_dir):
        self.url = dir

        self.monitor_current_dir()

        eval_in_emacs('eaf--change-default-directory', [self.buffer_id, dir])
        self.change_title("Dir [{}]".format(os.path.sep.join(list(filter(lambda x: x != '', dir.split(os.path.sep)))[-2:])))
        
        self.file_infos = self.get_file_infos(dir)

        self.select_index = 0

        if current_dir != "":
            files = list(map(lambda file: file["path"], self.file_infos))
            self.select_index = files.index(current_dir) if current_dir in files else 0

        self.buffer_widget.eval_js_function('''changePath''', self.url, self.file_infos, self.select_index)

        if len(self.file_infos) > 0:
            self.init_first_file_preview()

        self.fetch_git_log()
        
    @interactive
    def sort_by_created_time(self):
        self.sort_by_file_key("ctime", "ctime")
        message_to_emacs("Sort file by created time.")
        
    @interactive
    def sort_by_modified_time(self): 
        self.sort_by_file_key("mtime", "mtime")
        message_to_emacs("Sort file by modified time.")
    
    @interactive
    def sort_by_access_time(self): 
        self.sort_by_file_key("atime", "atime")
        message_to_emacs("Sort file by access time.")
    
    @interactive
    def sort_by_size(self):
        self.sort_by_file_key("bytes", "bytes")
        message_to_emacs("Sort file by size.")
        
    @interactive
    def sort_by_name(self):
        self.sort_by_file_key("name", "bytes")
        message_to_emacs("Sort file by name.")

    @interactive
    def sort_by_type(self):
        self.sort_by_file_key("extension", "bytes")
        message_to_emacs("Sort file by type.")
        
    def sort_by_file_key(self, key, info_key):
        if key == self.sort_key:
            # If the sorting type is the same as the last time, then the order is reversed.
            self.sort_reverse = not self.sort_reverse
        else:
            # Keep sort order as default value if sorting type is not same as the last time.
            self.sort_reverse = False
            
        self.sort_key = key
        
        select_path = self.file_infos[self.select_index]["path"]
        
        for file_info in self.file_infos:
            file_info["info"] = self.get_file_sort_info(file_info, info_key)
        
        from functools import cmp_to_key
        self.file_infos.sort(key=cmp_to_key(lambda a, b: self.sort_file_by_key(a, b, key)), reverse=self.sort_reverse)
        files = list(map(lambda file: file["path"], self.file_infos))
        self.select_index = files.index(select_path)
        
        self.buffer_widget.eval_js_function('''changePath''', self.url, self.file_infos, self.select_index)
        
    def get_file_sort_info(self, file_info, info_key):
        if info_key == "bytes":
            if file_info["type"] == "file":
                return self.file_size_format(file_info["bytes"])
            elif file_info["type"] == "directory":
                return str(self.get_dir_file_number(file_info["path"]))
            elif file_info["type"] == "symlink":
                return "1"
        else:
            import time
            return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(file_info[info_key]))

    def fetch_git_log(self):
        thread = GitCommitThread(self.url)
        thread.fetch_command_result.connect(self.update_git_log)
        self.fetch_git_log_threads.append(thread)
        thread.start()

    @PostGui()
    def update_git_log(self, log):
        self.buffer_widget.eval_js_function('''updateGitLog''', {"log": log})

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

    def update_preview_info(self, file, file_type, file_mime, file_infos):
        file_html_content = ""
        
        file_size = 0
        
        if file_type == "file":
            file_size = os.path.getsize(file)
            
            if file_mime == "eaf-mime-type-code-html":
                if file_size < 100000:
                    from pygments import highlight
                    from pygments.styles import get_all_styles
                    from pygments.lexers import PythonLexer, get_lexer_for_filename, html
                    from pygments.formatters import HtmlFormatter
                        
                    with open(file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        try:
                            # All styles please look: https://pygments.org/styles/
                            style_name = "monokai" if self.theme_mode == "dark" else "stata-light"
                            
                            if file.endswith(".vue"):
                                file_html_content = highlight(content, html.HtmlLexer(), HtmlFormatter(full=True, style=style_name))
                            else:
                                file_html_content = highlight(content, get_lexer_for_filename(file), HtmlFormatter(full=True, style=style_name))
                        except:
                            file_html_content = highlight(content, PythonLexer(), HtmlFormatter())
                else:
                    file_mime = "eaf-mime-type-code"
        
        self.buffer_widget.eval_js_function('''setPreview''', file, file_type, file_size, file_mime, {"content": file_html_content}, file_infos)

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

        destination_path = os.path.join(get_emacs_func_result("eaf-file-browser-get-destination-path", []), "")

        if mark_number > 0:
            self.move_files = self.vue_get_mark_files()
            self.send_input_message("Move mark files to: ", "move_files", "file", destination_path)
        else:
            self.move_file = self.vue_get_select_file()
            if self.move_file != None:
                self.send_input_message("Move '{}' to: ".format(self.move_file["name"]), "move_file", "file", destination_path)

    @interactive
    def copy_current_or_mark_file(self):
        mark_number = len(self.vue_get_mark_files())

        destination_path = os.path.join(get_emacs_func_result("eaf-file-browser-get-destination-path", []), "")

        if mark_number > 0:
            self.copy_files = self.vue_get_mark_files()
            self.send_input_message("Copy mark files to: ", "copy_files", "file", destination_path)
        else:
            self.copy_file = self.vue_get_select_file()
            if self.copy_file != None:
                self.send_input_message("Copy '{}' to: ".format(self.copy_file["name"]), "copy_file", "file", destination_path)

    @interactive
    def change_path(self):
        self.send_input_message("Change path: ", "change_path", "file", self.url)

    @interactive
    def open_path(self):
        self.send_input_message("Open path: ", "open_path", "file", self.url)
        
    def handle_change_path(self, new_path):
        self.change_directory(new_path, "")

    def handle_open_path(self, new_path):
        eval_in_emacs('eaf-open-in-file-manager', [new_path])
        
    @interactive
    def batch_rename(self):
        directory = os.path.basename(os.path.normpath(self.url))

        all_files = []
        marked_files = []

        for id, f in enumerate(self.vue_get_all_files()):
            f["id"] = id
            all_files.append(f)
            if f["mark"] == "mark":
                marked_files.append(f)

        self.batch_rename_files = all_files

        pending_files = marked_files
        if len(pending_files) == 0:
            pending_files = all_files

        output = []
        for f in pending_files:
            output.append([len(pending_files), f["id"], f["path"], f["name"], f["type"]])
        eval_in_emacs("eaf-file-manager-rename-edit-buffer", [self.buffer_id, directory, json.dumps(output)])

    @interactive
    def toggle_hidden_file(self):
        if self.show_hidden_file:
            message_to_emacs("Hide hidden file")
        else:
            self.inhibit_mark_change_file = True
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

        self.buffer_widget.eval_js_function('''setPreviewOption''', "true" if self.show_preview else "false")

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
    def mark_file_by_extension(self):
        self.send_input_message("Mark file by extension: ", "mark_file_by_extension", "string")
        
    @interactive
    def open_file_with_external_app(self):
        file_info = self.vue_get_select_file()
        if file_info != None:
            # Don't sue subprocess, otherwise external application will exit when you call eaf-stop-process.
            eval_in_emacs("eaf-file-manager-open-file-with-external-app", [file_info["path"]])
            message_to_emacs("Open file by external app '{}'".format(file_info["path"]))

    def refresh(self):
        old_file_info_dict = {}
        
        if not self.inhibit_mark_change_file:
            for file_info in self.file_infos:
                old_file_info_dict[file_info["path"]] = file_info

        if self.new_select_file != None:
            # Select new file if self.new_select_file is not None.
            self.change_directory(self.url, self.new_select_file)
            self.new_select_file = None
        else:
            current_file = self.vue_get_select_file()
            if current_file != None:
                self.change_directory(self.url, current_file["path"])
            else:
                self.change_directory(self.url, "")

        if self.inhibit_mark_change_file:
            self.inherit_mark_change_file = False
        else:
            change_file_indexes = []
            for index, new_file in enumerate(self.file_infos):
                if new_file["path"] in old_file_info_dict:
                    if new_file["mtime"] != old_file_info_dict[new_file["path"]]["mtime"]:
                        change_file_indexes.append(index)
                else:
                    change_file_indexes.append(index)
            self.buffer_widget.eval_js_function("markChangeFiles", change_file_indexes)
            
            QTimer().singleShot(10000, lambda : self.buffer_widget.eval_js_function("cleanChangeFiles", change_file_indexes))

        self.fetch_git_log()

    def batch_rename_confirm(self, new_file_string):
        self.inhibit_mark_change_file = True
        
        new_files = json.loads(new_file_string)

        for [total, id, path, old_file_name, new_file_name] in new_files:
            file_dir = os.path.dirname(path)
            # when run find_files, old and new file name may include "/" or "\".
            old_file_path = os.path.join(file_dir, os.path.basename(old_file_name))
            new_file_path = os.path.join(file_dir, os.path.basename(new_file_name))

            os.rename(old_file_path, new_file_path)

            for i, f in enumerate(self.batch_rename_files):
                if f["id"] == id:
                    self.batch_rename_files[i]["name"] = new_file_name
                    self.batch_rename_files[i]["path"] = new_file_path
                    break

        self.buffer_widget.eval_js_function('''renameFiles''', self.batch_rename_files)

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
        elif callback_tag == "search_file":
            self.handle_search_file(result_content)
        elif callback_tag == "mark_file_by_extension":
            self.handle_mark_file_by_extension(result_content)
        elif callback_tag == "change_path":
            self.handle_change_path(result_content)
        elif callback_tag == "open_path":
            self.handle_open_path(result_content)

    def cancel_input_response(self, callback_tag):
        ''' Cancel input message.'''
        if callback_tag == "open_link":
            self.buffer_widget.cleanup_links_dom()
        elif callback_tag == "search_file":
            self.buffer_widget.eval_js_function('''selectFileByIndex''', self.search_start_index)
            self.buffer_widget.eval_js_function('''setSearchMatchFiles''', [])

    def handle_search_forward(self, callback_tag):
        if callback_tag == "search_file":
            if len(self.search_files) > 0:
                if self.search_files_index >= len(self.search_files) - 1:
                    self.search_files_index = 0
                else:
                    self.search_files_index += 1

                self.buffer_widget.eval_js_function('''selectFileByIndex''', self.search_files[self.search_files_index][0])

    def handle_search_backward(self, callback_tag):
        if callback_tag == "search_file":
            if len(self.search_files) > 0:
                if self.search_files_index <= 0:
                    self.search_files_index = len(self.search_files) - 1
                else:
                    self.search_files_index -= 1

                self.buffer_widget.eval_js_function('''selectFileByIndex''', self.search_files[self.search_files_index][0])

    def handle_search_finish(self, callback_tag):
        if callback_tag == "search_file":
            self.buffer_widget.eval_js_function('''setSearchMatchFiles''', [])

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
    
    def get_mark_file_names(self):
        return list(map(lambda file: file["path"], self.vue_get_mark_files()))
    
    def get_select_file_name(self):
        current_file = self.vue_get_select_file()
        if current_file != None:
            return current_file["path"]
        else:
            return ""

    def vue_get_file_next_to_last_mark(self):
        mark_indexes = []
        for id, f in enumerate(self.vue_files):
            if f["mark"] == "mark":
                mark_indexes.append(id)

        reverse_mark_indexes = copy.deepcopy(mark_indexes)
        reverse_mark_indexes.reverse()
        for i, mark_id in enumerate(reverse_mark_indexes):
            if i < len(reverse_mark_indexes) - 1:
                if reverse_mark_indexes[i] - reverse_mark_indexes[i + 1] > 1:
                    return self.vue_files[reverse_mark_indexes[i] - 1]

        if mark_indexes[0] > 0:
            return self.vue_files[mark_indexes[0] - 1]
        elif mark_indexes[-1] < len(self.vue_files) - 1:
            return self.vue_files[mark_indexes[-1] + 1]
        else:
            return None

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
        next_to_file = self.vue_get_file_next_to_last_mark()
        if next_to_file != None:
            self.new_select_file = next_to_file["path"]

        self.delete_files(self.vue_get_mark_files())
        self.buffer_widget.eval_js_function("removeMarkFiles")

        message_to_emacs("Delete selected files success.")

    def handle_delete_current_file(self):
        file_info = self.vue_get_select_file()
        if file_info != None:
            if self.vue_current_index > 0:
                self.new_select_file = self.vue_files[self.vue_current_index - 1]["path"]

            self.delete_file(file_info)
            self.buffer_widget.eval_js_function("removeSelectFile")

            message_to_emacs("Delete file {} success.".format(file_info["path"]))

    def handle_rename_file(self, new_file_name):
        if new_file_name == self.rename_file_name:
            message_to_emacs("Same as original name, the file name remains unchanged.")
        elif new_file_name in os.listdir(os.path.dirname(self.rename_file_path)):
            self.send_input_message("File name '{}' exists, choose different name: ".format(self.rename_file_name), "rename_file", "string", new_file_name)
        else:
            try:
                new_file_path = os.path.join(os.path.dirname(self.rename_file_path), new_file_name)
                self.new_select_file = new_file_path

                os.rename(self.rename_file_path, new_file_path)

                self.buffer_widget.eval_js_function("rename", self.rename_file_path, new_file_path, new_file_name)

                message_to_emacs("Rename to '{}'".format(new_file_name))
            except:
                import traceback
                message_to_emacs("Error in rename file: " + str(traceback.print_exc()))

    def handle_create_file(self, new_file):
        if new_file in os.listdir(self.url):
            self.send_input_message("File '{}' exists, choose different name: ".format(new_file), "create_file")
        else:
            self.inhibit_mark_change_file = True

            new_file_path = os.path.join(self.url, new_file)
            self.new_select_file = new_file_path # make sure select new file

            with open(new_file_path, "a"):
                os.utime(new_file_path)

            self.buffer_widget.eval_js_function('''addNewFile''', self.get_file_info(new_file_path))

    def handle_create_directory(self, new_directory):
        if new_directory in os.listdir(self.url):
            self.send_input_message("Directory '{}' exists, choose different name: ".format(new_directory), "create_directory")
        else:
            self.inhibit_mark_change_file = True

            new_directory_path = os.path.join(self.url, new_directory)
            self.new_select_file = new_directory_path # make sure select new directory

            try:
                os.makedirs(new_directory_path)
                self.buffer_widget.eval_js_function('''addNewDirectory''', self.get_file_info(new_directory_path))
            except PermissionError:
                message_to_emacs("Insufficient permissions to create directory: {}".format(new_directory))

    def handle_move_file(self, new_file):
        if self.move_file != None:
            if new_file == self.url:
                message_to_emacs("The directory has not changed, file '{}' not moved.".format(self.move_file["name"]))
            else:
                try:
                    if self.vue_current_index > 0:
                        self.new_select_file = self.vue_files[self.vue_current_index - 1]["path"]
            
                    shutil.move(self.move_file["path"], new_file)
                    self.buffer_widget.eval_js_function("removeSelectFile")
            
                    message_to_emacs("Move '{}' to '{}'".format(self.move_file["name"], new_file))
                except:
                    import traceback
                    message_to_emacs("Error in move file: " + str(traceback.print_exc()))

    def handle_move_files(self, new_dir):
        if new_dir == self.url:
            message_to_emacs("The directory has not changed, mark files not moved.")
        elif os.path.isdir(new_dir):
            try:
                next_to_file = self.vue_get_file_next_to_last_mark()
                if next_to_file != None:
                    self.new_select_file = next_to_file["path"]

                for move_file in self.move_files:
                    shutil.move(move_file["path"], new_dir)

                self.buffer_widget.eval_js_function("removeMarkFiles")

                message_to_emacs("Move mark files to '{}'".format(new_dir))
            except:
                import traceback
                message_to_emacs("Error in move files: " + str(traceback.print_exc()))
        else:
            message_to_emacs("'{}' is not directory, abandon movement.")

    def handle_copy_file(self, new_file):
        if self.copy_file != None:
            if new_file == self.url:
                message_to_emacs("The directory has not changed, file '{}' not copyd.".format(self.copy_file["name"]))
            else:
                try:
                    self.copy_to(self.copy_file["path"], new_file)
            
                    self.new_select_file = new_file
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
                    self.copy_to(copy_file["path"], new_dir)

                message_to_emacs("Copy mark files to '{}'".format(new_dir))
            except:
                import traceback
                message_to_emacs("Error in copy files: " + str(traceback.print_exc()))
        else:
            message_to_emacs("'{}' is not directory, abandon copy.")
            
    def copy_to(self, src, dst):
        if os.path.isdir(src):
            if os.path.exists(dst):
                # shutil.copytree is copy content **under** src to dst,
                # so we need create subdirectory at dst directory before copy content.
                dst_dir = os.path.join(dst, os.path.basename(src))
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                shutil.copytree(src=src, dst=dst_dir, dirs_exist_ok=True)
            else:
                shutil.copytree(src=src, dst=dst, dirs_exist_ok=True)
        else:
            shutil.copy(src, dst)

    def handle_open_link(self, result_content):
        marker = result_content.strip()
        file_name = self.buffer_widget.execute_js("Marker.getMarkerText('%s')" % str(marker))
        class_name = self.buffer_widget.execute_js("Marker.getMarkerClass('%s')" % str(marker))

        if class_name == "eaf-file-manager-file-name":
            self.buffer_widget.eval_js_function('''openFileByName''', file_name)
        elif class_name == "eaf-file-manager-preview-file-name":
            self.buffer_widget.eval_js_function('''openPreviewFileByName''', file_name)

        self.buffer_widget.cleanup_links_dom()

    def handle_find_files(self, regex):
        eval_in_emacs("eaf-open", [self.url, "file-manager", "search:{}".format(regex), "always-new"])

    def handle_search_file(self, search_string):
        in_minibuffer = get_emacs_func_result("minibufferp", [])

        if in_minibuffer:
            all_files = list(map(self.pick_search_string, self.vue_get_all_files()))
            self.search_files = list(filter(
                lambda args: not False in list(map(lambda str: self.is_file_match(args[1], str), search_string.split())),
                enumerate(all_files)
            ))
            self.search_files_index = 0

            self.buffer_widget.eval_js_function('''setSearchMatchFiles''', list(map(lambda args: args[0], self.search_files)))

            if len(self.search_files) > 0:
                return self.buffer_widget.eval_js_function('''selectFileByIndex''', self.search_files[self.search_files_index][0])

            # Notify user if no match file found.
            eval_in_emacs("message", ["Did not find a matching file"])
        else:
            message_to_emacs("Select file: {}".format(self.vue_files[self.vue_current_index]['name']))
            self.buffer_widget.eval_js_function('''setSearchMatchFiles''', [])

    def handle_mark_file_by_extension(self, extension):
        self.buffer_widget.eval_js_function('''markFileByExtension''', extension)

    def is_file_match(self, file, search_word):
        return ((len(search_word) > 0 and search_word[0] != "!" and search_word.lower() in file.lower()) or
                (len(search_word) > 0 and search_word[0] == "!" and (not search_word.lower()[1:] in file.lower())))

    def marker_offset_x(self):
        if self.show_icon:
            return -28
        else:
            return -16

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

    def resize_view(self):
        if self.width_enough_to_show_preview():
            if self.show_preview and self.hide_preview_by_width:
                self.buffer_widget.eval_js_function('''setPreviewOption''', "true")
                self.hide_preview_by_width = False
        else:
            if self.show_preview:
                self.buffer_widget.eval_js_function('''setPreviewOption''', "false")
                self.hide_preview_by_width = True

class FetchPreviewInfoThread(QThread):

    fetch_finish = QtCore.pyqtSignal(str, str, str, list)

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
            mime = ""
            file_type = ""
            file_infos = []

            if self.file != "":
                path = Path(self.file)
                mime = self.get_file_mime_callback(str(path.absolute()))

                if path.is_file():
                    file_type = "file"
                    file_infos = [{
                        "mime": mime,
                        "size": os.path.getsize(str(path.absolute()))
                    }]
                elif path.is_dir():
                    file_type = "directory"
                    file_infos = self.get_files_callback(self.file)
                elif path.is_symlink():
                    file_type = "symlink"

            self.fetch_finish.emit(self.file, file_type, mime, file_infos)

class GitCommitThread(QThread):

    fetch_command_result = QtCore.pyqtSignal(str)

    def __init__(self, current_dir):
        QThread.__init__(self)

        self.current_dir = current_dir

    def get_command_result(self, command_string):
        process = subprocess.Popen(command_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        result = process.stdout.readline().decode("utf-8")    # type: ignore
        return os.linesep.join([s for s in result.splitlines() if s])

    def run(self):
        git_log = ""
        git_last_commit = self.get_command_result("cd {}; git log -1 --oneline".format(self.current_dir))

        if git_last_commit != "" and not git_last_commit.startswith("fatal"):
            git_current_branch = self.get_command_result("cd {}; git branch --show-current".format(self.current_dir))
            git_log = "[{}] {}".format(git_current_branch, git_last_commit)

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

        process = subprocess.Popen("{} -c never -I --search-path '{}' {}".format(fd_command, self.search_dir, self.search_regex),
                                   shell=True,
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        while True:
            status = process.poll()
            if status is not None:
                break

            output = process.stdout.readline()    # type: ignore
            if output:
                self.file_paths.append(output.strip().decode("utf-8"))
                self.match_number += 1

                if (time.time() - self.start_time) > self.search_send_duration:
                    self.send_files()
                    self.start_time = time.time()

        self.send_files()

        self.finish_search.emit(self.search_dir, "{} {}".format(get_fd_command(), self.search_regex), self.match_number)
