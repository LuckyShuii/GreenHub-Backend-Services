-- Chargement initial uniquement : 20 questions pour Paris et 60 reponses.
-- Execute par Docker apres 01-postgis.sql lorsque le volume est vide.
-- Ne pas rejouer sur une base deja alimentee : les UUID sont fixes.
-- Textes et baremes du document fourni, sans validation metier.

-- Q1. Dans quel bac jeter un emballage plastique alimentaire (pot de yaourt, barquette) propre ?
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000001',
    'Dans quel bac jeter un emballage plastique alimentaire (pot de yaourt, barquette) propre ?',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000011',
        '47524851-0000-4000-8000-000000000001',
        '**Bac jaune**',
        true,
        10,
        'Tous les emballages vont dans le bac jaune — Règle nationale. Depuis 2023 (loi AGEC), 100 % des emballages sont acceptés dans le bac jaune : plastiques, cartons, métaux, briques alimentaires, films plastiques. Plus aucune exclusion sur la forme ou la matière.'
    ),
    (
        '47524841-0000-4000-8000-000000000012',
        '47524851-0000-4000-8000-000000000001',
        '**Poubelle noire**',
        false,
        0,
        'Tous les emballages vont dans le bac jaune — Règle nationale. Depuis 2023 (loi AGEC), 100 % des emballages sont acceptés dans le bac jaune : plastiques, cartons, métaux, briques alimentaires, films plastiques. Plus aucune exclusion sur la forme ou la matière.'
    ),
    (
        '47524841-0000-4000-8000-000000000013',
        '47524851-0000-4000-8000-000000000001',
        '**Colonne à verre**',
        false,
        0,
        'Tous les emballages vont dans le bac jaune — Règle nationale. Depuis 2023 (loi AGEC), 100 % des emballages sont acceptés dans le bac jaune : plastiques, cartons, métaux, briques alimentaires, films plastiques. Plus aucune exclusion sur la forme ou la matière.'
    );

