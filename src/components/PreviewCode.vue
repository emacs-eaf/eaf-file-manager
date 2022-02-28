<template>
  <div ref="scrollArea" class="code-box">
    <pre class="code">{{content}}</pre>
  </div>
</template>

<script>
 export default {
   name: 'PreviewCode',
   components: {
   },
   props: {
     file: String,
     size: Number,
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
 .code-box {
   width: 100%;
   height: 100%;
   overflow: scroll;
   padding-left: 15px;
 }

 .code {
   margin: 0;
   font-size: 18px;
 }
</style>
