"""Editorial seed. Unknown project facts are deliberately omitted."""
SITE = {
 'name':'AMH Agencement','phone':'01 43 62 56 55','phone_link':'+33143625655',
 'email':'contact@amh-agencement.com','workshop':'10 rue de l’Épine prolongée, 93170 Bagnolet',
 'office':'26 bis rue Planchat, 75020 Paris',
 'hero_title':'Menuiserie et agencement sur mesure à Paris',
 'hero_intro':'Des espaces pensés pour vous. Des ouvrages fabriqués dans notre atelier à Bagnolet, puis installés chez vous.',
 'hero_display_title':'Des lieux.\nÀ votre mesure.',
 'hero_image':'rivoli-salle',
 'home_intro':'Un intérieur se construit dans les détails. Une matière, une proportion, une façon de laisser entrer la lumière. Nous concevons et réalisons des agencements qui trouvent naturellement leur place dans votre quotidien.',
 'faq':[
 {'question':'Quels projets pouvez-vous nous confier ?','answer':'Menuiserie et mobilier sur mesure, rénovation d’appartements, aménagement de bureaux et commerces ou travaux en copropriété : présentez-nous votre besoin pour préciser le périmètre de notre intervention.'},
 {'question':'Où se trouve votre atelier ?','answer':'Notre atelier et notre matériauthèque se trouvent à Bagnolet. Nous disposons également d’un bureau à Paris, dans le 20e arrondissement. Contactez-nous pour organiser une visite.'},
 {'question':'Que préparer pour un premier échange ?','answer':'Quelques photos, la commune du projet et une description de vos attentes suffisent pour commencer. Vous pouvez aussi joindre un plan et indiquer votre budget ou votre échéance, si vous les connaissez.'},
 {'question':'Comment connaître le budget et les délais ?','answer':'Ils dépendent du périmètre, des matériaux et des contraintes de votre projet. Ces éléments sont précisés après étude, avant votre engagement.'}],
 'legal_publisher':'','legal_registration':'','legal_director':'','legal_host':'','privacy_retention':'',
 'social_instagram':'https://www.instagram.com/amhagencement/',
 'social_linkedin':'https://fr.linkedin.com/company/agencement-menuiserie-habillage'
}
SERVICES = [
 {'slug':'menuiserie-sur-mesure-paris','title':'Menuiserie & mobilier sur mesure','short':'Menuiserie sur mesure','number':'01','image':'bibliotheque','intro':'Des meubles dessinés pour votre espace, vos usages et les matières que vous aimez.','body':'Bibliothèque, dressing, cuisine ou habillage mural : chaque ouvrage s’inscrit dans un ensemble. Nous étudions les dimensions, les rangements et les finitions pour associer confort d’usage et cohérence visuelle.','details':['Étude des usages et des dimensions','Choix des matières et des finitions','Plans et préparation de la fabrication','Fabrication en atelier et installation'],'category':'menuiserie'},
 {'slug':'renovation-appartement-paris','title':'Rénovation d’appartements','short':'Rénovation d’appartements','number':'02','image':'rivoli','intro':'Repenser un lieu de vie, en respectant ce qui fait son caractère.','body':'De la distribution des espaces aux finitions, nous préparons avec vous le périmètre de la rénovation. Menuiserie, revêtements et équipements se répondent pour composer un intérieur cohérent.','details':['Analyse de l’existant et de vos attentes','Définition du périmètre des travaux','Coordination des interventions prévues','Installation et réception'],'category':'appartements'},
 {'slug':'renovation-bureaux-commerces-paris','title':'Bureaux & commerces','short':'Bureaux & commerces','number':'03','image':'opticien','intro':'Des espaces professionnels qui accueillent, organisent et donnent envie.','body':'Un point de vente et un bureau répondent à des usages différents. Nous travaillons les circulations, le mobilier et les matériaux en tenant compte de votre activité et des contraintes du lieu.','details':['Mobilier d’accueil et de présentation','Agencement des espaces de travail','Choix de finitions adaptées aux usages','Préparation du planning d’intervention'],'category':'professionnels'},
 {'slug':'syndic-et-copropriete','title':'Copropriétés','short':'Copropriétés','number':'04','image':'copropriete','intro':'Prendre soin des espaces que l’on partage.','body':'Halls, escaliers et parties communes méritent une attention particulière. Nous étudions les interventions avec les interlocuteurs de la copropriété et proposons des solutions adaptées à l’usage des lieux.','details':['État des lieux et définition du besoin','Menuiserie et habillages des parties communes','Matériaux et finitions adaptés','Organisation des interventions'],'category':'coproprietes'}
]
PROJECTS = [
 {'slug':'appartement-rivoli','title':'Lumière sur Rivoli','category':'appartements','location':'Paris, rue de Rivoli','image':'rivoli-salle','summary':'Une pièce de vie où les boiseries, les lignes et la lumière composent un ensemble chaleureux.','description':'Les aménagements dialoguent avec le caractère de cet intérieur. Les rangements intégrés accompagnent la pièce de vie et laissent une place à la lumière naturelle.','materials':'','brief':'','constraints':'','gallery':['rivoli-salle','rivoli','rivoli-interieur']},
 {'slug':'bibliotheque-avenue-foch','title':'Une bibliothèque, un lieu de vie','category':'menuiserie','location':'Paris, avenue Foch','image':'bibliotheque','summary':'Une bibliothèque sur mesure qui réunit rangement, livres et espace multimédia.','description':'Les étagères et les volumes de rangement dessinent les contours du salon. Livres, objets et espace multimédia trouvent leur place dans une même composition.','materials':'Chêne.','brief':'','constraints':'','gallery':['bibliotheque']},
 {'slug':'boutique-opticien','title':'Un autre regard sur la boutique','category':'professionnels','location':'Paris','image':'opticien','summary':'Présentoirs, comptoir et circulations organisent cet espace de vente.','description':'Le mobilier structure la présentation des collections et l’accueil des visiteurs. Les présentoirs muraux et le comptoir organisent les différents usages de la boutique.','materials':'','brief':'','constraints':'','gallery':['opticien']},
 {'slug':'habillage-universite','title':'Le bois comme fil conducteur','category':'menuiserie','location':'Paris, rue de l’Université','image':'universite','summary':'Un habillage mural en bois rythme l’espace et accompagne les circulations.','description':'Un habillage en chêne vertical avec éclairage intégré. Les lignes du bois soulignent les volumes et accompagnent les circulations.','materials':'Chêne.','brief':'','constraints':'','gallery':['universite']},
 {'slug':'espaces-communs','title':'Les espaces en commun','category':'coproprietes','location':'','image':'copropriete','summary':'Une attention portée aux volumes et aux finitions des parties communes.','description':'Les volumes et les finitions composent un espace commun accueillant. Une intervention pensée à l’échelle des lieux partagés.','materials':'','brief':'','constraints':'','gallery':['copropriete']}
]
ARTICLES = [
 {'slug':'preparer-projet-sur-mesure','title':'Bien préparer son projet sur mesure','image':'plans','intro':'Les bonnes informations pour un premier échange utile.','sections':[
 ['Partir des usages','Listez ce que vous souhaitez ranger, les gestes du quotidien et les points qui vous gênent aujourd’hui. Les usages aident à définir les bonnes dimensions.'],
 ['Rassembler quelques éléments','Des photographies du lieu, un plan si vous en avez un et quelques inspirations permettent de partager votre intention. Un relevé technique reste nécessaire avant fabrication.'],
 ['Préciser ses priorités','Indiquez les éléments indispensables et ceux sur lesquels vous êtes ouvert à des propositions. Budget et calendrier peuvent ensuite être étudiés en fonction du projet.']]},
 {'slug':'choisir-matieres-finitions','title':'Matières et finitions : choisir dans la durée','image':'matieres','intro':'Regarder, toucher et comparer avant de décider.','sections':[
 ['Observer à la bonne lumière','Une finition se perçoit différemment selon l’éclairage. Comparez les échantillons dans les conditions du lieu à aménager.'],
 ['Penser à l’entretien','L’usage de la pièce, l’exposition à l’humidité et la fréquence de nettoyage orientent les choix. Demandez les consignes d’entretien propres aux matériaux retenus.'],
 ['Composer un ensemble','Bois, pierre, métal et couleur doivent dialoguer. Une sélection resserrée aide à garder une continuité entre le mobilier et l’architecture.']]}
]
CATEGORIES={'menuiserie':'Menuiserie','appartements':'Appartements','professionnels':'Bureaux & commerces','coproprietes':'Copropriétés'}
STEPS=[('Échanger','Votre lieu, vos usages, vos envies. Nous commençons par comprendre ce qui compte pour vous.'),('Étudier','Dimensions, matières et contraintes : nous précisons ensemble le projet.'),('Valider','Le périmètre, les plans et les conditions sont définis avant le lancement.'),('Fabriquer','Les ouvrages prennent forme à l’atelier de Bagnolet.'),('Installer','L’installation et les ajustements donnent au projet sa place dans le lieu.'),('Réceptionner','Un dernier regard ensemble sur le travail réalisé et ses finitions.')]

