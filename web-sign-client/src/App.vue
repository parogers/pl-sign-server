<script setup lang="ts">
import { ref, watch, reactive, onUnmounted, onMounted } from 'vue';

const CLIENT_ID_KEY = 'sign-client-id';
const SERVER_PORT = 8000;
const MAX_MESSAGE_LEN = 50

const isConnected = ref(false);
const isSignConnected = ref(false);
const message = ref('');
const lastMessage = ref('');
const preview = reactive<string[]>([]);
const clientID = ref('');

function getServerUrl(): string {
    return (
        import.meta.env.VITE_SIGN_SERVER ??
        `${location.protocol}//${location.hostname}:${SERVER_PORT}`
    );
}

function getClientID(): string {
    if (localStorage.getItem(CLIENT_ID_KEY)) {
        return localStorage.getItem(CLIENT_ID_KEY) ?? '';
    }
    const clientID = ('' + Math.random()).slice(2);
    localStorage.setItem(CLIENT_ID_KEY, clientID);
    return clientID;
}

function useWebSocket(url: string)
{
    const lastSocketMessage = ref<any>('');
    let socket: WebSocket|null = null;

    function onMessage(event: any) {
        isConnected.value = true;
        lastSocketMessage.value = JSON.parse(event.data);
    }
    function onClose() {
        isConnected.value = false;
        console.warn('WebSocket closed... reconnecting');
        setTimeout(() => init(), 3000);
    }
    function onError(err: any) {
        console.error('WebSocket error:', err);
    }
    function onOpen() {
        isConnected.value = true;
    }
    function init() {
        socket = new WebSocket(url);
        socket.onmessage = onMessage;
        socket.onclose = onClose;
        socket.onerror = onError;
        socket.onopen = onOpen;
    }
    const send = (msg: any) => {
        if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(msg));
        }
    }
    onUnmounted(() => socket?.close());
    init();
    return { send, lastSocketMessage };
}

const { lastSocketMessage } = useWebSocket(`${getServerUrl()}/ws/`);

watch(lastSocketMessage, () => {
    if (lastSocketMessage.value?.message) {
        preview.length = 0;
        preview.push(...<string[]>lastSocketMessage.value.messages);
    }
    if ('sign_connected' in lastSocketMessage.value) {
        isSignConnected.value = !!lastSocketMessage.value.sign_connected;
    }
});

onMounted(() => {
    clientID.value = getClientID();
});

function onPost() {
    lastMessage.value = message.value;
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

function isSubmitEnabled() {
    return lastMessage.value !== message.value && isConnected.value;
}

</script>

<template>
    <main>
        <div class="input-area">
            <textarea
                placeholder="Your message here"
                v-model="message"
                :maxlength="MAX_MESSAGE_LEN"
                @keydown.enter.prevent="onPost()"
            >
            </textarea>
            <div class="button-area">
                <button @click="onPost()" :disabled="!isSubmitEnabled()">
                    Post message
                </button>

                <div class="char-count">({{ message.length }}/{{ MAX_MESSAGE_LEN }} chars)</div>
            </div>
        </div>

        <div v-if="!isConnected" class="disconnected">
            Connecting to server...
        </div>

        <div v-if="isConnected && !isSignConnected" class="disconnected">
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
    padding: 0.25em 0.5em;
    color: inherit;
    background: #eee;
    border: none;
    outline: solid 1px lightgray;
    border-radius: 0.25em;
    box-shadow: 2px 4px 6px rgb(0, 0, 0, 0.25);
}

button:disabled {
    color: gray;
    outline: solid 1px #eee;
    pointer-events: none;
}

button:active {
    box-shadow: none;
    transform: scale(0.95);
}

textarea {
    font-size: larger;
    display: block;
    width: 100%;
    height: 5em;
    padding: 0.5em;
    box-sizing: border-box;
    border: solid 1px lightgray;
    border-radius: 0.25em;
    margin-bottom: 1em;
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
    margin-top: 2em;
    border-radius: 0.25em;
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

.char-count {
    color: gray;
}
</style>
