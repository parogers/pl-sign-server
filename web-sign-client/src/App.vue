<script setup lang="ts">
import { ref, watch, reactive, onUnmounted, onMounted } from 'vue';

const CLIENT_ID_KEY = 'sign-client-id';
const SERVER_PORT = 8000;
const MAX_MESSAGE_LEN = 50

const connected = ref(false);
const message = ref('');
const preview = reactive([]);
const clientID = ref('');

function getServerUrl(): string {
    return (
        import.meta.env.VITE_SIGN_SERVER ??
        `${location.protocol}//${location.hostname}:${SERVER_PORT}`
    );
}

function getClientID(): string {
    if (localStorage.getItem(CLIENT_ID_KEY)) {
        return localStorage.getItem(CLIENT_ID_KEY);
    }
    const clientID = ('' + Math.random()).slice(2);
    localStorage.setItem(CLIENT_ID_KEY, clientID);
    return clientID;
}

function useWebSocket(url: string, callbacks: any)
{
    const lastMessage = ref<any>('');
    let socket = null;

    function onMessage(event) {
        lastMessage.value = JSON.parse(event.data);
    }
    function onClose() {
        console.warn('WebSocket closed... reconnecting');
        setTimeout(() => init(), 3000);
    }
    function onError(err) {
        console.error('WebSocket error:', err);
    }
    function init() {
        socket = new WebSocket(url);
        socket.onmessage = onMessage;
        socket.onclose = onClose;
        socket.onerror = onError;
    }
    const send = (msg: any) => {
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(msg));
        }
    }
    onUnmounted(() => socket?.close());
    init();
    return { send, lastMessage };
}

const { lastMessage } = useWebSocket(`${getServerUrl()}/ws/`);

watch(lastMessage, () => {
    if (lastMessage?.value?.message) {
        preview.length = 0;
        preview.push(...lastMessage.value.messages);
    }
    if ('sign_connected' in lastMessage.value) {
        connected.value = !!lastMessage.value.sign_connected;
    }
});

onMounted(() => {
    clientID.value = getClientID();
});

function onPost() {
    fetch(`${getServerUrl()}/message/`, {
        method: 'POST',
        headers: {
            'Content-type' : 'application/json',
        },
        body: JSON.stringify({
            content: message.value,
            client_id: clientID.value,
        }),
    });
}
</script>

<template>
    <main>
        <div class="input-area">
            <textarea
                placeholder="Enter your message here"
                v-model="message"
                :maxlength="MAX_MESSAGE_LEN"
            >
            </textarea>
            <div class="button-area">
                <button @click="onPost()">
                    Post message
                </button>

                <div>({{ message.length }}/{{ MAX_MESSAGE_LEN }} chars)</div>
            </div>
        </div>

        <div v-if="!connected" class="disconnected">
            Sign not connected
        </div>

        <div class="preview">
            <p v-for="message in preview">{{ message }}</p>
        </div>
    </main>
</template>

<style scoped>
button {
    display: block;
    font-size: larger;
    padding: 0.25em;
    color: inherit;
}

textarea {
    display: block;
    width: 100%;
    height: 5em;
    padding: 0.5em;
    box-sizing: border-box;
    border: solid 1px #aaa;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

.preview {
    font-size: x-large;
    width: 100%;
    border: solid 1px gray;
    padding: 0.75em;
    box-sizing: border-box;
    background: #444;
    color: orange;
    font-weight: bold;
    font-family: monospace;
    margin: 0;
    margin-top: 1em;
}

.preview p:first-of-type {
    margin-top: 0;
}

.preview p:last-of-type {
    margin-bottom: 0;
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

.button-area {
    display: flex;
    justify-content: space-between;
}
</style>
