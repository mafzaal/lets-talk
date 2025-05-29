<script lang="ts">
	import marked from './marked';
	import { scale, fade, blur } from 'svelte/transition';
	import { Client } from '@langchain/langgraph-sdk';
	import typewriter from './typewriter';

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

	// new Message('human', 'Hello! How can I assist you today?'),
	// new Message('ai', 'Hi there! I am here to help you with any questions or tasks you have.')

	const client = new Client( { apiUrl: 'http://localhost:2024/'
});
	const messages = $state<Array<Message>>([]);
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
			let inputMessages = []
			if(messages.length === 1)
			{
				const options = Intl.DateTimeFormat().resolvedOptions()
				const timezone = options.timeZone;
				const language = options.locale;

				inputMessages.push({
					role: 'system',
					content: `User's timezone: ${timezone} and language: ${language}.\nAlways convert date and time to user's timezone`
				});


			}

			inputMessages.push(userMsg.toJSON());
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
				scrollToBottom();
			}
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
			userInput = '';
		}
	}

	function scrollToBottom() {
		const chatContainer = document.querySelector('.flex-1');
		if (chatContainer) {
			chatContainer.scrollTo({
				top: chatContainer.scrollHeight,
				behavior: 'smooth'
			});
		}
	}

	$effect(() => {
		if (messages.length) {
			scrollToBottom();
		}
	});
</script>

{#if showChat}
	<div
		in:scale={{ duration: 300  }}
		out:scale={{ duration: 300  }}
		class="flex flex-col gap-2 items-center justify-center bg-gray-100 p-4 border rounded-xl mb-14"
	>
		<!-- Chat Widget -->

		<div class="flex gap-2 items-center justify-center rounded-xl">
			<!-- Buttons to add messages -->
			<button
				class="bg-blue-100 hover:bg-blue-300 p-4 text-white rounded shadow-lg flex items-center justify-center text-3xl focus:outline-none focus:ring"
				onclick={() => messages.push(new Message('human', 'Hello! How can I assist you today?'))}
				aria-label="Add human message"
			>
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
			</button>

			<button
				class=" bg-blue-100 hover:bg-blue-300 p-4 text-white rounded shadow-lg flex items-center justify-center text-3xl focus:outline-none focus:ring"
				onclick={() => messages.push(new Message('AI', 'Hello! How can I assist you today?'))}
				aria-label="Add AI message"
			>
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
			</button>
		</div>
		<div class="w-100 h-100 bg-white shadow-lg rounded-lg flex flex-col">
			<div class="flex-1 overflow-y-auto p-4">
				{#each messages as msg}
					<div
						in:scale={{ duration: 300 }}
						class="flex gap-2 mb-3 p-3 rounded-lg text-base flex-col"
						class:bg-blue-50={msg.role === 'human'}
						class:bg-green-50={msg.role === 'ai'}
						class:text-right={msg.role === 'human'}
						class:text-left={msg.role === 'ai'}
						class:items-end={msg.role === 'human'}
					>
						<div class="flex flex-1 gap-1" class:flex-row-reverse={msg.role === 'human'}>
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
							<!-- <strong>{msg.role === 'human' ? 'You' : 'AI'}</strong> -->
						</div>

						<div class="prose max-w-full markdown">
							{@html marked.parse(msg.content)}
						</div>
					</div>
				{/each}
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
	</div>
{/if}

<button
	in:fade={{ duration: 300 }}
	out:blur={{ duration: 300 }}
	class="fixed bottom-4 right-4 bg-blue-700 hover:bg-blue-800 text-white rounded-full shadow-lg w-12 h-12 flex items-center justify-center text-3xl focus:outline-none focus:ring"
	onclick={() => (showChat = !showChat)}
	aria-label="Open chat"
>
	<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
		{#if !showChat}
			<path
				in:fade={{ duration: 300 }}
				d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z"
				fill="white"
			/>
			<path
				in:fade={{ duration: 300 }}
				d="M7 9H17M7 13H14"
				stroke="white"
				stroke-width="2"
				stroke-linecap="round"
			/>
		{:else}
			<path
				in:fade={{ duration: 300 }}
				d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z"
				fill="white"
			/>
		{/if}
	</svg>
</button>
