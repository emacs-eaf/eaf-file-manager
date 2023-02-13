<template>
  <div ref="scrollArea" class="box">
    <div
      class="file"
      v-for="file in files"
      @click="openFile(file)"
      :key="file.path"
      :style="{ 'background': itemBackgroundColor(file), 'color': itemForegroundColor(file) }">
      <img
        v-if="showIcon === 'true'"
        class="file-icon" :src="fileIconPath(file.icon)"/>
      <div class="eaf-file-manager-preview-file-name">
        {{ file.name }}
      </div>
      <div class="file-size">
        {{ file.size }}
      </div>
    </div>
  </div>
</template>

<script>
 import JSZip from "jszip"

 export default {
   name: 'PreviewZip',
   components: {
   },
   props: {
     file: String,
     size: Number,
     openFile: Function,
     itemBackgroundColor: Function,
     itemForegroundColor: Function,
     fileIconPath: Function,
     showIcon: String,
     backgroundColor: String
   },
   watch: {
     file: function() {
       this.readFileContent();
       this.$refs.scrollArea.scrollTop = 0;
     }
   },
   data() {
     return {
       files: []
     }
   },
   mounted() {
     var that = this;

     this.$root.$on("previewToggle", function() {
       that.scrollUp();
     });

     this.$root.$on("scrollUp", function() {
       that.scrollUp();
     });

     this.$root.$on("scrollDown", function() {
       that.scrollDown();
     });

     this.$root.$on("scrollUpLine", function() {
       that.scrollUpLine();
     });

     this.$root.$on("scrollDownLine", function() {
       that.scrollDownLine();
     });
   },
   created() {
     this.readFileContent();
   },
   methods: {
     readFileContent() {
       var that = this;

       const xhr = new XMLHttpRequest();
       xhr.open("get", this.file, true);
       xhr.responseType = "arraybuffer";
       xhr.onload = () => {
         if (xhr.status == 0) {
           var zipReader = new JSZip();

           zipReader.loadAsync(xhr.response).then(function(zip) {
             zip.forEach(function(_, zipEntry) {
               var fileType = "";
               var fileIcon = "";
               if (zipEntry.dir) {
                 fileType = "directory"
                 fileIcon = "directory.png"
               } else {
                 fileType = "file"
                 fileIcon = "application-zip.png"
               }

               that.files.push({
                 "name": zipEntry.name,
                 "type": fileType,
                 "icon": fileIcon
               })
             });
           });
         }
       };
       xhr.send();
     },

     scrollUp() {
       this.$refs.scrollArea.scrollTop = this.$refs.scrollArea.scrollTop + this.$refs.scrollArea.clientHeight;
     },

     scrollDown() {
       this.$refs.scrollArea.scrollTop = this.$refs.scrollArea.scrollTop - this.$refs.scrollArea.clientHeight;
     },

     scrollUpLine() {
       this.$refs.scrollArea.scrollTop = this.$refs.scrollArea.scrollTop + 50;
     },

     scrollDownLine() {
       this.$refs.scrollArea.scrollTop = this.$refs.scrollArea.scrollTop - 50;
     }
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .box {
   width: 100%;
   height: 100%;
   overflow: scroll;
   padding-top: 5px;
 }

 .file {
   font-size: 18px;
   padding-left: 20px;
   padding-top: 4px;
   padding-bottom: 4px;

   display: flex;
   flex-direction: row;
   align-items: center;
 }

 .file:last-child {
   margin-bottom: 10px;
 }

 .file-icon {
   width: 24px;
   margin-right: 5px;
 }

 .eaf-file-manager-preview-file-name {
   flex: 1;
   padding-right: 20px;
 }

 .file-size {
   padding-right: 20px;
   display: flex;
   flex-direction: column;
   justify-content: center;
 }
</style>
