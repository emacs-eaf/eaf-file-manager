<template>
  <div class="too-big-file">
    <div class="too-big-info">
      Current file is too big, preview will slow down file manager.
    </div>
  </div>
</template>

<script>
 export default {
   name: 'PreviewTooBig',
   props: {
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
 .too-big-file {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
   justify-content: center;
 }

 .too-big-info {
   text-align: center;
 }
</style>
