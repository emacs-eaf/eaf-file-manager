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

     this.$root.$on("previewToggle", function() {
       that.$refs.scrollArea.scrollTop = that.$refs.scrollArea.scrollTop + that.$refs.scrollArea.clientHeight;
     });
   },
   created() {
   },
   methods: {
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
