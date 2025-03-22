document.addEventListener('DOMContentLoaded', () => {
  const sendButton = document.getElementById('send-button') as HTMLButtonElement;
  const userInput = document.getElementById('user-input') as HTMLInputElement;
  const chatMessages = document.getElementById('chat-messages') as HTMLElement;
  const typingIndicator = document.getElementById('typing-indicator') as HTMLElement;

  userInput.focus();

  function addMessage(sender: 'user' | 'bot', text: string): void {
    const messageCard = document.createElement('div');
    messageCard.classList.add('message-card', sender);
    messageCard.textContent = text;
    chatMessages.appendChild(messageCard);
    chatMessages.scrollTo({
      top: chatMessages.scrollHeight,
      behavior: 'smooth'
    });
  }

  async function sendMessage(): Promise<void> {
    const message = userInput.value.trim();
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

      const data = await response.json();
      addMessage('bot', data.response || 'Error: No response');
    } catch (error: any) {
      addMessage('bot', 'Error: ' + error.message);
    }

    typingIndicator.style.visibility = 'hidden';
  }

  sendButton.addEventListener('click', sendMessage);
  userInput.addEventListener('keydown', (e: KeyboardEvent) => {
    if (e.key === 'Enter') sendMessage();
  });
});
