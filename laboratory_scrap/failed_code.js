// Trouver le textarea et y inscrire la question
const textarea = document.querySelector("textarea[placeholder='Ask Anything']");
if (textarea) {
    textarea.value = "Keima Katsuragi";  // Inscrire la question dans le textarea
    textarea.dispatchEvent(new Event('input'));  // Déclencher un événement pour simuler la saisie
    textarea.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));  // Simuler la touche "Entrée"
} else {
    console.log("Textarea non trouvé.");
}

// Si le textarea n'est pas trouvé, on essaie avec le div contenteditable
const editableDiv = document.querySelector("#prompt-textarea[contenteditable='true']");
if (editableDiv) {
    editableDiv.innerText = "Keima Katsuragi";  // Inscrire la question dans le div contenteditable
    editableDiv.dispatchEvent(new Event('input'));  // Déclencher un événement pour simuler la saisie
    editableDiv.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));  // Simuler la touche "Entrée"
} else {
    console.log("Div contenteditable non trouvé.");
}

// Trouver le bouton pour démarrer la question et cliquer dessus
const startButton = document.querySelector("button[data-testid='composer-speech-button']");
if (startButton) {
    startButton.click();  // Cliquer sur le bouton pour démarrer la question
    console.log("Question démarrée.");
} else {
    console.log("Bouton de démarrage non trouvé.");
}
