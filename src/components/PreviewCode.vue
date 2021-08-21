<template>
  <div ref="scrollArea" class="code-box">
    <pre class="code" v-highlightjs="content">
      <code :style="{ 'background': backgroundColor }">
      </code>
    </pre>
  </div>
</template>

<script>
 export default {
   name: 'PreviewCode',
   components: {
   },
   props: {
     file: String,
     backgroundColor: String
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
         }
       };
       xhr.send();
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
   font-size: 16px;
 }
</style>
