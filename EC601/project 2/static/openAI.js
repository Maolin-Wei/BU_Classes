// Function to send a message to OpenAI and display the response
function askOpenAI() {
    // Get the input element and its value
    const inputElement = document.getElementById('openaiInput');
    const userMessage = inputElement.value;
    const chatHistory = document.getElementById('chatHistory');

    // If the user message is empty, do nothing
    if (userMessage.trim() === '') return;

    // Append the user's message to the chat history
    chatHistory.innerHTML += `<div><strong>User:</strong> ${userMessage}</div>`;
    
    // Clear the input box
    inputElement.value = '';

    // Send a POST request to the server endpoint '/askOpenAI' with the user's message
    fetch('/askOpenAI', {
        method: 'POST',
        body: new URLSearchParams({ 'message': userMessage }),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Append OpenAI's response to the chat history after receiving it
        chatHistory.innerHTML += `<div><strong>Assistant:</strong> ${data.response}</div>`;
    })
    .catch(error => {
        // Log any errors to the console
        console.error('Error:', error);
    });
}

// Variables for the dragging functionality
var dragItem = document.querySelector("#openaiChat");
var container = document.querySelector("body");

var active = false;
var currentX;
var currentY;
var initialX;
var initialY;
var xOffset = 0;
var yOffset = 0;

// Add touch and mouse event listeners for dragging functionality
container.addEventListener("touchstart", dragStart, false);
container.addEventListener("touchend", dragEnd, false);
container.addEventListener("touchmove", drag, false);

container.addEventListener("mousedown", dragStart, false);
container.addEventListener("mouseup", dragEnd, false);
container.addEventListener("mousemove", drag, false);

function dragStart(e) {
    // Check if the event is a touch event or a mouse event and set initial positions accordingly
    if (e.type === "touchstart") {
        initialX = e.touches[0].clientX - xOffset;
        initialY = e.touches[0].clientY - yOffset;
    } else {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;
    }

    // Check if the dragged item is the target and set the 'active' flag to true
    if (e.target === dragItem) {
        active = true;
    }
}

function dragEnd(e) {
    // Update the initial positions to the current ones
    initialX = currentX;
    initialY = currentY;

    // Reset the 'active' flag
    active = false;
}

function drag(e) {
    // Check if dragging is active
    if (active) {
        // Prevent default behavior of the event
        e.preventDefault();

        // Check if the event is a touch event or a mouse event and set current positions accordingly
        if (e.type === "touchmove") {
            currentX = e.touches[0].clientX - initialX;
            currentY = e.touches[0].clientY - initialY;
        } else {
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;
        }

        xOffset = currentX;
        yOffset = currentY;

        // Translate the dragged item to the new position
        setTranslate(currentX, currentY, dragItem);
    }
}

function setTranslate(xPos, yPos, el) {
    // Set the transform style of the element to move it to the specified position
    el.style.transform = "translate3d(" + xPos + "px, " + yPos + "px, 0)";
}
