<template>
  <div class="page">
    <div class="content">
      <div class="file-area">
        <div
          class="current-path"
          :style="{ 'color': headerForegroundColor() }">
          {{ path }}
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
            <div class="file-name">
              {{ file.name }}
            </div>
            <div class="file-size">
              {{ file.size }}
            </div>
          </div>
        </div>
      </div>

      <div class="preview">
        <PreviewImage v-if="previewType == 'file' && previewMime == 'image'" :file="previewPath"/>
        <PreviewCode v-if="previewType == 'file' && previewMime == 'text'" :content="previewContent" :backgroundColor="backgroundColor"/>
        <PreviewPdf v-if="previewType == 'file' && previewMime == 'pdf'" :file="previewPath"/>
        <PreviewVideo v-if="previewType == 'file' && previewMime == 'video'" :file="previewPath"/>
        <PreviewAudio v-if="previewType == 'file' && previewMime == 'audio'" :file="previewPath" :barColor="foregroundColor"/>
        <PreviewDirectory
          v-if="previewType == 'directory' && previewFiles.length > 0"
          :files="previewFiles" :itemBackgroundColor="itemBackgroundColor" :itemForegroundColor="itemForegroundColor"/>
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
 import PreviewImage from "./PreviewImage.vue"
 import PreviewEmpty from "./PreviewEmpty.vue"
 import PreviewSymlink from "./PreviewSymlink.vue"
 import PreviewDirectory from "./PreviewDirectory.vue"

 export default {
   name: 'Main',
   components: {
     PreviewVideo,
     PreviewAudio,
     PreviewPdf,
     PreviewCode,
     PreviewImage,
     PreviewEmpty,
     PreviewSymlink,
     PreviewDirectory,
   },
   props: {
     msg: String
   },
   data() {
     return {
       path: "",
       files: [],
       fileNumber: 0,
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

       previewPath: "",
       previewType: "",
       previewFiles: [],
       previewMime: "",
       previewContent: "",
     }
   },
   mounted() {
     window.changePath = this.changePath;
     window.initColors = this.initColors;
     window.selectNextFile = this.selectNextFile;
     window.selectPrevFile = this.selectPrevFile;
     window.selectFirstFile = this.selectFirstFile;
     window.selectLastFile = this.selectLastFile;
     window.scrollUpSelectFile = this.scrollUpSelectFile;
     window.scrollDownSelectFile = this.scrollDownSelectFile;
     window.openFile = this.openFile;
     window.upDirectory = this.upDirectory;
     window.setPreview = this.setPreview;
     window.markFile = this.markFile;
     window.unmarkFile = this.unmarkFile;
     window.unmarkAllFiles = this.unmarkAllFiles;
     window.getMarkFileNumber = this.getMarkFileNumber;
     window.getMarkFiles = this.getMarkFiles;
     window.removeMarkFiles = this.removeMarkFiles;
     window.getSelectFile = this.getSelectFile;
     window.removeSelectFile = this.removeSelectFile;
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
       this.fileNumber = files.length;
       this.currentIndex = index;
       this.currentPath = files[this.currentIndex].path;
     },

     initColors(backgroundColor, foregroundColor, headerColor, directoryColor, symlinkColor, markColor, selectColor) {
       this.backgroundColor = backgroundColor;
       this.foregroundColor = foregroundColor;
       this.fileColor = foregroundColor;
       this.headerColor = headerColor;
       this.directoryColor = directoryColor;
       this.symlinkColor = symlinkColor;
       this.markColor = markColor;
       this.selectColor = selectColor;
     },

     itemBackgroundColor(item) {
       if (item.path == this.currentPath) {
         return this.selectColor;
       } else {
         return this.backgroundColor;
       }
     },

     itemForegroundColor(item) {
       if (item.mark == "mark") {
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

     selectFileByIndex(index) {
       if (index >= this.fileNumber) {
         this.currentIndex = this.fileNumber - 1;
       } else if (index <= 0) {
         this.currentIndex = 0;
       } else {
         this.currentIndex = index;
       }

       this.currentPath = this.files[this.currentIndex].path;

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
       this.selectFileByIndex(this.fileNumber - 1);
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

     unmarkFile() {
       this.files[this.currentIndex].mark = "";
       this.selectNextFile();
     },

     unmarkAllFiles() {
       this.files.forEach(file => {file.mark = ""});
     },

     getMarkFileNumber() {
       return this.files.filter(file => { return file.mark == "mark" }).length;
     },

     getMarkFiles() {
       return this.files.filter(file => { return file.mark == "mark" });
     },

     removeMarkFiles() {
       var markNumber = this.getMarkFileNumber();

       this.files = this.files.filter(file => { return file.mark != "mark" });
       this.fileNumber = this.files.length;

       this.currentIndex -= markNumber;

       if (this.currentIndex > this.fileNumber - 1) {
         this.currentIndex = this.fileNumber - 1;
       } else if (this.currentIndex < 0) {
         this.currentIndex = 0;
       }

       this.currentPath = this.files[this.currentIndex].path;

       this.selectFile(this.files[this.currentIndex]);
     },

     getSelectFile() {
       return this.files[this.currentIndex];
     },

     removeSelectFile() {
       this.files = this.files.filter(file => { return file.path != this.currentPath });
       this.fileNumber = this.files.length;

       if (this.currentIndex > this.fileNumber - 1) {
         this.currentIndex = this.fileNumber - 1;
       } else if (this.currentIndex < 0) {
         this.currentIndex = 0;
       }

       this.currentPath = this.files[this.currentIndex].path;

       this.selectFile(this.files[this.currentIndex]);
     },

     getSceenElementNumber() {
       return Math.floor(window.innerHeight / this.$refs.filelist.children[this.currentIndex].clientHeight);
     },

     selectFile(file) {
       this.currentPath = file.path;
       this.currentIndex = this.files.map(file => file.path).indexOf(file.path);

       this.updatePreview();
     },

     keepSelectVisible() {
       this.$refs.filelist.children[this.currentIndex].scrollIntoViewIfNeeded(false);
     },

     openFile() {
       var currentFile = this.files[this.currentIndex];

       if (currentFile.type == "directory") {
         window.pyobject.change_directory(currentFile.path, "");
       } else if (currentFile.type == "file") {
         window.pyobject.eval_emacs_function("find-file", [currentFile.path])
       }
     },

     upDirectory() {
       window.pyobject.change_up_directory(this.currentPath);
     },

     updatePreview() {
       window.pyobject.update_preview(this.files[this.currentIndex].path);
     },

     setPreview(filePath, fileType, fileInfos) {
       this.previewPath = filePath;
       this.previewType = fileType;
       this.previewFiles = fileInfos;

       if (fileType == "file") {
         var mime = fileInfos[0]["mime"]
         console.log("***** ", filePath, mime)

         if (mime.startsWith("image/")) {
           this.previewMime = "image"
         } else if (mime.startsWith("text/")) {
           this.previewMime = "text"
           this.previewContent = fileInfos[0]["content"]
         } else if (mime == "application/pdf") {
           this.previewMime = "pdf"
         } else if (mime.startsWith("video/")) {
           this.previewMime = "video"
         } else if (mime.startsWith("audio/")) {
           this.previewMime = "audio"
         }
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
   width: 50%;
   height: 100%;
   display: flex;
   flex-direction: column;
 }

 .current-path {
   font-size: 16px;
   padding-left: 20px;
   padding-top: 5px;
   padding-bottom: 5px;
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
 }

 .file-name {
   flex: 1;
   padding-right: 20px;
 }

 .file-size {
   padding-right: 20px;
   display: flex;
   flex-direction: column;
   justify-content: center;
 }

 .preview {
   width: 50%;
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
