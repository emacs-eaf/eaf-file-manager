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

```Elisp
(add-to-list 'load-path "~/.emacs.d/site-lisp/eaf-file-manager/")
(require 'eaf-file-manager)
```

### The keybinding of EAF File Manager.

| Key   | Event   |
| :---- | :------ |
| `<f12>` | open_devtools |
| `h` | js_up_directory |
| `j` | js_select_next_file |
| `k` | js_select_prev_file |
| `l` | js_open_file |
| `J` | js_select_last_file |
| `K` | js_select_first_file |
| `r` | js_rename_file |
| `R` | batch_rename |
| `<left>` | js_up_directory |
| `<down>` | js_select_next_file |
| `<up>` | js_select_prev_file |
| `<right>` | js_open_file |
| `f` | open_link |
| `SPC` | js_scroll_up_select_file |
| `b` | js_scroll_down_select_file |
| `<return>` | js_open_file |
| `w` | js_copy_file_name |
| `W` | js_copy_file_path |
| `/` | copy_dir_path |
| `n` | new_file |
| `N` | new_directory |
| `x` | move_current_or_mark_file |
| `c` | copy_current_or_mark_file |
| `'` | js_up_directory |
| `m` | js_mark_file |
| `u` | js_unmark_file |
| `t` | js_toggle_mark_file |
| `U` | js_unmark_all_files |
| `d` | delete_selected_files |
| `D` | delete_current_file |
| `o` | toggle_hidden_file |
| `q` | bury-buffer |
| `g` | refresh_dir |
| `G` | find_files |

