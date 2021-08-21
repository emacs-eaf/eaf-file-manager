<template>
  <div
    ref="box"
    class="visual">
    <av-circle
      ref-link="player"
      playtime-font="30px monospace"
      :key="dynamicKey"
      :canv-width="visualCanvasWidth"
      :canv-height="visualCanvasWidth"
      :bar-color="barColor"
      :progress-color="barColor"
      :playtime-color="barColor"
      :outline-width="0"
      :progress-width="5"
      :outline-meter-space="5"
      :playtime="true"
    ></av-circle>
    <audio
      ref="player"
      class="audio"
      :key="dynamicKey"
      controls>
      <source :src="file">
    </audio>
  </div>
</template>

<script>
 export default {
   name: 'PreviewAudio',
   props: {
     file: String,
     barColor: String,
   },
   watch: {
     file: function() {
       this.dynamicKey = Math.random(10000);
     }
   },
   data() {
     return {
       dynamicKey: "",
       visualCanvasWidth: 0,
     }
   },
   mounted() {
     var that = this;

     this.$refs.player.pause();

     this.$root.$on("previewToggle", function() {
       if (that.$refs.player.paused) {
         that.$refs.player.play();
       } else {
         that.$refs.player.pause();
       }
     });
   },
   created() {
     this.visualCanvasWidth = window.innerWidth / 3;
   },
   methods: {
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .visual {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
   align-items: center;
   justify-content: center;
 }

 .audio {
   width: 100%;
   border: none;
   outline: none;
   display: none;
 }

 .notify-info-wrap {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
   justify-content: center;
 }

 .notify-info {
   text-align: center;
 }
</style>
