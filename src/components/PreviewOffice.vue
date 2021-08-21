<template>
  <div ref="scrollArea" class="office-box">
    <div v-html="wordText"/>
  </div>
</template>

<script>
 import mammoth from "mammoth";

 export default {
   name: 'PreviewOffice',
   components: {
   },
   props: {
     file: String
   },
   watch: {
     file: function() {
       this.getWordText();
     }
   },
   data() {
     return {
       wordText: ""
     }
   },
   mounted() {
     var that = this;

     this.$root.$on("previewToggle", function() {
       that.$refs.scrollArea.scrollTop = that.$refs.scrollArea.scrollTop + that.$refs.scrollArea.clientHeight;
     });
   },
   created() {
     this.getWordText();
   },
   methods: {
     getWordText() {
       const xhr = new XMLHttpRequest();
       xhr.open("get", this.file, true);
       xhr.responseType = "arraybuffer";
       xhr.onload = () => {
         if (xhr.status == 0) {
           mammoth.convertToHtml({ arrayBuffer: new Uint8Array(xhr.response) }).then((resultObject) => {
             this.$nextTick(() => {
               this.wordText = resultObject.value;
             });
           });
         }
       };
       xhr.send();
     }
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .office-box {
   width: 100%;
   height: 100%;
   overflow: scroll;
   padding: 15px;
 }

 img {
   max-width: 100%;
 }
</style>
