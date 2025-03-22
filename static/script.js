document.addEventListener('DOMContentLoaded', function() {
  const sendButton = document.getElementById('send-button');
  const userInput = document.getElementById('user-input');
  const chatMessages = document.getElementById('chat-messages');
  const typingIndicator = document.getElementById('typing-indicator');

  // Focus input field when page loads
  userInput.focus();

  // Function to add a message to the chat display area
  function addMessage(sender, text) {
    const messageCard = document.createElement('div');
    messageCard.classList.add('message-card', sender);
    messageCard.textContent = text;
    chatMessages.appendChild(messageCard);
    chatMessages.scrollTo({
      top: chatMessages.scrollHeight,
      behavior: 'smooth'
      
    });
  }

  // Function to send a message and update the chat window
  async function sendMessage() {
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
        body: JSON.stringify({ message: message })
      });
      const data = await response.json();
      addMessage('bot', data.response || 'Error: No response');
    } catch (error) {
      addMessage('bot', 'Error: ' + error.message);
    }
    typingIndicator.style.visibility = 'hidden';
  }

  sendButton.addEventListener('click', sendMessage);
  userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') sendMessage();
  });
});