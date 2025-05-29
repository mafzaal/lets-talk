<script lang="ts">
	import ChatWidget from '$lib/ChatWidget.svelte';

	//@ts-ignore
	import { RemoteGraph } from '@langchain/langgraph/remote';
	const url = `http://localhost:8123/`;
	const graphName = 'the_data_guy_chat';
	const remoteGraph = new RemoteGraph({ graphId: graphName, url });

	async function main() {
		
		

		// invoke the graph
		// const result = await remoteGraph.invoke({
		// 	messages: [{ role: 'user', content: "what's the weather in sf" }]
		// });

		// get users timezone using javascript
		const options = Intl.DateTimeFormat().resolvedOptions()
		const timezone = options.timeZone;
		const language = options.locale;
		console.log(options)
		console.log(`User's timezone: ${timezone}`);
		

		
		// stream outputs from the graph
		for await (const chunk of await remoteGraph.stream({
			messages: [
				{ role: 'system', content: `User's timezone: ${timezone} and language: ${language}.\nAlways convert date and time to user's timezone` },
				{ role: 'user', content: "What is current time?" }
			]
		}))
			console.log(chunk);
	}
	//main().catch(console.error);
</script>

<div class="fixed bottom-6 right-6 z-40">
	<ChatWidget />
</div>
