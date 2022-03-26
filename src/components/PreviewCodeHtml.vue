<template>
  <div ref="scrollArea" class="code-box">
    <div v-html="content"/>
  </div>
</template>

<script>
 export default {
   name: 'PreviewCodeHtml',
   components: {
   },
   props: {
     file: String,
     size: Number,
     backgroundColor: String,
     content: String
   },
   watch: {
     file: function() {
       this.$refs.scrollArea.scrollTop = 0;
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
 .code-box {
   width: 100%;
   height: 100%;
   overflow: scroll;
   padding-left: 15px;
   font-size: 18px;
 }
</style>
