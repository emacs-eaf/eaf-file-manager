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
   background-color: #FFFFFF;
   overflow: scroll;
 }
</style>