-- Q2. Un carton de pizza taché de gras, je le mets dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000002',
    'Un carton de pizza taché de gras, je le mets dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000021',
        '47524851-0000-4000-8000-000000000002',
        '**Bac jaune**, comme tout carton',
        false,
        0,
        'Carton pizza souillé → poubelle noire — Erreur fréquente. Le carton imprégné de gras n''''est pas recyclable. Si seule la moitié est souillée, déchirer le carton : la partie propre dans le jaune, la partie grasse dans le noir.'
    ),
    (
        '47524841-0000-4000-8000-000000000022',
        '47524851-0000-4000-8000-000000000002',
        '**Poubelle noire**',
        true,
        10,
        'Carton pizza souillé → poubelle noire — Erreur fréquente. Le carton imprégné de gras n''''est pas recyclable. Si seule la moitié est souillée, déchirer le carton : la partie propre dans le jaune, la partie grasse dans le noir.'
    ),
    (
        '47524841-0000-4000-8000-000000000023',
        '47524851-0000-4000-8000-000000000002',
        '**Compost**',
        false,
        0,
        'Carton pizza souillé → poubelle noire — Erreur fréquente. Le carton imprégné de gras n''''est pas recyclable. Si seule la moitié est souillée, déchirer le carton : la partie propre dans le jaune, la partie grasse dans le noir.'
    );

-- Q3. À Paris, où jeter un journal ou un prospectus publicitaire ?
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000003',
    'À Paris, où jeter un journal ou un prospectus publicitaire ?',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000031',
        '47524851-0000-4000-8000-000000000003',
        'Dans un **bac bleu** séparé pour le papier',
        false,
        0,
        'Les papiers vont aussi dans le bac jaune en IdF — Spécifique IdF. À Paris et dans la petite couronne (Syctom), journaux, magazines, courriers et papiers bureau sont collectés dans le même bac jaune que les emballages. Pas de bac bleu séparé dans la majorité des communes franciliennes.'
    ),
    (
        '47524841-0000-4000-8000-000000000032',
        '47524851-0000-4000-8000-000000000003',
        'Dans le même **bac jaune** que les emballages',
        true,
        10,
        'Les papiers vont aussi dans le bac jaune en IdF — Spécifique IdF. À Paris et dans la petite couronne (Syctom), journaux, magazines, courriers et papiers bureau sont collectés dans le même bac jaune que les emballages. Pas de bac bleu séparé dans la majorité des communes franciliennes.'
    ),
    (
        '47524841-0000-4000-8000-000000000033',
        '47524851-0000-4000-8000-000000000003',
        'À la **déchetterie**',
        false,
        0,
        'Les papiers vont aussi dans le bac jaune en IdF — Spécifique IdF. À Paris et dans la petite couronne (Syctom), journaux, magazines, courriers et papiers bureau sont collectés dans le même bac jaune que les emballages. Pas de bac bleu séparé dans la majorité des communes franciliennes.'
    );

-- Q4. Une bombe de déodorant complètement vide va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000004',
    'Une bombe de déodorant complètement vide va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000041',
        '47524851-0000-4000-8000-000000000004',
        '**La déchetterie**, car c''est dangereux',
        false,
        0,
        'Aérosols vides → bac jaune — Règle nationale. Un aérosol complètement vide (déodorant, laque) va dans le bac jaune. Ne pas percer ni écraser. Si encore sous pression : déchetterie uniquement.'
    ),
    (
        '47524841-0000-4000-8000-000000000042',
        '47524851-0000-4000-8000-000000000004',
        '**Le bac jaune**',
        true,
        10,
        'Aérosols vides → bac jaune — Règle nationale. Un aérosol complètement vide (déodorant, laque) va dans le bac jaune. Ne pas percer ni écraser. Si encore sous pression : déchetterie uniquement.'
    ),
    (
        '47524841-0000-4000-8000-000000000043',
        '47524851-0000-4000-8000-000000000004',
        '**La poubelle noire**',
        false,
        0,
        'Aérosols vides → bac jaune — Règle nationale. Un aérosol complètement vide (déodorant, laque) va dans le bac jaune. Ne pas percer ni écraser. Si encore sous pression : déchetterie uniquement.'
    );

-- Q5. J'ai un carton trop grand pour rentrer dans mon bac jaune fermé, même aplati. Je dois...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000005',
    'J''ai un carton trop grand pour rentrer dans mon bac jaune fermé, même aplati. Je dois...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000051',
        '47524851-0000-4000-8000-000000000005',
        'Le laisser **à côté du bac**',
        false,
        0,
        'Aplatir les cartons avant dépôt — Spécifique IdF. Les cartons doivent être aplatis pour économiser le volume du bac. Les cartons très volumineux (déménagement) vont en déchetterie ou Trimobile Paris.'
    ),
    (
        '47524841-0000-4000-8000-000000000052',
        '47524851-0000-4000-8000-000000000005',
        'L''apporter **en déchetterie** ou via **Trimobile Paris**',
        true,
        10,
        'Aplatir les cartons avant dépôt — Spécifique IdF. Les cartons doivent être aplatis pour économiser le volume du bac. Les cartons très volumineux (déménagement) vont en déchetterie ou Trimobile Paris.'
    ),
    (
        '47524841-0000-4000-8000-000000000053',
        '47524851-0000-4000-8000-000000000005',
        'Le **découper en confettis** et le jeter en plusieurs fois',
        false,
        0,
        'Aplatir les cartons avant dépôt — Spécifique IdF. Les cartons doivent être aplatis pour économiser le volume du bac. Les cartons très volumineux (déménagement) vont en déchetterie ou Trimobile Paris.'
    );

-- Q6. Une bouteille de vin vide va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000006',
    'Une bouteille de vin vide va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000061',
        '47524851-0000-4000-8000-000000000006',
        '**Le bac jaune**',
        false,
        0,
        'Le verre ne va jamais dans le bac jaune — Spécifique Paris. À Paris, le verre a son propre circuit : bac à couvercle blanc en immeuble, ou colonnes à verre sur la voie publique (accessibles 24h/24). Le mélanger au jaune contamine tout le flux.'
    ),
    (
        '47524841-0000-4000-8000-000000000062',
        '47524851-0000-4000-8000-000000000006',
        '**La colonne à verre** ou **le bac blanc** (Paris)',
        true,
        10,
        'Le verre ne va jamais dans le bac jaune — Spécifique Paris. À Paris, le verre a son propre circuit : bac à couvercle blanc en immeuble, ou colonnes à verre sur la voie publique (accessibles 24h/24). Le mélanger au jaune contamine tout le flux.'
    ),
    (
        '47524841-0000-4000-8000-000000000063',
        '47524851-0000-4000-8000-000000000006',
        '**La poubelle noire**',
        false,
        0,
        'Le verre ne va jamais dans le bac jaune — Spécifique Paris. À Paris, le verre a son propre circuit : bac à couvercle blanc en immeuble, ou colonnes à verre sur la voie publique (accessibles 24h/24). Le mélanger au jaune contamine tout le flux.'
    );

-- Q7. Un plat à gratin en Pyrex cassé va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000007',
    'Un plat à gratin en Pyrex cassé va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000071',
        '47524851-0000-4000-8000-000000000007',
        '**La colonne à verre**, comme tout le verre',
        false,
        0,
        'Pyrex, porcelaine, miroirs → pas dans le verre — Règle nationale. Ces matériaux fondent à une température différente du verre d''emballage et créent des défauts dans le verre recyclé. Déchetterie uniquement. Seuls les emballages en verre (bouteilles, bocaux, flacons) sont acceptés dans les colonnes.'
    ),
    (
        '47524841-0000-4000-8000-000000000072',
        '47524851-0000-4000-8000-000000000007',
        '**La déchetterie**',
        true,
        10,
        'Pyrex, porcelaine, miroirs → pas dans le verre — Règle nationale. Ces matériaux fondent à une température différente du verre d''emballage et créent des défauts dans le verre recyclé. Déchetterie uniquement. Seuls les emballages en verre (bouteilles, bocaux, flacons) sont acceptés dans les colonnes.'
    ),
    (
        '47524841-0000-4000-8000-000000000073',
        '47524851-0000-4000-8000-000000000007',
        '**Le bac jaune**',
        false,
        0,
        'Pyrex, porcelaine, miroirs → pas dans le verre — Règle nationale. Ces matériaux fondent à une température différente du verre d''emballage et créent des défauts dans le verre recyclé. Déchetterie uniquement. Seuls les emballages en verre (bouteilles, bocaux, flacons) sont acceptés dans les colonnes.'
    );

-- Q8. Un verre à boire cassé chez moi, je dois...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000008',
    'Un verre à boire cassé chez moi, je dois...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000081',
        '47524851-0000-4000-8000-000000000008',
        'Le jeter directement dans **la colonne à verre**',
        false,
        0,
        'Le verre d’emballage (bouteilles, pots et bocaux) peut être recyclé à l’infini sans perte de qualité mais les verres culinaire (assiettes, verres à pied, flûtes, verrines…) et d’autres objets en verre, comme les ampoules ou les miroirs, contiennent des additifs chimiques pour les rendre plus solides ou brillants. Ces substances modifient leur point de fusion et créent des imperfections dans le verre recyclé. Les capsules et couvercles métalliques vont dans le bac jaune, pas dans la colonne à verre.

Bouchons et couvercles métalliques → bac jaune / verre cassé → poubelle noire — Spécifique Paris. . Le verre cassé (verres à boire) va dans la poubelle noire emballé dans du papier journal, pour la sécurité des agents.'
    ),
    (
        '47524841-0000-4000-8000-000000000082',
        '47524851-0000-4000-8000-000000000008',
        'L''emballer dans du papier journal puis le mettre en **poubelle noire**',
        true,
        10,
        'Le verre d’emballage (bouteilles, pots et bocaux) peut être recyclé à l’infini sans perte de qualité mais les verres culinaire (assiettes, verres à pied, flûtes, verrines…) et d’autres objets en verre, comme les ampoules ou les miroirs, contiennent des additifs chimiques pour les rendre plus solides ou brillants. Ces substances modifient leur point de fusion et créent des imperfections dans le verre recyclé. Les capsules et couvercles métalliques vont dans le bac jaune, pas dans la colonne à verre.

Bouchons et couvercles métalliques → bac jaune / verre cassé → poubelle noire — Spécifique Paris. . Le verre cassé (verres à boire) va dans la poubelle noire emballé dans du papier journal, pour la sécurité des agents.'
    ),
    (
        '47524841-0000-4000-8000-000000000083',
        '47524851-0000-4000-8000-000000000008',
        'Le mettre dans **le bac jaune** avec les autres déchets cassants',
        false,
        0,
        'Le verre d’emballage (bouteilles, pots et bocaux) peut être recyclé à l’infini sans perte de qualité mais les verres culinaire (assiettes, verres à pied, flûtes, verrines…) et d’autres objets en verre, comme les ampoules ou les miroirs, contiennent des additifs chimiques pour les rendre plus solides ou brillants. Ces substances modifient leur point de fusion et créent des imperfections dans le verre recyclé. Les capsules et couvercles métalliques vont dans le bac jaune, pas dans la colonne à verre.

Bouchons et couvercles métalliques → bac jaune / verre cassé → poubelle noire — Spécifique Paris. . Le verre cassé (verres à boire) va dans la poubelle noire emballé dans du papier journal, pour la sécurité des agents.'
    );

-- Q9. Des épluchures de légumes et du marc de café se jettent dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000009',
    'Des épluchures de légumes et du marc de café se jettent dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000091',
        '47524851-0000-4000-8000-000000000009',
        '**Le bac jaune**',
        false,
        0,
        'Tri des biodéchets obligatoire depuis jan. 2024 — Spécifique Paris. La loi AGEC impose le tri à la source pour tous. À Paris : ~600 points d''apport volontaire (bornes + Trilib''). Les biodéchets ne vont ni dans le jaune ni dans le noir — ils vont dans les bornes dédiées ou un composteur.'
    ),
    (
        '47524841-0000-4000-8000-000000000092',
        '47524851-0000-4000-8000-000000000009',
        'Une **borne biodéchets**, un **Trilib''** ou un **composteur**',
        true,
        10,
        'Tri des biodéchets obligatoire depuis jan. 2024 — Spécifique Paris. La loi AGEC impose le tri à la source pour tous. À Paris : ~600 points d''apport volontaire (bornes + Trilib''). Les biodéchets ne vont ni dans le jaune ni dans le noir — ils vont dans les bornes dédiées ou un composteur.'
    ),
    (
        '47524841-0000-4000-8000-000000000093',
        '47524851-0000-4000-8000-000000000009',
        '**La poubelle noire**',
        false,
        0,
        'Tri des biodéchets obligatoire depuis jan. 2024 — Spécifique Paris. La loi AGEC impose le tri à la source pour tous. À Paris : ~600 points d''apport volontaire (bornes + Trilib''). Les biodéchets ne vont ni dans le jaune ni dans le noir — ils vont dans les bornes dédiées ou un composteur.'
    );

-- Q10. Des os de poulet après le repas vont dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000010',
    'Des os de poulet après le repas vont dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000101',
        '47524851-0000-4000-8000-000000000010',
        '**La borne biodéchets**, comme tout reste alimentaire',
        false,
        0,
        'Ce qui est compostable — Règle nationale. Épluchures, marc de café avec filtre papier, coquilles d''œuf, sachet de thé, fleurs fanées, restes de repas, pain rassis sont compostables. Les os et noyaux très durs sont à mettre dans la poubelle noire.'
    ),
    (
        '47524841-0000-4000-8000-000000000102',
        '47524851-0000-4000-8000-000000000010',
        '**La poubelle noire**',
        true,
        10,
        'Ce qui est compostable — Règle nationale. Épluchures, marc de café avec filtre papier, coquilles d''œuf, sachet de thé, fleurs fanées, restes de repas, pain rassis sont compostables. Les os et noyaux très durs sont à mettre dans la poubelle noire.'
    ),
    (
        '47524841-0000-4000-8000-000000000103',
        '47524851-0000-4000-8000-000000000010',
        '**Le compost à la maison** uniquement',
        false,
        0,
        'Ce qui est compostable — Règle nationale. Épluchures, marc de café avec filtre papier, coquilles d''œuf, sachet de thé, fleurs fanées, restes de repas, pain rassis sont compostables. Les os et noyaux très durs sont à mettre dans la poubelle noire.'
    );

-- Q11. Dans quel bac jeter des piles usagées ?
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000011',
    'Dans quel bac jeter des piles usagées ?',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000111',
        '47524851-0000-4000-8000-000000000011',
        '**Bac jaune**',
        false,
        0,
        'Piles et petits appareils électroniques → point de collecte — Règle nationale. Jamais dans aucune poubelle. Les piles se déposent dans les bacs présents en supermarchés, pharmacies ou Trilib''. Pour les DEEE (téléphone, chargeur...) : déchetterie ou reprise en magasin (obligation légale depuis 2022).'
    ),
    (
        '47524841-0000-4000-8000-000000000112',
        '47524851-0000-4000-8000-000000000011',
        '**Poubelle noire**',
        false,
        0,
        'Piles et petits appareils électroniques → point de collecte — Règle nationale. Jamais dans aucune poubelle. Les piles se déposent dans les bacs présents en supermarchés, pharmacies ou Trilib''. Pour les DEEE (téléphone, chargeur...) : déchetterie ou reprise en magasin (obligation légale depuis 2022).'
    ),
    (
        '47524841-0000-4000-8000-000000000113',
        '47524851-0000-4000-8000-000000000011',
        '**Point de collecte dédié** (supermarché, pharmacie, Trilib'')',
        true,
        15,
        'Piles et petits appareils électroniques → point de collecte — Règle nationale. Jamais dans aucune poubelle. Les piles se déposent dans les bacs présents en supermarchés, pharmacies ou Trilib''. Pour les DEEE (téléphone, chargeur...) : déchetterie ou reprise en magasin (obligation légale depuis 2022).'
    );

-- Q12. Des médicaments périmés se rapportent...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000012',
    'Des médicaments périmés se rapportent...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000121',
        '47524851-0000-4000-8000-000000000012',
        'À **la poubelle noire**, dans un sac fermé',
        false,
        0,
        'Médicaments → pharmacie uniquement — Règle nationale. Les médicaments (comprimés, sirops, tubes) se rapportent en pharmacie, même périmés. Jamais dans les poubelles ni dans les toilettes. Réseau Cyclamed en Île-de-France.'
    ),
    (
        '47524841-0000-4000-8000-000000000122',
        '47524851-0000-4000-8000-000000000012',
        'En **pharmacie**',
        true,
        10,
        'Médicaments → pharmacie uniquement — Règle nationale. Les médicaments (comprimés, sirops, tubes) se rapportent en pharmacie, même périmés. Jamais dans les poubelles ni dans les toilettes. Réseau Cyclamed en Île-de-France.'
    ),
    (
        '47524841-0000-4000-8000-000000000123',
        '47524851-0000-4000-8000-000000000012',
        'Dans **les toilettes** pour les formes liquides',
        false,
        0,
        'Médicaments → pharmacie uniquement — Règle nationale. Les médicaments (comprimés, sirops, tubes) se rapportent en pharmacie, même périmés. Jamais dans les poubelles ni dans les toilettes. Réseau Cyclamed en Île-de-France.'
    );

-- Q13. Un t-shirt troué et un vieux jean partent dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000013',
    'Un t-shirt troué et un vieux jean partent dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000131',
        '47524851-0000-4000-8000-000000000013',
        '**La poubelle noire**, ils sont trop abîmés',
        false,
        0,
        'Textiles → conteneurs dédiés — Règle nationale. Vêtements, linge de lit, chaussures appariées : conteneurs spécifiques sur la voie publique (Le Relais, Refashion...) — même usés ou troués, propres et secs. Depuis jan. 2025, tri textile obligatoire en entreprise.'
    ),
    (
        '47524841-0000-4000-8000-000000000132',
        '47524851-0000-4000-8000-000000000013',
        'Un **conteneur textile** dédié sur la voie publique',
        true,
        10,
        'Textiles → conteneurs dédiés — Règle nationale. Vêtements, linge de lit, chaussures appariées : conteneurs spécifiques sur la voie publique (Le Relais, Refashion...) — même usés ou troués, propres et secs. Depuis jan. 2025, tri textile obligatoire en entreprise.'
    ),
    (
        '47524841-0000-4000-8000-000000000133',
        '47524851-0000-4000-8000-000000000013',
        '**Le bac jaune** avec les autres matières recyclables',
        false,
        0,
        'Textiles → conteneurs dédiés — Règle nationale. Vêtements, linge de lit, chaussures appariées : conteneurs spécifiques sur la voie publique (Le Relais, Refashion...) — même usés ou troués, propres et secs. Depuis jan. 2025, tri textile obligatoire en entreprise.'
    );

-- Q14. De l'huile de friture usagée se jette...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000014',
    'De l''huile de friture usagée se jette...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000141',
        '47524851-0000-4000-8000-000000000014',
        'Dans **l''évier**, en petite quantité',
        false,
        0,
        'Huiles usagées → filière spécifique — Spécifique IdF. Huile de vidange : déchetterie. Huile de friture usagée : bornes dédiées (certains Trilib'' parisiens) ou déchetterie. Un litre d''huile peut polluer 1 million de litres d''eau.'
    ),
    (
        '47524841-0000-4000-8000-000000000142',
        '47524851-0000-4000-8000-000000000014',
        'Dans une **borne dédiée (Trilib'')** ou en **déchetterie**',
        true,
        15,
        'Huiles usagées → filière spécifique — Spécifique IdF. Huile de vidange : déchetterie. Huile de friture usagée : bornes dédiées (certains Trilib'' parisiens) ou déchetterie. Un litre d''huile peut polluer 1 million de litres d''eau.'
    ),
    (
        '47524841-0000-4000-8000-000000000143',
        '47524851-0000-4000-8000-000000000014',
        'Dans **le bac jaune**, dans une bouteille fermée',
        false,
        0,
        'Huiles usagées → filière spécifique — Spécifique IdF. Huile de vidange : déchetterie. Huile de friture usagée : bornes dédiées (certains Trilib'' parisiens) ou déchetterie. Un litre d''huile peut polluer 1 million de litres d''eau.'
    );

-- Q15. Une seringue usagée (traitement à domicile) se jette...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000015',
    'Une seringue usagée (traitement à domicile) se jette...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000151',
        '47524851-0000-4000-8000-000000000015',
        'Dans **la poubelle noire**, bien refermée',
        false,
        0,
        'Seringues et DASRI → pharmacie ou déchetterie — Spécifique IdF. Les déchets piquants/coupants médicaux (DASRI) ont une filière dédiée. En Île-de-France, les pharmacies assurent la reprise gratuite. Jamais dans une poubelle standard.'
    ),
    (
        '47524841-0000-4000-8000-000000000152',
        '47524851-0000-4000-8000-000000000015',
        'En **pharmacie** ou en **déchetterie**',
        true,
        15,
        'Seringues et DASRI → pharmacie ou déchetterie — Spécifique IdF. Les déchets piquants/coupants médicaux (DASRI) ont une filière dédiée. En Île-de-France, les pharmacies assurent la reprise gratuite. Jamais dans une poubelle standard.'
    ),
    (
        '47524841-0000-4000-8000-000000000153',
        '47524851-0000-4000-8000-000000000015',
        'Dans **le bac jaune** avec les autres déchets médicaux',
        false,
        0,
        'Seringues et DASRI → pharmacie ou déchetterie — Spécifique IdF. Les déchets piquants/coupants médicaux (DASRI) ont une filière dédiée. En Île-de-France, les pharmacies assurent la reprise gratuite. Jamais dans une poubelle standard.'
    );

-- Q16. Un ticket de caisse va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000016',
    'Un ticket de caisse va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000161',
        '47524851-0000-4000-8000-000000000016',
        '**Le bac jaune**, comme tout papier',
        false,
        0,
        'Tickets de caisse → poubelle noire — Erreur fréquente. Le papier thermique (tickets de caisse, reçus CB) contient du bisphénol A. Il n''est pas recyclable et contamine le bac jaune. Règle simple : papier brillant ou ciré = poubelle noire.'
    ),
    (
        '47524841-0000-4000-8000-000000000162',
        '47524851-0000-4000-8000-000000000016',
        '**La poubelle noire**',
        true,
        15,
        'Tickets de caisse → poubelle noire — Erreur fréquente. Le papier thermique (tickets de caisse, reçus CB) contient du bisphénol A. Il n''est pas recyclable et contamine le bac jaune. Règle simple : papier brillant ou ciré = poubelle noire.'
    ),
    (
        '47524841-0000-4000-8000-000000000163',
        '47524851-0000-4000-8000-000000000016',
        '**La déchetterie**',
        false,
        0,
        'Tickets de caisse → poubelle noire — Erreur fréquente. Le papier thermique (tickets de caisse, reçus CB) contient du bisphénol A. Il n''est pas recyclable et contamine le bac jaune. Règle simple : papier brillant ou ciré = poubelle noire.'
    );

-- Q17. Du papier cadeau brillant et pailleté va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000017',
    'Du papier cadeau brillant et pailleté va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000171',
        '47524851-0000-4000-8000-000000000017',
        '**Le bac jaune**',
        false,
        0,
        'Papier cadeau pailleté → poubelle noire — Erreur fréquente. Le papier cadeau brillant/pailleté ou avec film plastique n''est pas recyclable. Test de froissage : si ça reste froissé, c''est recyclable (papier mat). Sinon, poubelle noire.'
    ),
    (
        '47524841-0000-4000-8000-000000000172',
        '47524851-0000-4000-8000-000000000017',
        '**La poubelle noire**',
        true,
        15,
        'Papier cadeau pailleté → poubelle noire — Erreur fréquente. Le papier cadeau brillant/pailleté ou avec film plastique n''est pas recyclable. Test de froissage : si ça reste froissé, c''est recyclable (papier mat). Sinon, poubelle noire.'
    ),
    (
        '47524841-0000-4000-8000-000000000173',
        '47524851-0000-4000-8000-000000000017',
        '**Le compost**',
        false,
        0,
        'Papier cadeau pailleté → poubelle noire — Erreur fréquente. Le papier cadeau brillant/pailleté ou avec film plastique n''est pas recyclable. Test de froissage : si ça reste froissé, c''est recyclable (papier mat). Sinon, poubelle noire.'
    );

-- Q18. Une enveloppe avec une fenêtre plastique transparente va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000018',
    'Une enveloppe avec une fenêtre plastique transparente va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000181',
        '47524851-0000-4000-8000-000000000018',
        '**Le bac jaune**, comme une enveloppe normale',
        true,
        15,
        'Enveloppes à fenêtre plastique → bac jaune quand même — Spécifique IdF. Contrairement à une idée reçue, les enveloppes à fenêtre plastique peuvent aller dans le bac jaune en IdF. Les centres de tri du Syctom sont équipés pour les traiter.'
    ),
    (
        '47524841-0000-4000-8000-000000000182',
        '47524851-0000-4000-8000-000000000018',
        '**La poubelle noire**, à cause du plastique',
        false,
        0,
        'Enveloppes à fenêtre plastique → bac jaune quand même — Spécifique IdF. Contrairement à une idée reçue, les enveloppes à fenêtre plastique peuvent aller dans le bac jaune en IdF. Les centres de tri du Syctom sont équipés pour les traiter.'
    ),
    (
        '47524841-0000-4000-8000-000000000183',
        '47524851-0000-4000-8000-000000000018',
        'Il faut **retirer la fenêtre** avant de jeter',
        false,
        0,
        'Enveloppes à fenêtre plastique → bac jaune quand même — Spécifique IdF. Contrairement à une idée reçue, les enveloppes à fenêtre plastique peuvent aller dans le bac jaune en IdF. Les centres de tri du Syctom sont équipés pour les traiter.'
    );

-- Q19. Une capsule de café en aluminium (type Nespresso) va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000019',
    'Une capsule de café en aluminium (type Nespresso) va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000191',
        '47524851-0000-4000-8000-000000000019',
        '**Le bac jaune**, c''est du métal',
        false,
        0,
        'Capsules de café → collecte spécifique — Erreur fréquente. Les capsules Nespresso (aluminium) ont leur propre filière : bornes de collecte en boutique Nespresso. Les capsules plastique (Dolce Gusto, Tassimo) → poubelle noire. Jamais dans le bac jaune standard.'
    ),
    (
        '47524841-0000-4000-8000-000000000192',
        '47524851-0000-4000-8000-000000000019',
        'Une **filière de collecte dédiée** (boutique ou point de collecte spécifique)',
        true,
        15,
        'Capsules de café → collecte spécifique — Erreur fréquente. Les capsules Nespresso (aluminium) ont leur propre filière : bornes de collecte en boutique Nespresso. Les capsules plastique (Dolce Gusto, Tassimo) → poubelle noire. Jamais dans le bac jaune standard.'
    ),
    (
        '47524841-0000-4000-8000-000000000193',
        '47524851-0000-4000-8000-000000000019',
        '**La poubelle noire**',
        false,
        0,
        'Capsules de café → collecte spécifique — Erreur fréquente. Les capsules Nespresso (aluminium) ont leur propre filière : bornes de collecte en boutique Nespresso. Les capsules plastique (Dolce Gusto, Tassimo) → poubelle noire. Jamais dans le bac jaune standard.'
    );

-- Q20. Un essuie-tout utilisé pour essuyer une table va dans...
INSERT INTO questions (id, question, departments)
VALUES (
    '47524851-0000-4000-8000-000000000020',
    'Un essuie-tout utilisé pour essuyer une table va dans...',
    '[75]'::jsonb
);

INSERT INTO answers (id, question_id, body, is_correct, points, comment)
VALUES
    (
        '47524841-0000-4000-8000-000000000201',
        '47524851-0000-4000-8000-000000000020',
        '**Le bac jaune** avec les papiers',
        false,
        0,
        'Essuie-tout, mouchoirs, couches → poubelle noire — Règle nationale. Ces matériaux sont en papier mais non recyclables car souillés ou composites. Exception : essuie-tout propre et sec peut aller au compost.'
    ),
    (
        '47524841-0000-4000-8000-000000000202',
        '47524851-0000-4000-8000-000000000020',
        '**La poubelle noire**',
        true,
        10,
        'Essuie-tout, mouchoirs, couches → poubelle noire — Règle nationale. Ces matériaux sont en papier mais non recyclables car souillés ou composites. Exception : essuie-tout propre et sec peut aller au compost.'
    ),
    (
        '47524841-0000-4000-8000-000000000203',
        '47524851-0000-4000-8000-000000000020',
        '**Le compost**, comme tout papier',
        false,
        0,
        'Essuie-tout, mouchoirs, couches → poubelle noire — Règle nationale. Ces matériaux sont en papier mais non recyclables car souillés ou composites. Exception : essuie-tout propre et sec peut aller au compost.'
    );
