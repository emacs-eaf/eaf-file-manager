;;; eaf-file-manager.el --- File manager

;; Filename: eaf-file-manager.el
;; Description: File manager
;; Author: Andy Stewart <lazycat.manatee@gmail.com>
;; Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
;; Copyright (C) 2021, Andy Stewart, all rights reserved.
;; Created: 2021-07-31 20:45:09
;; Version: 0.1
;; Last-Updated: Sun Aug 22 22:39:42 2021 (-0400)
;;           By: Mingde (Matthew) Zeng
;; URL: http://www.emacswiki.org/emacs/download/eaf-file-manager.el
;; Keywords:
;; Compatibility: GNU Emacs 28.0.50
;;
;; Features that might be required by this library:
;;
;;
;;

;;; This file is NOT part of GNU Emacs

;;; License
;;
;; This program is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 3, or (at your option)
;; any later version.

;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with this program; see the file COPYING.  If not, write to
;; the Free Software Foundation, Inc., 51 Franklin Street, Fifth
;; Floor, Boston, MA 02110-1301, USA.

;;; Commentary:
;;
;; File manager
;;

;;; Installation:
;;
;; Put eaf-file-manager.el to your load-path.
;; The load-path is usually ~/elisp/.
;; It's set in your ~/.emacs like this:
;; (add-to-list 'load-path (expand-file-name "~/elisp"))
;;
;; And the following to your ~/.emacs startup file.
;;
;; (require 'eaf-file-manager)
;;
;; No need more.

(require 'json)

(defcustom eaf-file-manager-keybinding
  '(("<f12>" . "open_devtools")
    ("h" . "js_up_directory")
    ("j" . "js_select_next_file")
    ("C-n" . "js_select_next_file")
    ("k" . "js_select_prev_file")
    ("C-p" . "js_select_prev_file")
    ("l" . "js_open_current_file")
    ("J" . "js_select_last_file")
    ("K" . "js_select_first_file")
    ("r" . "js_rename_file")
    ("e" . "batch_rename")
    ("<left>" . "js_up_directory")
    ("<down>" . "js_select_next_file")
    ("<up>" . "js_select_prev_file")
    ("<right>" . "js_open_current_file")
    ("f" . "js_open_current_file")
    ("C-m" . "js_open_current_file")
    ("F" . "open_link")
    ("T" . "open_current_file_in_new_tab")
    ("H" . "open_file")
    ("SPC" . "js_scroll_up_select_file")
    ("b" . "js_scroll_down_select_file")
    ("<return>" . "js_open_current_file")
    ("w" . "js_copy_file_name")
    ("W" . "js_copy_file_path")
    ("/" . "copy_dir_path")
    ("n" . "new_file")
    ("N" . "new_directory")
    ("R" . "move_current_or_mark_file")
    ("C" . "copy_current_or_mark_file")
    ("^" . "js_up_directory")
    ("'" . "js_up_directory")
    ("m" . "js_mark_file")
    ("u" . "js_unmark_file")
    ("t" . "js_toggle_mark_file")
    ("U" . "js_unmark_all_files")
    ("x" . "delete_selected_files")
    ("X" . "delete_current_file")
    ("o" . "toggle_hidden_file")
    ("O" . "toggle_preview")
    ("q" . "bury-buffer")
    ("Q" . "close_buffer")
    ("g" . "refresh_dir")
    ("G" . "find_files")
    ("*" . "mark_file_by_extension")
    ("v" . "js_preview_toggle")
    ("," . "js_preview_scroll_up_line")
    ("." . "js_preview_scroll_down_line")
    ("<" . "js_preview_scroll_up")
    (">" . "js_preview_scroll_down")
    ("C-s" . "search_file")
    )
  "The keybinding of EAF File Manager."
  :type 'cons)

(add-to-list 'eaf-app-binding-alist '("file-manager" . eaf-file-manager-keybinding))

(setq eaf-file-manager-module-path (concat (file-name-directory load-file-name) "buffer.py"))
(add-to-list 'eaf-app-module-path-alist '("file-manager" . eaf-file-manager-module-path))

;;;###autoload
(defun eaf-open-file-manager ()
  "Open EAF file manager."
  (interactive)
  (eaf-open "~" "file-manager"))

(defcustom eaf-file-manager-show-hidden-file t
  "If non-nil, opening the EAF File Manager will default to display hidden files."
  :type 'boolean)

(defcustom eaf-file-manager-show-preview t
  "If non-nil, opening the EAF File Manager will default to display file preview."
  :type 'boolean)

(defcustom eaf-file-manager-show-icon t
  "If non-nil, opening the EAF File Manager will default to display file icon."
  :type 'boolean)

(defvar eaf-file-manager-rename-edit-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map (kbd "C-c C-k") #'eaf-file-manager-rename-edit-buffer-cancel)
    (define-key map (kbd "C-c C-c") #'eaf-file-manager-rename-edit-buffer-confirm)
    map))

(defun eaf-file-manager-rename-edit-buffer-cancel ()
  "Cancel EAF Browser focus text input and closes the buffer."
  (interactive)
  (let ((edit-text-buffer (current-buffer))
        (buffer-id eaf--buffer-id))
    (catch 'found-eaf
      (eaf-for-each-eaf-buffer
       (when (string= eaf--buffer-id buffer-id)
         (switch-to-buffer buffer)
         (throw 'found-eaf t))))
    (kill-buffer edit-text-buffer)
    (message "[EAF/file-manager] Rename edit cancelled!")))

(defun eaf--get-text-property (prop string)
  "Do the best to find value of PROP in STRING."
  (let ((n (length string))
        values)
    (dotimes (i n)
      (push (get-text-property i prop new-file-name) values))
    (setq values
          (remove nil (delete-dups values)))
    (when (= (length values) 1)
      (car values))))

(defun eaf-file-browser-get-destination-path ()
  "Get a destination path, which is used for copy or move command."
  (save-window-excursion
    (other-window 1)
    (let ((window-path (if (derived-mode-p 'eaf-mode)
                           (eaf-call-sync "execute_function" eaf--buffer-id "get_url")
                         default-directory)))
      (if (file-regular-p window-path)
          (file-name-directory window-path)
        window-path))))

(defun eaf-file-manager-rename-edit-buffer-confirm ()
  "Confirm input text and send the text to corresponding EAF app."
  (interactive)
  (let* ((new-files (cl-remove-if 'string-empty-p (split-string (buffer-string) "\n")))
         (test-files (delq nil (delete-dups new-files)))
         (buffer-id eaf--buffer-id)
         (files-total-num 0)
         orig-files-total-num files-info
         rename-failed files-info-json)

    (dolist (new-file-name new-files)
      (let* ((total (eaf--get-text-property 'total new-file-name))
             (id (eaf--get-text-property 'id new-file-name))
             (path (eaf--get-text-property 'path new-file-name))
             (orig-file-name (eaf--get-text-property 'name new-file-name))
             (new-file-name (replace-regexp-in-string
                             file-name-invalid-regexp ""
                             (replace-regexp-in-string
                              "^ " ""
                              (substring-no-properties new-file-name)))))
        (unless orig-files-total-num
          (setq orig-files-total-num total))
        (if (or (not orig-file-name)
                (equal (length new-file-name) 0)
                (not (eq (length (replace-regexp-in-string "[^/\\]" "" orig-file-name))
                         (length (replace-regexp-in-string "[^/\\]" "" new-file-name)))))
            (push orig-file-name rename-failed)
          (setq files-total-num (+ files-total-num 1))
          (push (vector total id path orig-file-name new-file-name) files-info))))

    (setq files-info-json (substring-no-properties (json-encode files-info)))

    (if (equal (length new-files) (length test-files))
        (if (> files-total-num orig-files-total-num)
            (message "Error: find extra lines in edit buffer, do nothing.")
          (progn
            (when (> (length files-info) 0)
              (eaf-call-async "execute_function_with_args"
                              eaf--buffer-id
                              "batch_rename_confirm"
                              files-info-json))
            (kill-buffer)
            (catch 'found-eaf
              (eaf-for-each-eaf-buffer
               (when (string= eaf--buffer-id buffer-id)
                 (switch-to-buffer buffer)
                 (throw 'found-eaf t))))
            (cond (rename-failed
                   (message "Rename files finished, fail to rename: %s."
                            (mapconcat (lambda (x)
                                         (propertize (format "%S" x) 'face 'warning))
                                       rename-failed " ")))
                  ((< files-total-num orig-files-total-num)
                   (message "Rename subset files finish."))
                  (t (message "Rename files finish.")))))
      (message "There are multiple files have same name."))))

(defun eaf-file-manager-rename-edit-set-header-line (dir)
  "Set header line."
  (setq header-line-format
        (substitute-command-keys
         (concat
          "\\<eaf-file-manager-rename-edit-mode-map>"
          " EAF/file-manager '" dir "' RENAME EDIT: "
          "Confirm with `\\[eaf-file-manager-rename-edit-buffer-confirm]', "
          "Cancel with `\\[eaf-file-manager-rename-edit-buffer-cancel]'. "
          ))))

(define-derived-mode eaf-file-manager-rename-edit-mode text-mode "EAF/file-manager-rename"
  "The major mode to edit focus text input.")

(defun eaf-file-manager-rename-edit-buffer (buffer-id dir files)
  (let ((edit-text-buffer (generate-new-buffer "eaf-file-manager-rename-edit-buffer")))
    (with-current-buffer edit-text-buffer
      (eaf-file-manager-rename-edit-mode)
      (set (make-local-variable 'eaf--buffer-id) buffer-id)
      (set (make-local-variable 'eaf--files-number) (length (split-string files "\n")))
      (set (make-local-variable 'yank-excluded-properties)
           '(total id path name face))
      (eaf-file-manager-rename-edit-set-header-line dir))
    (switch-to-buffer edit-text-buffer)
    (mapc (lambda (file)
            (let* ((total (elt file 0))
                   (id (elt file 1))
                   (path (elt file 2))
                   (name (elt file 3))
                   (type (elt file 4))
                   (face (cond
                          ((equal type "directory") 'font-lock-builtin-face)
                          ((equal type "symlink") 'font-lock-keyword-face)
                          ((equal type "file") 'default)
                          (t 'default)))
                   (p (list 'total total 'id id
                            'path path 'name name 'face face
                            'front-sticky nil 'rear-nonsticky '(face))))
              (insert (apply #'propertize
                             (concat " " (or (file-name-directory name) ""))
                             'read-only t 'rear-nonsticky '(read-only) p))
              (insert (apply #'propertize (file-name-nondirectory name) p))
              (insert "\n")))
          (json-read-from-string files))
    (goto-char (point-min))
    (forward-char 1)))

(defun eaf-open-in-file-manager (&optional file)
  (interactive)
  (let ((jump-file (or file (buffer-file-name))))
    (cond (jump-file
           (if(file-accessible-directory-p (file-truename jump-file))
               (eaf-open (file-truename jump-file) "file-manager")
             (eaf-open (file-name-directory (file-truename jump-file)) "file-manager" (format "jump:%s" (file-truename jump-file)) t)))
          ((equal major-mode 'eaf-mode)
           (eaf-open (file-name-directory (directory-file-name (file-truename default-directory))) "file-manager"))
          (t
           (eaf-open (file-truename default-directory) "file-manager")))))

(provide 'eaf-file-manager)

;;; eaf-file-manager.el ends here
