<template>
  <div class="page">
    <div class="content">
      <div class="file-area">
        <div
          class="current-path"
          :style="{ 'color': headerForegroundColor() }">
          <span class="current-path-first-part">{{ pathFirstPart }}</span>
          <span class="current-path-second-part">{{ pathSecondPart }}</span>
        </div>
        <div
          v-if="searchRegex !== ''"
          class="search-keyword"
          :style="{ 'color': infoForegroundColor() }">
          search: {{ searchStr }} {{ files.length }} files matched "{{ searchRegex }}"
        </div>
        <div
          v-if="gitLog !== ''"
          class="git-log"
          :style="{ 'color': infoForegroundColor() }">
          git: {{ gitLog }}
        </div>

        <div
          ref="filelist"
          class="file-list">
          <div
            class="file"
            v-for="file in files"
            @click="selectFile(file)"
            :key="file.path"
            :style="{ 'background': itemBackgroundColor(file), 'color': itemForegroundColor(file) }">
            <img
              v-if="showIcon === 'true'"
              class="file-icon" :src="fileIconPath(file.icon)"/>
            <div class="eaf-file-manager-file-name">
              {{ file.name }}
            </div>
            <div class="file-size">
              {{ file.size }}
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="showPreview === 'true'"
        class="preview">
        <PreviewImage v-if="previewType == 'file' && previewMime == 'image'" :file="previewPath"/>
        <PreviewHtml v-if="previewType == 'file' && previewMime == 'html'" :file="previewPath"/>
        <PreviewCode
          v-if="previewType == 'file' && previewMime == 'text'"
          :file="previewPath"
          :size="previewSize"
          :backgroundColor="backgroundColor"/>
        <PreviewPdf v-if="previewType == 'file' && previewMime == 'pdf'" :file="previewPath"/>
        <PreviewVideo v-if="previewType == 'file' && previewMime == 'video'" :file="previewPath"/>
        <PreviewAudio v-if="previewType == 'file' && previewMime == 'audio'" :file="previewPath" :barColor="foregroundColor"/>
        <PreviewOffice v-if="previewType == 'file' && previewMime == 'office'" :file="previewPath"/>
        <PreviewDirectory
          v-if="previewType == 'directory' && previewFiles.length > 0"
          :files="previewFiles"
          :openFile="openFile"
          :itemBackgroundColor="itemBackgroundColor"
          :itemForegroundColor="itemForegroundColor"
          :fileIconPath="fileIconPath"
          :showIcon="showIcon"/>
        <PreviewEmpty v-if="previewType == 'directory' && previewFiles.length == 0"/>
        <PreviewSymlink v-if="previewType == 'symlink'"/>
      </div>

    </div>
  </div>
</template>

