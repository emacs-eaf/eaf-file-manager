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
 export default {
   name: 'PreviewDirectory',
   props: {
     files: Array,
     openFile: Function,
     itemBackgroundColor: Function,
     itemForegroundColor: Function,
     fileIconPath: Function,
     showIcon: String
   },
   watch: {
   },
   data() {
     return {
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
   },
   methods: {
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
   font-size: 20px;
   padding-left: 20px;
   padding-top: 4px;
   padding-bottom: 4px;

   display: flex;
   flex-direction: row;
   align-items: center;
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
