
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat");

function addMessage(text, sender, sources = []) {
    const message = document.createElement("div");
    message.className = `message ${sender}`;

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = sender === "user" ? "You" : "DIEMS Assistant";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = text;

    message.append(label, bubble);

    if (sources.length && sender === "assistant") {
        const sourceElement = document.createElement("div");
        sourceElement.className = "message-source";
        sourceElement.textContent = `Source: ${sources.map((item) => item.source || item).filter(Boolean).join(" • ")}`;
        message.appendChild(sourceElement);
    }

    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return message;
}

function showWelcome() {
    chatMessages.replaceChildren();

    const welcome = document.createElement("div");
    welcome.className = "welcome";

    const icon = document.createElement("div");
    icon.className = "welcome-icon";
    icon.textContent = "D";

    const title = document.createElement("h2");
    title.textContent = "Welcome to DIEMS!";

    const description = document.createElement("p");
    description.textContent =
        "Ask me about courses, fees, eligibility, required documents and campus facilities.";

    welcome.append(icon, title, description);
    chatMessages.appendChild(welcome);
}

async function sendMessage(question) {
    const cleanedQuestion = question.trim();

    if (!cleanedQuestion || sendButton.disabled) {
        return;
    }

    // Display the question immediately.
    addMessage(cleanedQuestion, "user");

    messageInput.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    const loadingMessage = addMessage(
        "Searching DIEMS admission information...",
        "assistant"
    );

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: cleanedQuestion
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "The request failed.");
        }

        loadingMessage.remove();

        addMessage(
            data.answer || "Sorry, no answer was returned.",
            "assistant",
            data.sources || (data.source ? [data.source] : [])
        );
    } catch (error) {
        loadingMessage.remove();

        addMessage(
            "I couldn't connect to the chatbot server. " +
            "Please check that Flask is running and try again.",
            "assistant"
        );

        console.error("Chat error:", error);
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send ↑";
        messageInput.focus();
    }
}

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(messageInput.value);
});

document.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => {
        sendMessage(button.dataset.question);
    });
});

newChatButton.addEventListener("click", () => {
    showWelcome();
    messageInput.value = "";
    messageInput.focus();
});

messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        messageInput.value = "";
    }
});
