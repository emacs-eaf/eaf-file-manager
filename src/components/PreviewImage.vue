<template>
  <div class="image-box">
    <img
      class="image"
      :src="file"/>
  </div>
</template>

<script>
 export default {
   name: 'PreviewImage',
   components: {
   },
   props: {
     file: String
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
 .image-box {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
   align-items: center;
   justify-content: center;
 }

 .image {
   width: 100%;
 }
</style>
