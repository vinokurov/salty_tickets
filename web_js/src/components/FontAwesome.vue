<template>
	<i :class="classStr" aria-hidden="true"></i>
</template>

<script>
export default {
  name: 'FontAwesome',
  props: {
  	    icon: String
  	},
  	computed: {
	    classStr: function () { return 'fa fa-fw fa-' + this.icon }
  }
}
</script>
