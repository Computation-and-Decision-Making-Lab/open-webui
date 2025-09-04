<script>
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	
	import { user } from '$lib/stores';
	import { getGroups, createNewGroup, getGroupById, updateGroupById, deleteGroupById } from '$lib/apis/groups';
	import { getAllUsers } from '$lib/apis/users';
	
	const i18n = getContext('i18n');
	
	let groups = [];
	let users = [];
	let loading = true;
	let showCreateModal = false;
	let showEditModal = false;
	let selectedGroup = null;
	
	// Form data
	let groupName = '';
	let groupDescription = '';
	let selectedUserIds = [];
	
	const loadGroups = async () => {
		try {
			const token = localStorage.token;
			groups = await getGroups(token);
		} catch (error) {
			console.error('Failed to load groups:', error);
			toast.error($i18n.t('Failed to load groups'));
		}
	};
	
	const loadUsers = async () => {
		try {
			const token = localStorage.token;
			const response = await getAllUsers(token);
			users = response.users || response;
		} catch (error) {
			console.error('Failed to load users:', error);
			toast.error($i18n.t('Failed to load users'));
		}
	};
	
	const handleCreateGroup = async () => {
		try {
			const token = localStorage.token;
			const groupData = {
				name: groupName,
				description: groupDescription,
				user_ids: selectedUserIds
			};
			
			await createNewGroup(token, groupData);
			toast.success($i18n.t('Group created successfully'));
			
			// Reset form
			groupName = '';
			groupDescription = '';
			selectedUserIds = [];
			showCreateModal = false;
			
			// Reload groups
			await loadGroups();
		} catch (error) {
			console.error('Failed to create group:', error);
			toast.error($i18n.t('Failed to create group'));
		}
	};
	
	const handleEditGroup = async (group) => {
		selectedGroup = group;
		groupName = group.name;
		groupDescription = group.description;
		selectedUserIds = group.user_ids || [];
		showEditModal = true;
	};
	
	const handleUpdateGroup = async () => {
		try {
			const token = localStorage.token;
			const groupData = {
				name: groupName,
				description: groupDescription,
				user_ids: selectedUserIds
			};
			
			await updateGroupById(token, selectedGroup.id, groupData);
			toast.success($i18n.t('Group updated successfully'));
			
			// Reset form
			groupName = '';
			groupDescription = '';
			selectedUserIds = [];
			selectedGroup = null;
			showEditModal = false;
			
			// Reload groups
			await loadGroups();
		} catch (error) {
			console.error('Failed to update group:', error);
			toast.error($i18n.t('Failed to update group'));
		}
	};
	
	const handleDeleteGroup = async (groupId) => {
		if (confirm($i18n.t('Are you sure you want to delete this group?'))) {
			try {
				const token = localStorage.token;
				await deleteGroupById(token, groupId);
				toast.success($i18n.t('Group deleted successfully'));
				await loadGroups();
			} catch (error) {
				console.error('Failed to delete group:', error);
				toast.error($i18n.t('Failed to delete group'));
			}
		}
  };

  const handleGoBack = () => {
    goto('/');
  };
	
	const toggleUserSelection = (userId) => {
		if (selectedUserIds.includes(userId)) {
			selectedUserIds = selectedUserIds.filter(id => id !== userId);
		} else {
			selectedUserIds = [...selectedUserIds, userId];
		}
	};
	
	const getUserName = (userId) => {
		const user = users.find(u => u.id === userId);
		return user ? user.name : userId;
	};
	
	onMount(async () => {
		if (!$user) {
			goto('/auth');
			return;
		}
		
		loading = true;
		await Promise.all([loadGroups(), loadUsers()]);
		loading = false;
	});
</script>

