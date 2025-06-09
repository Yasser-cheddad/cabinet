# Chatbot avec OpenRouter et DeepSeek V2

Ce module fournit une intégration de chatbot intelligent pour le Cabinet Médical, en utilisant l'API OpenRouter pour accéder au modèle DeepSeek V2.

## Fonctionnalités

- Interface de chat en temps réel
- Historique des conversations
- Réponses intelligentes aux questions médicales
- Support multilingue (français)
- Intégration avec le système d'authentification

## Configuration

### Prérequis

1. Un compte OpenRouter (https://openrouter.ai/)
2. Une clé API OpenRouter

### Variables d'environnement

Ajoutez les variables suivantes dans votre fichier `.env`:

```
OPENROUTER_API_KEY=votre_clé_api_openrouter
SITE_DOMAIN=http://localhost:8000
```

## Architecture

Le chatbot est composé de:

1. **Backend (Django)**
   - `openrouter_client.py`: Client pour l'API OpenRouter
   - `views.py`: Points d'API pour gérer les conversations et messages
   - `models.py`: Modèles de données pour les conversations, messages et feedback

2. **Frontend (React)**
   - `Chatbot.jsx`: Interface utilisateur du chat
   - `chatbotService.js`: Service pour communiquer avec l'API backend

## Utilisation du modèle DeepSeek V2

Le modèle DeepSeek V2 est utilisé via OpenRouter pour:

- Répondre aux questions médicales générales
- Fournir des informations sur les rendez-vous et procédures
- Assister les patients avec des questions fréquentes

## Personnalisation

### Prompt système

Le prompt système qui guide le comportement du modèle peut être modifié dans `openrouter_client.py`:

```python
system_prompt = {
    "role": "system",
    "content": (
        "Vous êtes un assistant médical pour un cabinet de médecin..."
    )
}
```

### Paramètres du modèle

Les paramètres comme la température et le top_p peuvent être ajustés dans la méthode `generate_response` de `openrouter_client.py`.

## Maintenance

### Logging

Toutes les interactions avec l'API sont enregistrées pour le débogage et l'amélioration continue.

### Feedback utilisateur

Les utilisateurs peuvent fournir un feedback sur les réponses, ce qui permet d'améliorer les réponses prédéfinies dans la base de données.

## Sécurité

- Toutes les requêtes API nécessitent une authentification
- Les clés API sont stockées en toute sécurité dans les variables d'environnement
- Les conversations sont associées à des utilisateurs spécifiques pour la confidentialité

## Limitations

- Le modèle peut parfois générer des informations incorrectes
- Pour des conseils médicaux spécifiques, les utilisateurs sont toujours dirigés vers un professionnel de santé
- La qualité des réponses dépend de la qualité du prompt et du contexte fourni
