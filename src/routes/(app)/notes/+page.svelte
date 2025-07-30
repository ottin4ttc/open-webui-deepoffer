<script>
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	import Notes from '$lib/components/notes/Notes.svelte';
	
	onMount(() => {
		if ($user?.role !== 'admin') {
			goto('/');
		}
	});
</script>

{#if $user?.role === 'admin'}
	<Notes />
{/if}
