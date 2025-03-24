function updateSavingsPanel(savings: any): void {
  const stats = document.getElementById("savings-stats");
  const bar = document.getElementById("savings-bar-fill");

  if (stats && bar) {
    const { original_chars, summarized_chars, saved } = savings;

    const summaryRatio = original_chars > 0
      ? Math.round((summarized_chars / original_chars) * 100)
      : 0;

    const savedPercentage = original_chars > 0
      ? Math.round((saved / original_chars) * 100)
      : 0;

    // Update visual bar (shows how much of memory is "used")
    bar.style.width = `${summaryRatio}%`;

    // Show all 3 stats
    stats.innerHTML = `
      Original: ${original_chars}<br>
      Summarized: ${summarized_chars}<br>
      Saved: ${savedPercentage}%
    `;
  }
}

function loadInitialSavings(): void {
  fetch("/api/stats")
    .then(response => response.json())
    .then(data => {
      if (data.savings) {
        updateSavingsPanel(data.savings);
      }
    })
    .catch(err => {
      console.error("Failed to load initial savings:", err);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  loadInitialSavings(); // ✅ Load panel as soon as page is ready

  const sendButton = document.getElementById("send-button");
  const input = document.getElementById("user-input") as HTMLInputElement;
  const messages = document.getElementById("chat-messages");
  const typingIndicator = document.getElementById("typing-indicator");

  function appendMessage(role: string, content: string) {
    const messageCard = document.createElement("div");
    messageCard.classList.add("message-card", role);
    messageCard.innerText = content;
    messages?.appendChild(messageCard);
    messages?.scrollTo(0, messages.scrollHeight);
  }

  function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    appendMessage("user", message);
    input.value = "";
    typingIndicator!.style.visibility = "visible";

    fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    })
      .then((res) => res.json())
      .then((data: ApiResponse) => {
        typingIndicator!.style.visibility = "hidden";
        appendMessage("assistant", data.response);
        updateSavingsPanel(data.savings); // ✅ Update savings after response too
      })
      .catch((err) => {
        typingIndicator!.style.visibility = "hidden";
        console.error("Fetch error:", err);
      });
  }

  sendButton?.addEventListener("click", sendMessage);
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});

interface ApiResponse {
  response: string;
  summary: string;
  savings: {
    original_chars: number;
    summarized_chars: number;
    saved: number;
    percentage: number;
  };
}
