<script>
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	import Chat from '$lib/components/playground/Chat.svelte';
	
	onMount(() => {
		if ($user?.role !== 'admin') {
			goto('/');
		}
	});
</script>

{#if $user?.role === 'admin'}
	<Chat />
{/if}
