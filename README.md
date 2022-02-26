### EAF File Manager
<p align="center">
  <img width="800" src="./screenshot-file.png">
</p>

<p align="center">
  <img width="800" src="./screenshot-pdf.png">
</p>

<p align="center">
  <img width="800" src="./screenshot-image.png">
</p>

<p align="center">
  <img width="800" src="./screenshot-music.png">
</p>

File manager application for the [Emacs Application Framework](https://github.com/emacs-eaf/emacs-application-framework).

### Load application

[Install EAF](https://github.com/emacs-eaf/emacs-application-framework#install) first, then add below code in your emacs config:

```Elisp
(add-to-list 'load-path "~/.emacs.d/site-lisp/emacs-application-framework/")
(require 'eaf)
(require 'eaf-file-manager)
```

### The keybinding of EAF File Manager.

### The keybinding of EAF File Manager.

### The keybinding of EAF File Manager.

| Key   | Event   |
| :---- | :------ |
| `<f12>` | open_devtools |
| `h` | js_up_directory |
| `j` | js_select_next_file |
| `C-n` | js_select_next_file |
| `k` | js_select_prev_file |
| `C-p` | js_select_prev_file |
| `l` | js_open_current_file |
| `J` | js_select_last_file |
| `K` | js_select_first_file |
| `r` | js_rename_file |
| `e` | batch_rename |
| `<left>` | js_up_directory |
| `<down>` | js_select_next_file |
| `<up>` | js_select_prev_file |
| `<right>` | js_open_current_file |
| `f` | js_open_current_file |
| `C-m` | js_open_current_file |
| `F` | open_link |
| `T` | open_current_file_in_new_tab |
| `H` | open_file |
| `SPC` | js_scroll_up_select_file |
| `b` | js_scroll_down_select_file |
| `<return>` | js_open_current_file |
| `w` | js_copy_file_name |
| `W` | js_copy_file_path |
| `/` | copy_dir_path |
| `n` | new_file |
| `N` | new_directory |
| `R` | move_current_or_mark_file |
| `C` | copy_current_or_mark_file |
| `^` | js_up_directory |
| `'` | js_up_directory |
| `m` | js_mark_file |
| `u` | js_unmark_file |
| `t` | js_toggle_mark_file |
| `U` | js_unmark_all_files |
| `x` | delete_selected_files |
| `X` | delete_current_file |
| `o` | toggle_hidden_file |
| `O` | toggle_preview |
| `q` | bury-buffer |
| `Q` | close_buffer |
| `g` | refresh_dir |
| `G` | find_files |
| `*` | mark_file_by_extension |
| `v` | js_preview_toggle |
| `,` | js_preview_scroll_up_line |
| `.` | js_preview_scroll_down_line |
| `<` | js_preview_scroll_up |
| `>` | js_preview_scroll_down |
| `1` | sort_by_name |
| `2` | sort_by_size |
| `3` | sort_by_modified_time |
| `4` | sort_by_created_time |
| `5` | sort_by_access_time |
| `!` | eaf-file-manager-run-command-for-mark-files |
| `z` | eaf-file-manager-compress-file |
| `Z` | eaf-file-manager-uncompress-file |
| `B` | eaf-file-manager-byte-compile-file |
| `C-s` | search_file |

