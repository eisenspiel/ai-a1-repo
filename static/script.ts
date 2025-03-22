document.addEventListener('DOMContentLoaded', () => {
  const sendButton = document.getElementById('send-button') as HTMLButtonElement;
  const userInput = document.getElementById('user-input') as HTMLInputElement;
  const chatMessages = document.getElementById('chat-messages') as HTMLElement;
  const typingIndicator = document.getElementById('typing-indicator') as HTMLElement;

  // Auto-focus the input field on load
  userInput.focus();

  // Define a type for the message sender
  type Sender = 'user' | 'bot';

  // Function to add a new message bubble to the chat window
  function addMessage(sender: Sender, text: string): void {
    const messageCard = document.createElement('div');
    messageCard.classList.add('message-card', sender);
    messageCard.textContent = text;
    chatMessages.appendChild(messageCard);
    chatMessages.scrollTo({
      top: chatMessages.scrollHeight,
      behavior: 'smooth'
    });
  }

  // Define an interface for the API response
  interface ApiResponse {
    response?: string;
    error?: string;
  }

  // Async function to send the message to the server and update the chat
  async function sendMessage(): Promise<void> {
    const message: string = userInput.value.trim();
    if (!message) return;

    addMessage('user', message);
    userInput.value = '';
    typingIndicator.style.visibility = 'visible';
    userInput.focus();

    try {
      const response = await fetch('/api/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });

      // Check if response is OK
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      addMessage('bot', data.response ?? 'Error: No response');
    } catch (error: unknown) {
      if (error instanceof Error) {
        addMessage('bot', 'Error: ' + error.message);
      } else {
        addMessage('bot', 'An unexpected error occurred.');
      }
    } finally {
      typingIndicator.style.visibility = 'hidden';
    }
  }

  // Event listeners for sending messages
  sendButton.addEventListener('click', sendMessage);
  userInput.addEventListener('keydown', (e: KeyboardEvent) => {
    if (e.key === 'Enter') sendMessage();
  });
});