<template>
  <div ref="scrollArea" class="box">
    <div v-html="content"/>
  </div>
</template>

<script>
 export default {
   name: 'PreviewHtml',
   props: {
     file: String,
   },
   watch: {
     file: function() {
       this.readFileContent();
     }
   },
   data() {
     return {
       content: ""
     }
   },
   mounted() {
     var that = this;

     this.$root.$on("previewToggle", function() {
       that.$refs.scrollArea.scrollTop = that.$refs.scrollArea.scrollTop + that.$refs.scrollArea.clientHeight;
     });
   },
   created() {
     this.readFileContent();
   },
   methods: {
     readFileContent() {
       const xhr = new XMLHttpRequest();
       xhr.open("get", this.file, true);
       xhr.responseType = "arraybuffer";
       xhr.onload = () => {
         if (xhr.status == 0) {
           var enc = new TextDecoder();
           this.content = enc.decode(xhr.response)
           print(this.content)
         }
       };
       xhr.send();
     }
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .box {
   width: 100%;
   height: 100%;
   background-color: #FFFFFF;
   overflow: scroll;
 }
</style>
