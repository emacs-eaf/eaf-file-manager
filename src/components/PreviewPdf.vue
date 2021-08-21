<template>
  <div ref="scrollArea" class="pdf-box">
    <pdf
      :src="file"
      :key="dynamicKey"/>
  </div>
</template>

<script>
 import pdf from 'pdfvuer'

 export default {
   name: 'PreviewPdf',
   components: {
     pdf,
   },
   props: {
     file: String
   },
   watch: {
     file: function() {
       this.dynamicKey = Math.random(10000);
     }
   },
   data() {
     return {
       dynamicKey: ""
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
 .pdf-box {
   width: 100%;
   height: 100%;
   overflow: scroll;
 }
</style>
