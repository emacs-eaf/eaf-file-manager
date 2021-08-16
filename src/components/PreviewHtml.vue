<template>
  <div>
    <iframe
      :src="file"
      style="background: #FFFFFF"
      ref="iframeContent"
      allowtransparency="true"
      frameborder="0"
      width="100%"
      height="100%">
    </iframe>
  </div>
</template>

<script>
 export default {
   name: 'PreviewHtml',
   props: {
     file: String,
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
</style>