<script>
 import { QWebChannel } from "qwebchannel";
 import PreviewVideo from "./PreviewVideo.vue"
 import PreviewAudio from "./PreviewAudio.vue"
 import PreviewPdf from "./PreviewPdf.vue"
 import PreviewCode from "./PreviewCode.vue"
 import PreviewHtml from "./PreviewHtml.vue"
 import PreviewImage from "./PreviewImage.vue"
 import PreviewEmpty from "./PreviewEmpty.vue"
 import PreviewSymlink from "./PreviewSymlink.vue"
 import PreviewDirectory from "./PreviewDirectory.vue"
 import PreviewOffice from "./PreviewOffice.vue"

 export default {
   name: 'Main',
   components: {
     PreviewVideo,
     PreviewAudio,
     PreviewPdf,
     PreviewCode,
     PreviewHtml,
     PreviewImage,
     PreviewEmpty,
     PreviewSymlink,
     PreviewDirectory,
     PreviewOffice,
   },
   props: {
     msg: String
   },
   watch: {
     currentIndex: {
       // eslint-disable-next-line no-unused-vars
       handler: function(val, oldVal) {
         if (this.files.length > 0) {
           this.currentPath = this.files[val].path;
         }
         window.pyobject.vue_update_current_index(val);
       }
     },
     files: {
       // eslint-disable-next-line no-unused-vars
       handler: function (val, oldVal) {
         window.pyobject.vue_update_files(val);
       },
       deep: true
     },
     path: {
       // eslint-disable-next-line no-unused-vars
       handler: function(val, oldVal) {
         this.pathFirstPart = val.substring(0, val.length / 2);
         this.pathSecondPart = val.substring(val.length / 2, val.length);
       }
     }
   },
   data() {
     return {
       path: "",
       pathFirstPart: "",
       pathSecondPart: "",
       searchRegex: "",
       gitLog: "",
       searchStr: "finding",
       files: [],
       currentIndex: 0,
       currentPath: "",
       backgroundColor: "",
       foregroundColor: "",
       headerColor: "",
       markColor: "",
       fileColor: "",
       directoryColor: "",
       symlinkColor: "",
       selectColor: "",
       searchMatchColor: "",
       searchKeywordColor: "",

       previewPath: "",
       previewType: "",
       previewFiles: [],
       previewMime: "",
       previewSize: "",

       pathSep: "",
       iconCacheDir: "",

       showPreview: "false",
       showIcon: "false",

       themeMode: ""
     }
   },
   mounted() {
     window.changePath = this.changePath;
     window.updateGitLog = this.updateGitLog;
     window.initSearch = this.initSearch;
     window.appendSearch = this.appendSearch;
     window.finishSearch = this.finishSearch;
     window.init = this.init;
     window.selectNextFile = this.selectNextFile;
     window.selectPrevFile = this.selectPrevFile;
     window.selectFirstFile = this.selectFirstFile;
     window.selectLastFile = this.selectLastFile;
     window.scrollUpSelectFile = this.scrollUpSelectFile;
     window.scrollDownSelectFile = this.scrollDownSelectFile;
     window.openCurrentFile = this.openCurrentFile;
     window.upDirectory = this.upDirectory;
     window.setPreview = this.setPreview;
     window.setPreviewOption = this.setPreviewOption;
     window.markFile = this.markFile;
     window.markFileByExtension = this.markFileByExtension;
     window.markChangeFiles = this.markChangeFiles;
     window.unmarkFile = this.unmarkFile;
     window.unmarkAllFiles = this.unmarkAllFiles;
     window.toggleMarkFile = this.toggleMarkFile;
     window.getMarkFileNumber = this.getMarkFileNumber;
     window.removeMarkFiles = this.removeMarkFiles;
     window.removeSelectFile = this.removeSelectFile;
     window.renameFile = this.renameFile;
     window.renameFiles = this.renameFiles;
     window.rename = this.rename;
     window.copyFileName = this.copyFileName;
     window.copyFilePath = this.copyFilePath;
     window.addNewFile = this.addNewFile;
     window.addNewDirectory = this.addNewDirectory;
     window.openFileByName = this.openFileByName;
     window.openPreviewFileByName = this.openPreviewFileByName;
     window.previewScrollUp = this.previewScrollUp;
     window.previewScrollDown = this.previewScrollDown;
     window.previewScrollUpLine = this.previewScrollUpLine;
     window.previewScrollDownLine = this.previewScrollDownLine;
     window.previewToggle = this.previewToggle;
     window.selectFileByIndex = this.selectFileByIndex;
     window.setSearchMatchFiles = this.setSearchMatchFiles;
   },
   created() {
     // eslint-disable-next-line no-undef
     new QWebChannel(qt.webChannelTransport, channel => {
       window.pyobject = channel.objects.pyobject;
     });
   },
   methods: {
     changePath(path, files, index) {
       this.path = path;
       this.files = files;
       this.currentIndex = index;

       /* Need set currentPath here, watch track will miss update currentPath */
       if (this.files.length > 0) {
         this.currentPath = this.files[this.currentIndex].path;
       }

       /* Use nextTick wait DOM update, then make sure current file in visible area. */
       this.$nextTick(function(){
         this.keepSelectVisible();
       })

       this.searchRegex = "";
     },

     updateGitLog(log) {
       this.gitLog = log;
     },

     initSearch(path, searchRegex) {
       this.path = path;
       this.files = [];
       this.searchRegex = searchRegex;

       this.currentIndex = 0;
       this.currentPath = "";
       this.searchStr = "finding";
     },

     appendSearch(files) {
       this.files = this.files.concat(files);

       if (this.currentPath == "") {
         this.currentPath = this.files[this.currentIndex].path;
       }
     },

     finishSearch() {
       this.searchStr = "found";
     },

     init(backgroundColor, foregroundColor, headerColor, directoryColor, symlinkColor, markColor, selectColor, searchMatchColor,
          searchKeywordColor, iconCacheDir, pathSep, showPreview, showIcon, themeMode) {
       this.backgroundColor = backgroundColor;
       this.foregroundColor = foregroundColor;
       this.fileColor = foregroundColor;
       this.headerColor = headerColor;
       this.directoryColor = directoryColor;
       this.symlinkColor = symlinkColor;
       this.markColor = markColor;
       this.selectColor = selectColor;
       this.searchMatchColor = searchMatchColor;
       this.searchKeywordColor = searchKeywordColor;
       this.iconCacheDir = iconCacheDir;
       this.pathSep = pathSep;
       this.showPreview = showPreview;
       this.showIcon = showIcon;
       this.themeMode = themeMode;
     },

     itemBackgroundColor(item) {
       if (item.path == this.currentPath) {
         return this.selectColor;
       } else {
         return this.backgroundColor;
       }
     },

     itemForegroundColor(item) {
       if (item.match == "match") {
         return this.searchMatchColor;
       } else if (item.mark == "mark") {
         return this.markColor;
       } else {
         if (item.type == "directory") {
           return this.directoryColor;
         } else if (item.type == "file") {
           return this.fileColor;
         } else if (item.type == "symlink") {
           return this.symlinkColor;
         }
       }
     },

     headerForegroundColor() {
       return this.headerColor;
     },

     infoForegroundColor() {
       return this.searchKeywordColor;
     },

     setSearchMatchFiles(fileIndexes) {
       this.files.map(file => { file.match = "" });

       fileIndexes.map(fileIndex => {this.files[fileIndex].match = "match"});
     },

     selectFileByIndex(index) {
       if (index >= this.files.length) {
         this.currentIndex = this.files.length - 1;
       } else if (index <= 0) {
         this.currentIndex = 0;
       } else {
         this.currentIndex = index;
       }

       this.keepSelectVisible();

       this.updatePreview();
     },

     selectNextFile() {
       this.selectFileByIndex(this.currentIndex + 1);
     },

     selectPrevFile() {
       this.selectFileByIndex(this.currentIndex - 1);
     },

     selectFirstFile() {
       this.selectFileByIndex(0);
     },

     selectLastFile() {
       this.selectFileByIndex(this.files.length - 1);
     },

     scrollUpSelectFile() {
       this.selectFileByIndex(this.currentIndex + this.getSceenElementNumber());
     },

     scrollDownSelectFile() {
       this.selectFileByIndex(this.currentIndex - this.getSceenElementNumber());
     },

     markFile() {
       this.files[this.currentIndex].mark = "mark";
       this.selectNextFile();
     },

     markFileByExtension(extension) {
       for (var i=0; i < this.files.length; i++) {
         var fileExtension = this.files[i]["path"].split('.').pop();

         if (fileExtension == extension) {
           this.files[i].mark = "mark";
         }
       }
     },

     markChangeFiles(indexes) {
       indexes.forEach(index => {this.files[index].mark = "mark"});
     },

     unmarkFile() {
       this.files[this.currentIndex].mark = "";
       this.selectNextFile();
     },

     unmarkAllFiles() {
       this.files.forEach(file => {file.mark = ""});
     },

     toggleMarkFile() {
       this.files.map(file => {
         if (file.mark == "mark") {
           file.mark = ""
         } else {
           file.mark = "mark"
         }
       })
     },

     getMarkFileNumber() {
       return this.files.filter(file => { return file.mark == "mark" }).length;
     },

     removeMarkFiles() {
       this.files = this.files.filter(file => { return file.mark != "mark" });
     },

     removeSelectFile() {
       this.files = this.files.filter(file => { return file.path != this.currentPath });
     },

     getSceenElementNumber() {
       return Math.floor(window.innerHeight / this.$refs.filelist.children[this.currentIndex].clientHeight);
     },

     selectFile(file) {
       if (file !== undefined) {
         this.currentIndex = this.files.map(file => file.path).indexOf(file.path);

         this.updatePreview();
       }
     },

     keepSelectVisible() {
       var select_file = this.$refs.filelist.children[this.currentIndex]
       if (select_file !== undefined) {
         select_file.scrollIntoViewIfNeeded(false);
       }
     },

     openCurrentFile() {
       this.openFile(this.files[this.currentIndex]);
     },

     upDirectory() {
       window.pyobject.change_up_directory(this.currentPath);
     },

     updatePreview() {
       window.pyobject.update_preview(this.files[this.currentIndex].path);
     },

     renameFile() {
       window.pyobject.rename_file(this.files[this.currentIndex].path);
     },

     renameFiles(new_files) {
       this.files = new_files;
     },

     rename(old_file_path, new_file_path, new_file_name) {
       for (var i=0; i < this.files.length; i++) {
         if (this.files[i]["path"] == old_file_path) {
           this.files[i]["path"] = new_file_path;
           this.files[i]["name"] = new_file_name;
           break
         }
       }
     },

     fileIconPath(iconFile) {
       return this.iconCacheDir + this.pathSep + iconFile;
     },

     copyFileName() {
       var currentFile = this.files[this.currentIndex];
       window.pyobject.eval_emacs_function("kill-new", [currentFile.name])
       window.pyobject.eval_emacs_function("message", ["Copy '" + currentFile.name + "'"])
     },

     copyFilePath() {
       var currentFile = this.files[this.currentIndex];
       window.pyobject.eval_emacs_function("kill-new", [currentFile.path])
       window.pyobject.eval_emacs_function("message", ["Copy '" + currentFile.path + "'"])
     },

     addNewFile(new_file) {
       this.currentIndex = this.files.push(new_file) - 1;
       this.currentPath = new_file.path;
     },

     addNewDirectory(new_directory) {
       var insert_index = this.files.filter(file => { return file.type == "directory" }).length;
       this.files.splice(insert_index, 0, new_directory);
       this.currentIndex = insert_index;

       this.selectFileByIndex(insert_index);
     },

     openFileByName(fileName) {
       for (var i=0; i< this.files.length; i++) {
         if (this.files[i]["name"] == fileName) {
           this.openFile(this.files[i]);

           break;
         }
       }
     },

     openPreviewFileByName(fileName) {
       for (var i=0; i< this.previewFiles.length; i++) {
         if (this.previewFiles[i]["name"] == fileName) {
           this.openFile(this.previewFiles[i]);

           break;
         }
       }
     },

     openFile(file) {
       if (file.type == "directory") {
         window.pyobject.change_directory(file.path, "");
       } else if (file.type == "file") {
         window.pyobject.eval_emacs_function("find-file", [file.path])
       }
     },

     previewScrollUp() {
       this.$root.$emit("scrollUp");
     },

     previewScrollDown() {
       this.$root.$emit("scrollDown");
     },

     previewScrollUpLine() {
       this.$root.$emit("scrollUpLine");
     },

     previewScrollDownLine() {
       this.$root.$emit("scrollDownLine");
     },

     previewToggle() {
       this.$root.$emit("previewToggle");
     },

     setPreviewOption(option) {
       this.showPreview = option;
     },

     setPreview(filePath, fileType, fileInfos) {
       this.previewPath = filePath;
       this.previewType = fileType;
       this.previewFiles = fileInfos;

       if (fileType == "file") {
         var mime = fileInfos[0]["mime"]
         console.log("***** ", filePath, mime)

         if (mime.startsWith("image-")) {
           this.previewMime = "image"
         } else if (mime == "text-html") {
           this.previewMime = "html"
         } else if (mime.startsWith("text-") || mime == "application-json") {
           this.previewMime = "text"
         } else if (mime == "application-pdf") {
           this.previewMime = "pdf"
         } else if (mime.startsWith("video-")) {
           this.previewMime = "video"
         } else if (mime.startsWith("audio-")) {
           this.previewMime = "audio"
         } else if (mime == "application-wps-office.docx") {
           this.previewMime = "office"
         }

         this.previewSize = fileInfos[0]["size"]
       }
     }
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .page {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
 }

 .file-area {
   flex: 1 1 0px;
   height: 100%;
   display: flex;
   flex-direction: column;

   overflow: hidden;/* It's import for long git log  */
 }

 .search-keyword {
   padding-left: 20px;
   padding-bottom: 5px;
   font-weight: bold;
 }

 .git-log {
   padding-left: 20px;
   padding-right: 20px;
   padding-bottom: 5px;
   font-weight: bold;

   overflow: hidden;
   white-space: nowrap;
   text-overflow: ellipsis;
 }

 .current-path {
   font-size: 16px;
   padding-left: 20px;
   padding-right: 20px;
   padding-top: 5px;
   padding-bottom: 5px;

   display: flex;
   min-width: 0;
 }

 .current-path-first-part {
   text-overflow: ellipsis;
   white-space: nowrap;
   overflow: hidden;
 }

 .current-path-second-part {
   flex-shrink: 0;
 }

 .file-list {
   width: 100%;
   height: 100%;
   overflow: scroll;
 }

 .file {
   font-size: 16px;
   padding-left: 20px;
   padding-top: 2px;
   padding-bottom: 2px;

   display: flex;
   flex-direction: row;
   align-items: center;
 }

 .file-icon {
   width: 24px;
   margin-right: 5px;
 }

 .eaf-file-manager-file-name {
   flex: 1;
   padding-right: 20px;
   word-break: break-word;
 }

 .file-size {
   padding-right: 20px;
   display: flex;
   flex-direction: column;
   justify-content: center;
 }

 .preview {
   flex: 1 1 0px;
   height: 100%;
   overflow: hidden;

   border-left: 1px solid;
 }

 .content {
   width: 100%;
   height: 100%;
   overflow: hidden;

   display: flex;
   flex-direction: row;
 }
</style>