<svelte:head>
	<title>Groups - Open WebUI</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<div class="flex justify-between items-center">
        <div class="flex items-center">
          <button
            on:click={handleGoBack}
            class="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Back
          </button>
        </div>
        <div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						{$i18n.t('Groups')}
					</h1>
					<p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
						{$i18n.t('Manage user groups and permissions')}
					</p>
				</div>
				
				{#if $user.role === 'admin'}
					<button
						on:click={() => showCreateModal = true}
						class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
					>
						{$i18n.t('Create Group')}
					</button>
				{/if}
			</div>
		</div>
		
		{#if loading}
			<div class="flex justify-center items-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>
		{:else}
			<!-- Groups List -->
			<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
				{#each groups as group (group.id)}
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
						<div class="flex justify-between items-start mb-4">
							<div>
								<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
									{group.name}
								</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
									{group.description || $i18n.t('No description')}
								</p>
							</div>
							
							{#if $user.role === 'admin' || group.user_id === $user.id}
								<div class="flex space-x-2">
									<button
										on:click={() => handleEditGroup(group)}
										class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
										title={$i18n.t('Edit')}
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
										</svg>
									</button>
									<button
										on:click={() => handleDeleteGroup(group.id)}
										class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
										title={$i18n.t('Delete')}
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
									</button>
								</div>
							{/if}
						</div>
						
						<!-- Members -->
						<div class="mt-4">
							<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								{$i18n.t('Members')} ({(group.user_ids || []).length})
							</p>
							<div class="flex flex-wrap gap-1">
								{#each (group.user_ids || []).slice(0, 5) as userId}
									<span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
										{getUserName(userId)}
									</span>
								{/each}
								{#if (group.user_ids || []).length > 5}
									<span class="text-xs text-gray-500 dark:text-gray-400">
										+{(group.user_ids || []).length - 5} more
									</span>
								{/if}
							</div>
						</div>
						
						<!-- Created by -->
						<div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
							<p class="text-xs text-gray-500 dark:text-gray-400">
								{$i18n.t('Created by')} {getUserName(group.user_id)}
							</p>
						</div>
					</div>
				{/each}
				
				{#if groups.length === 0}
					<div class="col-span-full text-center py-12">
						<div class="mx-auto h-12 w-12 text-gray-400">
							<svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
							</svg>
						</div>
						<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
							{$i18n.t('No groups')}
						</h3>
						<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
							{$i18n.t('Get started by creating a new group.')}
						</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<!-- Create Group Modal -->
{#if showCreateModal}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
				{$i18n.t('Create New Group')}
			</h2>
			
			<form on:submit|preventDefault={handleCreateGroup}>
				<div class="mb-4">
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						{$i18n.t('Group Name')}
					</label>
					<input
						bind:value={groupName}
						type="text"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						required
					/>
				</div>
				
				<div class="mb-4">
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						{$i18n.t('Description')}
					</label>
					<textarea
						bind:value={groupDescription}
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						rows="3"
					></textarea>
				</div>
				
				<div class="mb-4">
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						{$i18n.t('Select Members')}
					</label>
					<div class="max-h-40 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-md p-2">
						{#each users as user (user.id)}
							<label class="flex items-center space-x-2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
								<input
									type="checkbox"
									checked={selectedUserIds.includes(user.id)}
									on:change={() => toggleUserSelection(user.id)}
								/>
								<span class="text-sm text-gray-700 dark:text-gray-300">{user.name}</span>
							</label>
						{/each}
					</div>
				</div>
				
				<div class="flex justify-end space-x-3">
					<button
						type="button"
						on:click={() => {
							showCreateModal = false;
							groupName = '';
							groupDescription = '';
							selectedUserIds = [];
						}}
						class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						type="submit"
						class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
					>
						{$i18n.t('Create Group')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Edit Group Modal -->
{#if showEditModal && selectedGroup}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
				{$i18n.t('Edit Group')}
			</h2>
			
			<form on:submit|preventDefault={handleUpdateGroup}>
				<div class="mb-4">
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						{$i18n.t('Group Name')}
					</label>
					<input
						bind:value={groupName}
						type="text"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						required
					/>
				</div>
				
				<div class="mb-4">
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						{$i18n.t('Description')}
					</label>
					<textarea
						bind:value={groupDescription}
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						rows="3"
					></textarea>
				</div>
				
				<div class="mb-4">
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						{$i18n.t('Select Members')}
					</label>
					<div class="max-h-40 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-md p-2">
						{#each users as user (user.id)}
							<label class="flex items-center space-x-2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
								<input
									type="checkbox"
									checked={selectedUserIds.includes(user.id)}
									on:change={() => toggleUserSelection(user.id)}
								/>
								<span class="text-sm text-gray-700 dark:text-gray-300">{user.name}</span>
							</label>
						{/each}
					</div>
				</div>
				
				<div class="flex justify-end space-x-3">
					<button
						type="button"
						on:click={() => {
							showEditModal = false;
							groupName = '';
							groupDescription = '';
							selectedUserIds = [];
							selectedGroup = null;
						}}
						class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						type="submit"
						class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
					>
						{$i18n.t('Update Group')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
