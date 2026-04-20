<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';

const connected = ref(false);
const message = ref('');
const preview = ref('');

function useWebSocket(url: string) {
    const socket = new WebSocket(url);
    const lastMessage = ref('');

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
    const send = (msg) => {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(msg));
        }
    }
    onUnmounted(() => socket.close());
    return { send, lastMessage };
}

const { lastMessage } = useWebSocket('http://localhost:8000/ws/');

watch(lastMessage, () => {
    if (lastMessage?.value?.message) {
        preview.value = lastMessage.value.message;
    }
    if ('sign_connected' in lastMessage.value) {
        connected.value = lastMessage.value.sign_connected;
    }
});

function onPost() {
    fetch('http://localhost:8000/message/', {
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
    <div v-if="!connected" class="disconnected">
        Sign not connected
    </div>

    <main>
        <pre>{{ preview }}</pre>

        <div class="input-area">
            <textarea placeholder="Enter your message here" v-model="message">
            </textarea>

            <button @click="onPost()">
                Submit
            </button>
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
}

main {
    margin: 1em;
}

.disconnected {
    position: absolute;
    display: flex;
    align-items: center;
    justify-content: center;
    top: 0;
    left: 0;
    right: 0;
    height: 2em;
    font-style: italic;
    background: #a00000;
    color: white;
    padding: 0.5em;
    font-weight: bold;
}

.input-area {
}
</style>
