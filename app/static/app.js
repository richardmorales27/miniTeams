const displayNameInput = document.getElementById("display-name");
const messageList = document.getElementById("message-list");
const messageForm = document.getElementById("message-form");
const messageInput = document.getElementById("message-input");
const socket = new WebSocket(`ws://${window.location.host}/ws`);


socket.addEventListener("open", () => {
    console.log("WebSocket connected");
});

socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    const emptyMessage = messageList.querySelector(".empty-message");
    if (emptyMessage) {emptyMessage.remove();}
    const messageElement = document.createElement("div");

    const nameElement = document.createElement("strong");
    nameElement.textContent = message.display_name;

    const textElement = document.createElement("p");
    textElement.textContent = message.message;

    messageElement.appendChild(nameElement);
    messageElement.appendChild(textElement);

    messageList.appendChild(messageElement);

    messageList.scrollTop = messageList.scrollHeight;
});

socket.addEventListener("close", () => {
    console.log("WebSocket disconnected");
});

socket.addEventListener("error", (error) => {
    console.error("WebSocket error:", error);
});

//Temporary Event handlers --------------------
messageForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const displayName = displayNameInput.value.trim();
    const messageText = messageInput.value.trim();

    if (!displayName || !messageText) {
        return;
    }

    const message = {
        display_name: displayName,
        message: messageText
    };

    socket.send(JSON.stringify(message));

    messageInput.value = "";
    messageInput.focus();
});
// --------------------------------------------

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
        const messageElement = document.createElement("div");

        const nameElement = document.createElement("strong");
        nameElement.textContent = message.display_name;

        const textElement = document.createElement("p");
        textElement.textContent = message.message;

        messageElement.appendChild(nameElement);
        messageElement.appendChild(textElement);

        messageList.appendChild(messageElement);
    });
}


messageForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const displayName = displayNameInput.value.trim();
    const messageText = messageInput.value.trim();

    if (!displayName || !messageText) {
        return;
    }

    const response = await fetch("/messages", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            display_name: displayName,
            message: messageText
        })
    });

    if (!response.ok) {
        console.error("Failed to send message");
        return;
    }

    messageInput.value = "";

    await loadMessages();

    messageInput.focus();
});


loadMessages();

