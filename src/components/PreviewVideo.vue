<template>
  <div class="video-box">
    <video
      class="video"
      ref="player"
      :key="dynamicKey"
      controls>
      <source :src="file">
    </video>
  </div>
</template>

<script>
 export default {
   name: 'PreviewVideo',
   props: {
     file: String
   },
   watch: {
     file: function() {
       this.dynamicKey = Math.random(10000);
     }
   },
   data() {
     return {
       dynamicKey: ""
     }
   },
   mounted() {
     var that = this;
     this.$root.$on("previewToggle", function() {
       if (that.$refs.player.paused) {
         that.$refs.player.play();
       } else {
         that.$refs.player.pause();
       }
     });
   },
   created() {
   },
   methods: {
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .video-box {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
   align-items: center;
   justify-content: center;
 }

 .video {
   max-width: 100%;
   max-height: 100%;
   border: none;
   outline: none;
 }
</style>
