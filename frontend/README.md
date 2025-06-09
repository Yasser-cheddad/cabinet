# Cabinet Médical - Frontend

Interface utilisateur pour la gestion d'un cabinet médical, développée avec React, Vite et Tailwind CSS.

## Fonctionnalités

- **Gestion des rendez-vous**
  - Calendrier interactif avec vue jour, semaine et mois
  - Création, modification et suppression de rendez-vous
  - Gestion des statuts (planifié, confirmé, terminé, annulé, absent)
  - Filtrage et recherche des rendez-vous

- **Gestion des patients**
  - Liste des patients avec recherche
  - Fiches détaillées des patients
  - Historique des rendez-vous par patient

- **Gestion des ordonnances**
  - Création d'ordonnances liées aux rendez-vous
  - Historique des ordonnances par patient

- **Notifications**
  - Centre de notifications pour les rappels de rendez-vous
  - Alertes pour les rendez-vous à venir

- **Authentification**
  - Connexion sécurisée avec JWT
  - Gestion des rôles (médecin, secrétaire)

## Architecture technique

### Technologies utilisées

- **React 18** - Bibliothèque UI
- **Vite** - Build tool et serveur de développement
- **React Router v6** - Routage
- **Tailwind CSS** - Framework CSS utilitaire
- **FullCalendar** - Composant de calendrier
- **Axios** - Client HTTP
- **JWT Decode** - Décodage des tokens JWT

### Structure des dossiers

```
src/
├── assets/        # Images, fonts, etc.
├── components/    # Composants réutilisables
│   ├── ui/        # Composants d'interface utilisateur
├── context/       # Contextes React (Auth, etc.)
├── pages/         # Composants de page
├── services/      # Services API
└── utils/         # Fonctions utilitaires
```

## Composants principaux

### Calendrier et Rendez-vous

- `Calendar.jsx` - Affichage du calendrier avec FullCalendar
- `Appointments.jsx` - Liste des rendez-vous avec filtres
- `AppointmentDetail.jsx` - Vue détaillée d'un rendez-vous
- `AppointmentForm.jsx` - Formulaire de création/modification de rendez-vous

### Interface utilisateur

- `DashboardLayout.jsx` - Layout principal de l'application
- `Sidebar.jsx` - Barre latérale de navigation
- `Navbar.jsx` - Barre de navigation supérieure
- `NotificationCenter.jsx` - Centre de notifications

## Installation et démarrage

### Prérequis

- Node.js (v14+)
- npm ou yarn

### Installation

```bash
# Installer les dépendances
npm install
# ou
yarn
```

### Configuration

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```
VITE_API_URL=http://localhost:8000/api
```

### Démarrage en développement

```bash
npm run dev
# ou
yarn dev
```

### Build pour production

```bash
npm run build
# ou
yarn build
```

## Intégration avec le backend

Le frontend communique avec le backend Django via des API REST. Les principaux services d'API sont :

- `appointmentService` - Gestion des rendez-vous
- `patientService` - Gestion des patients
- `prescriptionService` - Gestion des ordonnances
- `authService` - Authentification et gestion des utilisateurs

## Localisation

L'application est entièrement localisée en français, y compris :

- Dates et heures au format français
- Messages et libellés en français
- Calendrier configuré avec le locale français

## Auteurs

- Équipe Cabinet Médical
