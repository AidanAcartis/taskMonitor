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
}, 10000); // 10 000 millisecondes = 10 secondes pour attendre avant de cliquer

let timeoutId; // Variable pour stocker le timeout

const observer = new MutationObserver((mutationsList) => {
    // Vérifier si une mutation a ajouté un ou plusieurs éléments
    mutationsList.forEach(mutation => {
        if (mutation.type === 'childList') {
            // Vérifier si des éléments ont été ajoutés
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1 && node.matches('.markdown.prose.w-full.break-words.dark\\:prose-invert.dark')) {
                    console.log('Nouvelle div correspondante ajoutée.');

                    // Réinitialiser le timeout précédent si un changement est détecté
                    if (timeoutId) {
                        clearTimeout(timeoutId);
                    }

                    // Attendre un délai avant d'exécuter le code
                    timeoutId = setTimeout(() => {
                        console.log('DOM stable, récupération du contenu...');

                        // Récupérer le contenu de la nouvelle div
                        const content = node.innerHTML;

                        console.log('Contenu extrait:', content);

                        // Créer un fichier local avec tout le contenu HTML
                        const blob = new Blob([content], { type: 'text/plain' }); // Créer un objet Blob
                        const url = URL.createObjectURL(blob); // Générer une URL pour le Blob

                        // Créer un lien pour télécharger le fichier
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'last_div_content.txt'; // Nom du fichier
                        a.click(); // Simuler un clic pour démarrer le téléchargement

                        console.log('Fichier téléchargé: last_div_content.txt');
                    }, 80000); // Attendre 80 secondes après le dernier changement pour vérifier la stabilité
                }
            });
        }
    });
});

// Configurer l'observateur pour surveiller les ajouts de nœuds enfants
const config = { childList: true, subtree: true };
const targetNode = document.body; // Observer tout le body de la page
observer.observe(targetNode, config);
