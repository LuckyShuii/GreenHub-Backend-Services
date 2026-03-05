```md
# PR – Greener Backend Services

Cette Pull Request doit respecter les règles définies dans le **Plan Qualité Greener**.

Référence : [Plan Qualité / Normes de développement](https://www.notion.so/shiningmoonsunshine/PLAN-ASSURANCE-QUALIT-2f5be3249cb08033bc65ef4baaa8ba68)

---

# Description

Explique brièvement ce que fait cette PR :

- fonctionnalité / correction
- services backend impactés

---

# Rappels importants

## Format de branche

Les branches doivent respecter la convention suivante :
```

feature/[TRIGRAM]-[ID_TICKET]-[description]
fix/[TRIGRAM]-[ID_TICKET]-[description]
refactor/[TRIGRAM]-[ID_TICKET]-[description]

```

Exemple :

```

feature/LBT-12-scan-image-ai

```

---

## Format des commits (Conventional Commits)

Format :

```

<type>(scope): description

```

Types autorisés :

- `feat` → nouvelle fonctionnalité
- `fix` → correction de bug
- `docs` → documentation
- `style` → formatage du code
- `refactor` → refactoring sans changement fonctionnel
- `test` → ajout ou modification de tests
- `release` → préparation d'une release

---

## Normes backend (Python)

Le code backend doit respecter **PEP8**.

Principales règles :

- indentation : **4 espaces**
- longueur de ligne : **79 caractères maximum**
- noms de fichiers : `snake_case.py`
- classes : `PascalCase`
- fonctions / variables : `snake_case`

Exemples :

```

user_router.py
waste_model.py
ai_processing_service.py

```

---

# Checklist avant merge

Avant de demander une review :

- [ ] Le code respecte les normes du projet
- [ ] Le linter passe sans erreur
- [ ] La CI est verte
- [ ] Les tests nécessaires ont été ajoutés
- [ ] Le code a été testé localement
```
