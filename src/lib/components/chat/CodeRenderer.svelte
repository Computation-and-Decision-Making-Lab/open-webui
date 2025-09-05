<script lang="ts">
  import { onMount } from 'svelte';

  export let code: string;
  export let language: string;

  let iframe: HTMLIFrameElement;

  function renderCode() {
    if (language === 'html' || language === 'js' || language === 'css') {
      const doc = iframe.contentDocument;
      if (doc) {
        doc.open();
        doc.write(`
          <style>body { font-family: sans-serif; }</style>
          ${code}
        `);
        doc.close();
      }
    }
  }

  onMount(() => {
    renderCode();
  });

  $: if (code) {
    renderCode();
  }
</script>

<iframe
  bind:this={iframe}
  title="Code Preview"
  class="w-full h-full border-0 bg-white"
></iframe>