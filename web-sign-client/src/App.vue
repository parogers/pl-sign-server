<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';

const SERVER_PORT = 8000;
const connected = ref(false);
const message = ref('');
const preview = ref('');

function getServerUrl(): string {
    return (
        import.meta.env.VITE_SIGN_SERVER ??
        `${location.protocol}//${location.hostname}:${SERVER_PORT}`
    );
}

function useWebSocket(url: string) {
    const socket = new WebSocket(url);
    const lastMessage = ref<any>('');

    socket.onmessage = (event) => {
        lastMessage.value = JSON.parse(event.data);
    }
    socket.onclose = () => {
        console.warn('WebSocket closed... reconnecting')
        setTimeout(() => useWebSocket(url), 3000)
    }
    socket.onerror = (err) => {
        console.error('WebSocket error:', err)
    }
    const send = (msg: any) => {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(msg));
        }
    }
    onUnmounted(() => socket.close());
    return { send, lastMessage };
}

const { lastMessage } = useWebSocket(`${getServerUrl()}/ws/`);

watch(lastMessage, () => {
    if (lastMessage?.value?.message) {
        preview.value = lastMessage.value.message;
    }
    if ('sign_connected' in lastMessage.value) {
        connected.value = !!lastMessage.value.sign_connected;
    }
});

function onPost() {
    fetch(`${getServerUrl()}/message/`, {
        method: 'POST',
        headers: {
            'Content-type' : 'application/json',
        },
        body: JSON.stringify({
            content: message.value,
        }),
    });
}

</script>

<template>
    <main>
        <pre>{{ preview }}</pre>

        <div class="input-area">
            <textarea placeholder="Enter your message here" v-model="message">
            </textarea>

            <button @click="onPost()">
                Submit
            </button>
        </div>

        <div v-if="!connected" class="disconnected">
            Sign not connected
        </div>
    </main>
</template>

<style scoped>
button {
    display: block;
    font-size: larger;
}

textarea {
    display: block;
    width: 100%;
    height: 10em;
    box-sizing: border-box;
    border: solid 1px gray;
    padding: 1em;
    margin-top: 1em;
    margin-bottom: 1em;
}

pre {
    font-size: xx-large;
    width: 100%;
    border: solid 1px gray;
    padding: 0.5em;
    box-sizing: border-box;
    background: #444;
    color: orange;
    font-weight: bold;
    margin: 0;
}

main {
    max-width: 80ch;
    margin-left: auto;
    margin-right: auto;
    padding: 1em;
}

.disconnected {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 2em;
    font-style: italic;
    background: #a00000;
    color: white;
    padding: 0.5em;
    margin-top: 1em;
    font-weight: bold;
}

.input-area {
}
</style>
