/**
 * EESAG — menu officiel de l'espace Église locale.
 * Aucun menu national ou système ne doit être ajouté ici.
 */
export const OPTIONS_EGLISE_LOCALE = [
  { code: "eglise-dashboard", label: "Tableau de bord", path: "/eglise-dashboard", icon: "⌂", description: "Vue générale de votre église" },
  { code: "membres", label: "Membres", path: "/membres", icon: "♙", description: "Membres et profils" },
  { code: "departements", label: "Départements", path: "/departements", icon: "▦", description: "Organisation des départements" },
  { code: "annexes", label: "Annexes", path: "/annexes", icon: "⌖", description: "Implantations rattachées" },
  { code: "documents", label: "Documents", path: "/documents", icon: "▤", description: "Documents de l'église" },
  { code: "notifications", label: "Notifications", path: "/notifications", icon: "◉", description: "Messages et alertes" },
  { code: "finances", label: "Finances", path: "/finances", icon: "₣", description: "Comptabilité et projets" },
  { code: "rapports", label: "Rapports", path: "/rapports", icon: "▥", description: "Rapports de l'église" },
  { code: "reunions", label: "Réunions", path: "/reunions", icon: "◷", description: "Réunions et rencontres" },
];

export const OPTION_ADMINISTRATION_EGLISE = {
  code: "eglise-administration",
  label: "Administration de l'église",
  path: "/eglise-administration",
  icon: "⚙",
  description: "Administrateurs et permissions",
  role: "ADMIN_LOCAL",
};

export const PERMISSIONS_ADMIN_DELEGUE = [
  { code: "MEMBRES", label: "Membres", description: "Créer, modifier et gérer les membres de cette église." },
  { code: "DEPARTEMENTS", label: "Départements", description: "Créer, modifier et gérer les départements." },
  { code: "ANNEXES", label: "Annexes", description: "Créer, modifier et gérer les annexes." },
  { code: "DOCUMENTS", label: "Documents", description: "Déposer et gérer les documents autorisés." },
  { code: "NOTIFICATIONS", label: "Notifications", description: "Préparer et envoyer les notifications autorisées." },
  { code: "FINANCES", label: "Finances", description: "Gérer les opérations financières autorisées." },
  { code: "RAPPORTS", label: "Rapports", description: "Préparer et consulter les rapports." },
  { code: "REUNIONS", label: "Réunions", description: "Créer et gérer les réunions." },
  { code: "COURRIERS", label: "Courriers", description: "Gérer les courriers de l'église." },
  { code: "ASSISTANT_IA", label: "Assistant IA", description: "Accéder aux fonctions IA autorisées." },
];
