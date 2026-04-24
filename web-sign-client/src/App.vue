<script setup lang="ts">
import { ref, watch, reactive, onUnmounted, onMounted } from 'vue';

const CLIENT_ID_KEY = 'sign-client-id';
const SERVER_PORT = 8000;
const MAX_MESSAGE_LEN = 50;
const MAX_NAME_LEN = 10;

const isConnected = ref(false);
const isSignConnected = ref(false);
const message = ref('');
const lastMessage = ref('');
const lastName = ref('');
const preview = reactive<string[]>([]);
const clientID = ref('');
const name = ref('');

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
        console.info('WebSocket connected');
        isConnected.value = true;
    }
    function init() {
        console.info('WebSocket connecting...')
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
    lastName.value = name.value;
    fetch(`${getServerUrl()}/message/`, {
        method: 'POST',
        headers: {
            'Content-type' : 'application/json',
        },
        body: JSON.stringify({
            name: name.value,
            content: message.value,
            client_id: clientID.value,
        }),
    });
}

function isSubmitEnabled() {
    return isConnected.value && message.value && (
        lastMessage.value !== message.value ||
        lastName.value !== name.value
    );
}
</script>

<template>
    <main>
        <div class="input-area">
            <div class="name-area">
                <input
                    v-model="name"
                    type="text"
                    :maxlength="MAX_NAME_LEN"
                    placeholder="Your name (optional)"
                    @keydown.enter.prevent="onPost()"
                />
                <div class="name-char-count">({{ name.length }}/{{ MAX_NAME_LEN }})</div>
            </div>

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

                <div class="message-char-count">({{ message.length }}/{{ MAX_MESSAGE_LEN }})</div>
            </div>
        </div>

        <div v-if="!isConnected" class="disconnected">
            Connecting to server...
        </div>

        <div v-if="isConnected && !isSignConnected" class="disconnected">
            Sign not connected
        </div>

        <div class="preview">
            <p v-if="preview.length === 0">&nbsp;</p>
            <p v-for="message in preview">{{ message }}</p>
        </div>
    </main>
</template>

<style scoped>
button {
    display: block;
    font-size: larger;
    padding: 0.25em 0.5em;
    color: var(--color-button-text);
    background: var(--color-button-bg);
    border: none;
    outline: solid 1px var(--color-button-text);
    border-radius: 0.25em;
    box-shadow: 2px 4px 6px rgb(0, 0, 0, 0.25);
}

button:disabled {
    opacity: 0.5;
    outline: solid 1px #eee;
    pointer-events: none;
}

button:active {
    box-shadow: none;
    transform: scale(0.95);
}

textarea {
    font-size: 1rem;
    font-family: monospace;
    display: block;
    width: 100%;
    height: 5em;
    padding: 0.5em;
    box-sizing: border-box;
    border: solid 1px lightgray;
    border-radius: 0.25em;
    margin-bottom: 1em;
    background: var(--color-input-bg);
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

.message-char-count {
    position: relative;
    top: -2.5em;
    left: -0.5em;
    color: gray;
}

.name-area {
    display: flex;
    flex-direction: column;
    align-items: end;
    position: relative;
}

.name-char-count {
    position: absolute;
    top: 0.5em;
    right: 0.5em;
    color: gray;
}

input {
    width: 100%;
    box-sizing: border-box;
    font-family: monospace;
    padding: 0.5em;
    font-size: 1rem;
    display: inline-block;
    margin-bottom: 1em;
    border: solid 1px lightgray;
    background: var(--color-input-bg);
    border-radius: 0.25em;
}
</style>
