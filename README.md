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

### Dependency List

| Package        | Description          |
| :--------      | :------              |
| python-magic                   | Get the MIME type of the file                                      |

### The keybinding of EAF File Manager.

| Key   | Event   |
| :---- | :------ |
| `<f12>` | open_devtools |
| `h` | js_up_directory |
| `j` | js_select_next_file |
| `k` | js_select_prev_file |
| `l` | js_open_file |
| `f` | js_open_file |
| `'` | js_up_directory |
| `q` | bury-buffer |

