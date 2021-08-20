;;; eaf-file-manager.el --- File manager

;; Filename: eaf-file-manager.el
;; Description: File manager
;; Author: Andy Stewart <lazycat.manatee@gmail.com>
;; Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
;; Copyright (C) 2021, Andy Stewart, all rights reserved.
;; Created: 2021-07-31 20:45:09
;; Version: 0.1
;; Last-Updated: 2021-07-31 20:45:09
;;           By: Andy Stewart
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

;;; Customize:
;;
;;
;;
;; All of the above can customize by:
;;      M-x customize-group RET eaf-file-manager RET
;;

;;; Change log:
;;
;; 2021/07/31
;;      * First released.
;;

;;; Acknowledgements:
;;
;;
;;

;;; TODO
;;
;;
;;

;;; Require


;;; Code:

(defcustom eaf-file-manager-keybinding
  '(("<f12>" . "open_devtools")
    ("h" . "js_up_directory")
    ("j" . "js_select_next_file")
    ("k" . "js_select_prev_file")
    ("l" . "js_open_file")
    ("J" . "js_select_last_file")
    ("K" . "js_select_first_file")
    ("r" . "js_rename_file")
    ("e" . "batch_rename")
    ("<left>" . "js_up_directory")
    ("<down>" . "js_select_next_file")
    ("<up>" . "js_select_prev_file")
    ("<right>" . "js_open_file")
    ("f" . "open_link")
    ("SPC" . "js_scroll_up_select_file")
    ("b" . "js_scroll_down_select_file")
    ("<return>" . "js_open_file")
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
    ("q" . "bury-buffer")
    ("g" . "refresh_dir")
    ("G" . "find_files")
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

(defcustom eaf-file-manager-dark-header-color "#EEC900"
  ""
  :type 'string)

(defcustom eaf-file-manager-dark-directory-color "#00B8FF"
  ""
  :type 'string)

(defcustom eaf-file-manager-dark-symlink-color "#46D9FF"
  ""
  :type 'string)

(defcustom eaf-file-manager-dark-select-color "#333333"
  ""
  :type 'string)

(defcustom eaf-file-manager-dark-mark-color "#D63F19"
  ""
  :type 'string)

(defcustom eaf-file-manager-light-header-color "#7E4C8D"
  ""
  :type 'string)

(defcustom eaf-file-manager-light-directory-color "#2257A0"
  ""
  :type 'string)

(defcustom eaf-file-manager-light-symlink-color "#46D9FF"
  ""
  :type 'string)

(defcustom eaf-file-manager-light-select-color "#EEEEEE"
  ""
  :type 'string)

(defcustom eaf-file-manager-light-mark-color "#E11441"
  ""
  :type 'string)

(defcustom eaf-file-manager-show-hidden-file nil
  ""
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

(defun eaf-file-manager-rename-edit-buffer-confirm ()
  "Confirm input text and send the text to corresponding EAF app."
  (interactive)
  (let* ((new-files (cl-remove-if 'string-empty-p (string-lines (buffer-string))))
         (test-files (delq nil (delete-dups (cl-remove-if 'string-empty-p (string-lines (buffer-string))))))
         (buffer-id eaf--buffer-id))
    (if (equal (length new-files) eaf--files-number)
        (if (equal (length new-files) (length test-files))
            (progn
              (eaf-call-async "call_function_with_args" eaf--buffer-id "batch_rename_confirm" (buffer-string))
              (kill-buffer)
              (catch 'found-eaf
                (eaf-for-each-eaf-buffer
                 (when (string= eaf--buffer-id buffer-id)
                   (switch-to-buffer buffer)
                   (throw 'found-eaf t))))
              (message "Rename files finish."))
          (message "There are multiple files have same name."))
      (message "File number are inconsistent (%s %s)" eaf--files-number (length new-files)))))

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
      (set (make-local-variable 'eaf--files-number) (length (string-lines files)))
      (eaf-file-manager-rename-edit-set-header-line dir))
    (switch-to-buffer edit-text-buffer)
    (insert files)
    (goto-char (point-min))))

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
