<template>
  <div class="box">
    <div
      class="file"
      v-for="file in files"
      @click="openFile(file)"
      :key="file.path"
      :style="{ 'background': itemBackgroundColor(file), 'color': itemForegroundColor(file) }">
      <img class="file-icon" :src="fileIconPath(file.icon)"/>
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
   },
   watch: {
   },
   data() {
     return {
     }
   },
   mounted() {
   },
   created() {
   },
   methods: {
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .box {
   width: 100%;
   height: 100%;
   overflow: scroll;
   padding-top: 33px;
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
