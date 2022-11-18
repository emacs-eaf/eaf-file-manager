<template>
  <div class="box">
    <img
      class="image"
      :src="file"/>
    <div class="exif-box">
      <div
        v-if="hasMaker"
        class="exif">
        <div class="title">
          {{ exif["make"] }}:
        </div>
        <div class="value">
          {{ exif["model"] }}
        </div>
      </div>
      <div
        v-if="hasResolution"
        class="exif">
        <div class="title">
          Resolution:
        </div>
        <div class="value">
          {{ exif["pixel_x_dimension"] }} x {{ exif["pixel_y_dimension"] }}
        </div>
      </div>
      <div
        v-if="hasDatetime"
        class="exif">
        <div class="title">
          Datetime:
        </div>
        <div class="value">
          {{ exif["datetime_original"] }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
 export default {
   name: 'PreviewImage',
   components: {
   },
   props: {
     file: String,
     exif: Object
   },
   computed: {
     hasMaker() {
       return this.containsKey(this.exif, 'make');
     },
     hasResolution() {
       return this.containsKey(this.exif, 'pixel_x_dimension') && this.containsKey(this.exif, 'pixel_y_dimension');
     },
     hasDatetime() {
       return this.containsKey(this.exif, 'datetime_original');
     }
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
     containsKey(obj, key ) {
       return Object.keys(obj).includes(key);
     }
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .box {
   width: 100%;
   height: 100%;
   display: flex;
   flex-direction: column;
   align-items: center;
   justify-content: center;
 }

 .image {
   max-width: 95%;
   max-height: 80%;
   padding-bottom: 20px;
 }

 .exif-box {
   display: flex;
   flex-direction: column;
   width: 60%;
 }

 .exif {
   display: flex;
   justify-content: space-between;
   padding-top: 2px;
   padding-bottom: 2px;
 }

 .title {
 }
</style>
