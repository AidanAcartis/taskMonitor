// Sélectionner le champ <textarea> en utilisant un sélecteur échappé
const textarea = document.querySelector('textarea.block.h-10.w-full.resize-none.border-0.bg-transparent.px-0.py-2.text-token-text-primary.placeholder\\:text-token-text-tertiary');

// Vérifier si le <textarea> a été trouvé
if (textarea) {
  // Insérer un message dans le champ de texte
  textarea.value = "Monkey D. Luffy";

  // Créer un événement de modification pour simuler un changement
  const inputEvent = new Event('input', { bubbles: true });

  // Déclencher l'événement de modification
  textarea.dispatchEvent(inputEvent);

  // Vérifier si le contenu éditable est utilisé (dans ce cas, ProseMirror)
  const editableDiv = document.querySelector('#prompt-textarea');

  if (editableDiv) {
    editableDiv.textContent = "Monkey D. Luffy";
    editableDiv.dispatchEvent(inputEvent); // Déclencher l'événement également
    console.log("Message envoyé à ProseMirror !");
  }

  console.log("Message envoyé à la zone de texte !");
} else {
  console.error("Champ <textarea> non trouvé !");
}

// Attendre environ 40 secondes avant de sélectionner le bouton
setTimeout(() => {
  console.log("Attente terminée, recherche du bouton...");

  // Sélectionner le bouton "Send" par son `data-testid`
  const button = document.querySelector('button[data-testid="send-button"]');

  // Vérifier si le bouton a été trouvé et cliquer dessus
  if (button) {
    console.log("Bouton trouvé ! Clic en cours...");
    button.click();
  } else {
    console.log("Bouton non trouvé !");
  }
}, 10000); // 40 000 millisecondes = 40 secondes
