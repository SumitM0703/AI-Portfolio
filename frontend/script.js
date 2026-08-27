const input = document.getElementById("chatInput");
const button = document.getElementById("sendButton");
const chatMessages = document.getElementById("chatMessages");

button.addEventListener("click", sendMessage);

input.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});
function formatAnswer(text) {
    return text
        // Remove Markdown bold stars: **text**
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")

        // Make important JD headings bold
        .replace(
            /^(MATCH SCORE:?)$/gim,
            "<strong>$1</strong>"
        )
        .replace(
            /^(MATCHING SKILLS:?)$/gim,
            "<strong>$1</strong>"
        )
        .replace(
            /^(MISSING \/ REQUIRED SKILLS:?)$/gim,
            "<strong>$1</strong>"
        )
        .replace(
            /^(STRENGTHS:?)$/gim,
            "<strong>$1</strong>"
        )
        .replace(
            /^(RECOMMENDATIONS:?)$/gim,
            "<strong>$1</strong>"
        )
        .replace(
            /^(FINAL VERDICT:?)$/gim,
            "<strong>$1</strong>"
        )

        // New lines → HTML line breaks
        .replace(/\n/g, "<br>");
}

async function sendMessage() {

    const question = input.value.trim();

    if (question === "") {
        return;
    }

    // Show user message
    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.textContent = question;

    chatMessages.appendChild(userMessage);

    input.value = "";

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Loading message
    const loadingMessage = document.createElement("div");
    loadingMessage.className = "bot-message";
    loadingMessage.textContent = "Thinking...";

    chatMessages.appendChild(loadingMessage);

    button.disabled = true;

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question
                })
            }
        );

        const data = await response.json();

        // Replace Thinking... with actual answer
        loadingMessage.innerHTML = formatAnswer(data.answer);

    } catch (error) {

        console.error(error);

        loadingMessage.textContent =
            "Sorry, I couldn't connect to the AI server.";

    } finally {

        button.disabled = false;

        chatMessages.scrollTop =
            chatMessages.scrollHeight;
    }
}
// ============================================================
// JD MATCHER
// ============================================================

const jdFile = document.getElementById("jdFile");
const jdButton = document.getElementById("jdButton");
const jdResult = document.getElementById("jdResult");

if (jdButton) {
    jdButton.addEventListener("click", async function () {

        if (!jdFile.files.length) {
            alert("Please select a PDF or DOCX file first.");
            return;
        }

        const file = jdFile.files[0];

        const formData = new FormData();
        formData.append("file", file);

        jdButton.disabled = true;
        jdButton.textContent = "Analyzing...";

        jdResult.innerHTML = "🤖 Analyzing your JD...";

        try {

            const response = await fetch(
                "http://127.0.0.1:8000/match-jd",
                {
                    method: "POST",
                    body: formData
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Something went wrong.");
            }

            jdResult.innerHTML = `
    <div class="jd-result-box">
        ${data.answer}
    </div>
`;

        } catch (error) {

            jdResult.innerHTML =
                `<strong>❌ Error:</strong> ${error.message}`;

        } finally {

            jdButton.disabled = false;
            jdButton.textContent = "Analyze JD →";
        }
    });
}