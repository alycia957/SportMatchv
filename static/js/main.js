// main.js - Fonctionnalités dynamiques pour SportMatch

document.addEventListener('DOMContentLoaded', function() {
    // Fonctions utilitaires
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Formatter toutes les dates affichées
    document.querySelectorAll('.datetime').forEach(element => {
        const dateText = element.textContent;
        if (dateText && dateText.includes('Date:')) {
            const date = dateText.split('Date:')[1].trim();
            element.innerHTML = `<strong>Date:</strong> ${formatDate(date)}`;
        }
    });

    // Validation du formulaire de création de session
    const createSessionForm = document.querySelector('.create-session-form');
    if (createSessionForm) {
        createSessionForm.addEventListener('submit', function(e) {
            const minPlayers = parseInt(document.getElementById('min_players').value);
            const maxPlayers = parseInt(document.getElementById('max_players').value);
            const datetime = document.getElementById('datetime').value;
            
            // Validation nombre de joueurs
            if (minPlayers > maxPlayers) {
                e.preventDefault();
                alert('Le nombre minimum de joueurs ne peut pas être supérieur au nombre maximum.');
                return false;
            }
            
            // Validation de la date (pas de sessions dans le passé)
            const selectedDate = new Date(datetime);
            const now = new Date();
            
            if (selectedDate < now) {
                e.preventDefault();
                alert('Vous ne pouvez pas créer une session dans le passé.');
                return false;
            }
            
            return true;
        });
    }

    // Filtres dynamiques
    const sportFilter = document.getElementById('sport_id');
    const levelFilter = document.getElementById('skill_level_id');
    
    // Mise à jour des niveaux disponibles selon le sport sélectionné
    if (sportFilter && levelFilter) {
        sportFilter.addEventListener('change', function() {
            // Cette fonction simule la récupération de niveaux adaptés au sport
            // Dans une application réelle, il faudrait faire une requête AJAX
            // pour récupérer les niveaux adaptés au sport sélectionné
            console.log('Sport sélectionné: ' + this.value);
        });
    }

    // Gestion des boutons de suppression de sport
    const deleteSportButtons = document.querySelectorAll('.delete-sport');
    if (deleteSportButtons.length > 0) {
        deleteSportButtons.forEach(button => {
            button.addEventListener('click', function() {
                const sportId = this.getAttribute('data-sport-id');
                if (confirm('Êtes-vous sûr de vouloir supprimer ce sport de votre profil ?')) {
                    fetch(`/profile/sports/${sportId}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Recharger la page pour voir les changements
                            window.location.reload();
                        } else {
                            alert('Erreur lors de la suppression du sport');
                        }
                    })
                    .catch(error => {
                        console.error('Erreur:', error);
                        alert('Une erreur s\'est produite lors de la suppression du sport');
                    });
                }
            });
        });
    }

    // Animation pour les cartes de session
    const sessionCards = document.querySelectorAll('.session-card');
    if (sessionCards.length > 0) {
        sessionCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
                this.style.boxShadow = '0 8px 15px rgba(0, 0, 0, 0.1)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.1)';
            });
        });
    }

    // Validation du formulaire de profil
    const addSportForm = document.querySelector('.add-sport form');
    if (addSportForm) {
        addSportForm.addEventListener('submit', function(e) {
            const sportId = document.getElementById('sport_id').value;
            const skillLevelId = document.getElementById('skill_level_id').value;
            
            if (!sportId || !skillLevelId) {
                e.preventDefault();
                alert('Veuillez sélectionner un sport et un niveau de compétence.');
                return false;
            }
            
            return true;
        });
    }

    // Validation du formulaire d'inscription
    const registerForm = document.querySelector('form[action*="register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            
            if (password.length < 8) {
                e.preventDefault();
                alert('Le mot de passe doit contenir au moins 8 caractères.');
                return false;
            }
            
            // Vérifier si le mot de passe contient des chiffres
            if (!/\d/.test(password)) {
                e.preventDefault();
                alert('Le mot de passe doit contenir au moins un chiffre.');
                return false;
            }
            
            return true;
        });
    }

    // Compte à rebours pour les sessions à venir
    const sessionDateElements = document.querySelectorAll('.datetime');
    if (sessionDateElements.length > 0) {
        // Fonction pour mettre à jour le compte à rebours
        function updateCountdowns() {
            sessionDateElements.forEach(element => {
                const dateText = element.textContent;
                if (dateText && dateText.includes('Date:')) {
                    const dateString = dateText.split('Date:')[1].trim();
                    const sessionDate = new Date(dateString);
                    const now = new Date();
                    
                    // Si la session est dans le futur
                    if (sessionDate > now) {
                        const timeLeft = sessionDate - now;
                        
                        // Calcul du temps restant
                        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
                        const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                        
                        // Créer l'élément de compte à rebours s'il n'existe pas
                        let countdownElement = element.nextElementSibling;
                        if (!countdownElement || !countdownElement.classList.contains('countdown')) {
                            countdownElement = document.createElement('p');
                            countdownElement.classList.add('countdown');
                            element.parentNode.insertBefore(countdownElement, element.nextSibling);
                        }
                        
                        // Mettre à jour le compte à rebours
                        countdownElement.textContent = `Commence dans: ${days}j ${hours}h ${minutes}m`;
                    }
                }
            });
        }
        
        // Mettre à jour le compte à rebours toutes les minutes
        updateCountdowns();
        setInterval(updateCountdowns, 60000);
    }

    // Notification pour les sessions avec peu de places restantes
    sessionCards.forEach(card => {
        const capacityElement = card.querySelector('.capacity');
        if (capacityElement) {
            const capacityText = capacityElement.textContent;
            const match = capacityText.match(/(\d+)\/(\d+)/);
            
            if (match) {
                const current = parseInt(match[1]);
                const max = parseInt(match[2]);
                const placesLeft = max - current;
                
                if (placesLeft <= 2 && placesLeft > 0) {
                    // Créer un badge "places limitées"
                    const badge = document.createElement('span');
                    badge.textContent = 'Plus que ' + placesLeft + ' place(s) !';
                    badge.classList.add('places-limited-badge');
                    badge.style.backgroundColor = '#e74c3c';
                    badge.style.color = 'white';
                    badge.style.padding = '3px 8px';
                    badge.style.borderRadius = '4px';
                    badge.style.fontSize = '0.8rem';
                    badge.style.fontWeight = 'bold';
                    badge.style.marginLeft = '10px';
                    
                    capacityElement.appendChild(badge);
                }
            }
        }
    });
});