<template>
  <div class="code-box">
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
     content: String,
     backgroundColor: String
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
   margin: 0;
   font-size: 16px;
 }
</style>