PAGES=[{'slug':'atelier','title':'Là où les idées prennent forme.','intro':'Un atelier à Bagnolet, un bureau à Paris et le goût du travail bien pensé.','image':'atelier','body':'AMH Agencement accompagne les particuliers et les professionnels dans leurs projets de menuiserie, d’agencement et de rénovation.','paragraphs':['À l’atelier, le projet passe du plan à la fabrication. Les matières, les proportions et les finitions sont étudiées pour servir les usages du lieu.','Notre matériauthèque permet de comparer les essences, les couleurs et les textures. Parce qu’une matière se choisit aussi en la touchant et en l’observant à la lumière.']}]

# Adapted from the existing public article; historical URL is redirected, not lost.
MIGRATED_ARTICLE={
 'slug':'amenagement-securite-bebe-rambarde-meuble-sur-mesure',
 'title':'Un intérieur adapté à la vie de famille',
 'image':'famille',
 'intro':'Dans un duplex parisien, une rambarde et un meuble bas sur mesure accompagnent de nouveaux usages sans effacer le caractère du salon.',
 'sections':[
 ['Préserver l’esprit du lieu','Le projet publié sur le site AMH concerne un appartement du 9e arrondissement, organisé autour d’un escalier en colimaçon. La demande portait sur l’adaptation de cet escalier et la création de rangements intégrés.'],
 ['Composer avec les accès','L’appartement se trouve à un étage élevé, sans ascenseur. Le meuble a été conçu en éléments démontables, fabriqués à Bagnolet puis assemblés sur place. Les contraintes d’accès ont ainsi été intégrées dès la conception.'],
 ['Exploiter les volumes','Le meuble bas en L intègre un rangement pour poussette sous l’escalier. Des façades blanches et un plateau en chêne lient les rangements au dessin de la pièce.'],
 ['Étudier chaque situation','Les usages familiaux et les questions de sécurité nécessitent une étude spécifique. Les dimensions, fixations et exigences applicables sont à valider par les professionnels pour chaque configuration. Ce récit de projet ne remplace pas cette étude.']]
}
MIGRATED_PROJECT={
 'slug':'duplex-parisien','title':'Une place pour chaque jour','category':'menuiserie','location':'Paris 9e','image':'famille',
 'summary':'Un meuble bas en L et une rambarde accompagnent la vie de famille dans un duplex parisien.',
 'description':'Autour d’un escalier en colimaçon, le projet associe rangements bas et continuité visuelle. Les façades blanches s’accordent à l’existant, tandis que le plateau en chêne apporte une note chaleureuse.',
 'brief':'Adapter l’appartement à l’arrivée d’un enfant et créer davantage de rangements sans transformer l’esprit du salon.',
 'constraints':'Un étage élevé sans ascenseur et un accès par un escalier étroit : le meuble est conçu en éléments démontables, fabriqués à Bagnolet et assemblés sur place.',
 'materials':'Façades en MDF stratifié blanc satiné et plateau en chêne.',
 'gallery':['famille','famille-detail']
}
