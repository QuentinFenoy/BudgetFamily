/// Fiche pédagogique d'une classe d'actifs (GET /v1/portfolio/asset-classes).
class AssetClassInfo {
  AssetClassInfo({
    required this.cle,
    required this.nom,
    required this.categorie,
    required this.definition,
    required this.exemples,
  });

  final String cle;
  final String nom;
  final String categorie;
  final String definition;
  final List<String> exemples;

  factory AssetClassInfo.fromJson(Map<String, dynamic> json) {
    return AssetClassInfo(
      cle: json['cle'] as String,
      nom: json['nom'] as String,
      categorie: json['categorie'] as String,
      definition: json['definition'] as String,
      exemples: (json['exemples'] as List<dynamic>).map((e) => e as String).toList(),
    );
  }
}
