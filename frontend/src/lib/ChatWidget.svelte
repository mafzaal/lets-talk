<script lang="ts">
	import marked from './marked';

	import { Client } from '@langchain/langgraph-sdk';

	class Message {
		role: string = $state('human');
		content: string = $state('');
		id: string | null = $state('');

		constructor(role: string, content: string, id: string | null = null) {
			this.id = id;
			this.role = role;
			this.content = content;
		}

		toJSON() {
			return {
				role: this.role,
				content: this.content,
				id: this.id
			};
		}
		static fromJSON(json: any): Message {
			return new Message(json.role, json.content, json.id);
		}
	}

	const client = new Client();
	const messages = $state<Array<Message>>([new Message('human', 'Hello! How can I assist you today?'),
        new Message('ai', 'Hi there! I am here to help you with any questions or tasks you have.')]);
	let userInput = $state<string>('');
	let loading = $state(false);
	let assistant_id = $state<string | null>(null);
	let thread_id = $state<string | null>(null);

	let disabled = $derived(userInput.trim() === '' || loading);
	let showChat = $state(false);

	async function sendMessage() {
		if (!userInput.trim()) return;
		const userMsg = new Message('human', userInput);
		messages.push(userMsg);
		loading = true;
		try {
			// List all assistants
			if (!assistant_id) {
				const assistants = await client.assistants.search({
					metadata: null,
					offset: 0,
					limit: 10
				});
				if (assistants.length > 0) {
					assistant_id = assistants[0]['assistant_id'];
				} else {
					throw new Error('No assistants found');
				}
			}

			if (!thread_id) {
				// Create a new thread if it doesn't exist
				const thread = await client.threads.create();
				if (thread) {
					thread_id = thread['thread_id'];
				} else {
					throw new Error('No threads found');
				}
			}
			// Start a new thread
			// const thread = await client.threads.create();
			// Prepare messages
			const inputMessages = [userMsg.toJSON()];
			const streamResponse = client.runs.stream(thread_id, assistant_id, {
				input: { messages: inputMessages },
				streamMode: 'messages-tuple'
			});

            userInput = '';

			let aiMsg = new Message('ai', '');
			messages.push(aiMsg);
			for await (const chunk of streamResponse) {
				if (chunk?.event === 'messages') {
					// Handle the message event
					const [msg, _] = chunk.data;

					//@ts-ignore
					if (msg.type === 'AIMessageChunk') {
						//@ts-ignore
						aiMsg.content += msg.content;
					}
				}
			}
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
			userInput = '';
		}
	}

	
</script>


<div class="flex flex-col gap-2 items-center justify-center bg-gray-100 p-4 border rounded-xl">
<!-- Chat Widget -->
	<div class="w-100 h-100 bg-white shadow-lg rounded-lg flex-col" style:display={showChat ? 'flex' : 'none'}>
		<div class="flex-1 overflow-y-auto p-4">
			{#each messages as msg}
				<div
					class="flex gap-2 mb-3 p-3 rounded-lg text-base flex-col"
					class:bg-blue-50={msg.role === 'human'}
					class:bg-green-50={msg.role === 'ai'}
					class:text-right={msg.role === 'human'}
					class:text-left={msg.role === 'ai'}
                    class:items-end={msg.role === 'human'}
				>
                <div class="flex flex-1 gap-1"
                    class:flex-row-reverse={msg.role === 'human'}>
					<span class="shrink-0">
						{#if msg.role === 'human'}
							<svg
								width="24"
								height="24"
								viewBox="0 0 24 24"
								fill="none"
								xmlns="http://www.w3.org/2000/svg"
								><circle cx="12" cy="8" r="4" fill="#1976d2" /><path
									d="M4 20c0-2.21 3.58-4 8-4s8 1.79 8 4"
									fill="#1976d2"
								/></svg
							>
						{:else}
							<svg
								width="24"
								height="24"
								viewBox="0 0 24 24"
								fill="none"
								xmlns="http://www.w3.org/2000/svg"
								><rect x="4" y="7" width="16" height="10" rx="5" fill="#43a047" /><circle
									cx="8.5"
									cy="12"
									r="1.5"
									fill="#fff"
								/><circle cx="15.5" cy="12" r="1.5" fill="#fff" /><rect
									x="11"
									y="3"
									width="2"
									height="4"
									rx="1"
									fill="#43a047"
								/></svg
							>
						{/if}
					</span>
					<strong>{msg.role === 'human' ? 'You' : 'AI'}</strong>
                    </div>
                
                    <div class="prose max-w-full markdown">
                        {@html marked.parse(msg.content)}
                    </div>
					
				</div>
			{/each}
			<!-- {#if loading}
				<div class="flex items-center gap-3 mb-3 p-3 rounded-lg bg-green-50 text-base">
					<span class="shrink-0"
						><svg
							width="24"
							height="24"
							viewBox="0 0 24 24"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
							><rect x="4" y="7" width="16" height="10" rx="5" fill="#43a047" /><circle
								cx="8.5"
								cy="12"
								r="1.5"
								fill="#fff"
							/><circle cx="15.5" cy="12" r="1.5" fill="#fff" /><rect
								x="11"
								y="3"
								width="2"
								height="4"
								rx="1"
								fill="#43a047"
							/></svg
						></span
					>
					<em>AI is typing...</em>
				</div>
			{/if} -->
		</div>
		<form class="flex gap-2 p-3 border-t bg-gray-50" onsubmit={sendMessage}>
			<input
				type="text"
				class="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
				bind:value={userInput}
				placeholder="Type your message..."
				autocomplete="off"
			/>
			<button
				type="submit"
				class="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
				{disabled}
			>
				Send
			</button>
		</form>
	</div>

	<button
		class="bg-blue-700 hover:bg-blue-800 text-white rounded-full shadow-lg w-16 h-16 flex items-center justify-center text-3xl focus:outline-none focus:ring"
		onclick={() => (showChat = !showChat)}
		aria-label="Open chat"
	>
		{#if !showChat}
			<!-- Icon for open chat -->
			💬
		{:else}
			<!-- Icon for close chat -->
			✕
		{/if}
	</button>
    </div>