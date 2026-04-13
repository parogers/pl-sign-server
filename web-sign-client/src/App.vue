<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';

const connected = ref(false);
const message = ref('');
const preview = ref('');

function useWebSocket(url: string) {
    const socket = new WebSocket(url);
    const messages = ref([]);
    const lastMessage = ref('');

    socket.onmessage = (event) => {
        console.log('message', event.data);
        lastMessage.value = JSON.parse(event.data);
        // messages.value.push(JSON.parse(event.data));
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
    return { messages, send, lastMessage };
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
    <main>
        <textarea
            placeholder="Your message here"
            rows="5"
            cols="80"
            v-model="message">
        </textarea>

        <button @click="onPost()">
            Submit
        </button>

        <p>Sign status: {{ connected ? 'connected' : 'disconnected' }}</p>

        <p>Currently displaying:</p>

        <pre>{{ preview }}</pre>
    </main>
</template>

<style scoped>
button {
    display: block;
    font-size: larger;
}

pre {
    font-size: xx-large;
}
</style>
