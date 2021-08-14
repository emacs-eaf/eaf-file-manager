<template>
  <div class="code-box">
    <pre class="code">{{ content }}</pre>
  </div>
</template>

<script>
 export default {
   name: 'PreviewCode',
   components: {
   },
   props: {
     content: String
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
 .code-box {
   width: 100%;
   height: 100%;
   overflow: scroll;
 }

 .code {
   padding-left: 20px;
   padding-right: 20px;
   margin: 0;
   font-size: 16px;
 }
</style>
