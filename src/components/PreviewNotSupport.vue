<template>
  <div class="not-support-file">
    <div class="not-support-file-info">
      Current file cannot be previewed yet.
    </div>
  </div>
</template>

<script>
 export default {
   name: 'PreviewNotSupport',
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
 .not-support-file {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
   justify-content: center;
 }

 .not-support-file-info {
   text-align: center;
 }
</style>
