<template>
  <div
    ref="scrollArea" 
    class="office-box">
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

     this.$refs.scrollArea.scrollTop = 0;
     
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
 .office-box {
   height: 100%;
   overflow: scroll;
   padding: 15px;
 }

 img {
   max-width: 100%;
 }
</style>
