const displayNameInput = document.getElementById("display-name");
const messageList = document.getElementById("message-list");
const messageForm = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const sendButton = messageForm.querySelector("button[type='submit']");
let socket;
let reconnectTimer;

function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    sendButton.disabled = true;

    socket.addEventListener("open", () => {
        console.log("WebSocket connected");
        sendButton.disabled = false;
    });

    socket.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "error") {
            console.error(message.message);
            return;
        }

        appendMessage(message);
    });

    socket.addEventListener("close", () => {
        console.log("WebSocket disconnected");
        sendButton.disabled = true;
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectWebSocket, 2000);
    });

    socket.addEventListener("error", (error) => {
        console.error("WebSocket error:", error);
    });
}

function appendMessage(message) {
    const emptyMessage = messageList.querySelector(".empty-message");
    if (emptyMessage) {
        emptyMessage.remove();
    }
    const messageElement = document.createElement("div");

    const nameElement = document.createElement("strong");
    nameElement.textContent = message.display_name;

    const textElement = document.createElement("p");
    textElement.textContent = message.message;

    messageElement.appendChild(nameElement);
    messageElement.appendChild(textElement);
    messageList.appendChild(messageElement);
    messageList.scrollTop = messageList.scrollHeight;
}

messageForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const displayName = displayNameInput.value.trim();
    const messageText = messageInput.value.trim();

    if (!displayName || !messageText) {
        return;
    }

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.error("WebSocket is not connected");
        return;
    }

    socket.send(JSON.stringify({
        display_name: displayName,
        message: messageText
    }));

    messageInput.value = "";
    messageInput.focus();
});

async function loadMessages() {
    const response = await fetch("/messages");

    if (!response.ok) {
        console.error("Failed to load messages");
        return;
    }

    const messages = await response.json();

    messageList.innerHTML = "";

    if (messages.length === 0) {
        messageList.innerHTML = `
            <p class="empty-message">
                No messages yet.
            </p>
        `;

        return;
    }

    messages.forEach((message) => {
        appendMessage(message);
    });
}

async function startApp() {
    await loadMessages();
    connectWebSocket();
}

startApp();
