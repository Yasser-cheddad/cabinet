# Guide d'installation du Chatbot avec OpenRouter et DeepSeek V2

Ce guide vous aidera à configurer le chatbot intelligent pour le Cabinet Médical, qui utilise OpenRouter pour accéder au modèle DeepSeek V2.

## Étape 1: Obtenir une clé API OpenRouter

1. Créez un compte sur [OpenRouter](https://openrouter.ai/)
2. Générez une nouvelle clé API dans les paramètres de votre compte
3. Notez cette clé pour l'étape suivante

## Étape 2: Configuration des variables d'environnement

1. Ouvrez le fichier `.env` dans le dossier `backend`
2. Ajoutez ou modifiez les variables suivantes:
   ```
   OPENROUTER_API_KEY=votre_clé_api_openrouter_ici
   SITE_DOMAIN=http://localhost:8000
   ```
   (En production, remplacez localhost par votre nom de domaine)

## Étape 3: Installation des dépendances

1. Assurez-vous d'être dans le dossier `backend`
2. Installez les nouvelles dépendances:
   ```bash
   pip install -r requirements.txt
   ```

## Étape 4: Vérification de l'installation

1. Démarrez le serveur backend:
   ```bash
   python manage.py runserver
   ```

2. Démarrez le serveur frontend:
   ```bash
   cd ../frontend
   npm run dev
   ```

3. Accédez à l'interface du chatbot via:
   - http://localhost:3000/chatbot (après connexion)

## Étape 5: Test du chatbot

1. Connectez-vous à l'application
2. Naviguez vers la page du chatbot
3. Créez une nouvelle conversation
4. Posez une question médicale simple pour tester la réponse

## Dépannage

### Problème: Le chatbot ne répond pas

Vérifiez:
- La clé API OpenRouter est correctement configurée
- Les logs du serveur backend pour les erreurs d'API
- La connexion internet est active

### Problème: Erreurs 401/403

Vérifiez:
- La validité de votre clé API OpenRouter
- Que votre compte OpenRouter est actif et dispose de crédits

### Problème: Réponses inappropriées

Vous pouvez ajuster le prompt système dans `backend/chatbot/openrouter_client.py` pour mieux guider le modèle.

## Utilisation des crédits

Notez que l'utilisation de l'API OpenRouter consomme des crédits. Surveillez votre utilisation sur le tableau de bord OpenRouter pour éviter des frais inattendus.

## Ressources supplémentaires

- [Documentation OpenRouter](https://openrouter.ai/docs)
- [Documentation DeepSeek V2](https://deepseek.ai/)
