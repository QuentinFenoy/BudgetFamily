/// Modèles de GET /v1/portfolio/allocation. Le backend ne renvoie que des classes
/// d'actifs génériques (jamais d'instrument nominatif) ; les montants par ligne ne
/// sont présents que si un capital total a été fourni.

class AllocationLine {
  AllocationLine({
    required this.classe,
    required this.categorie,
    required this.part,
    this.montant,
  });

  final String classe;
  final String categorie; // "Croissance" | "Défensif"
  final double part; // 0..1
  final double? montant;

  factory AllocationLine.fromJson(Map<String, dynamic> json) {
    return AllocationLine(
      classe: json['classe'] as String,
      categorie: json['categorie'] as String,
      part: (json['part'] as num).toDouble(),
      montant: json['montant'] == null ? null : (json['montant'] as num).toDouble(),
    );
  }
}

class PortfolioAllocation {
  PortfolioAllocation({
    required this.methode,
    required this.partCroissance,
    required this.partDefensive,
    required this.lignes,
    required this.rendementAnnuelEspere,
    required this.volatiliteAnnuelleEstimee,
    required this.ratioSharpeEstime,
    required this.hypotheses,
    required this.avertissement,
    this.profilRisque,
  });

  final int? profilRisque;
  final String methode;
  final double partCroissance;
  final double partDefensive;
  final List<AllocationLine> lignes;
  final double rendementAnnuelEspere;
  final double volatiliteAnnuelleEstimee;
  final double ratioSharpeEstime;
  final String hypotheses;
  final String avertissement;

  factory PortfolioAllocation.fromJson(Map<String, dynamic> json) {
    return PortfolioAllocation(
      profilRisque: json['profil_risque'] as int?,
      methode: json['methode'] as String,
      partCroissance: (json['part_croissance'] as num).toDouble(),
      partDefensive: (json['part_defensive'] as num).toDouble(),
      lignes: (json['allocation'] as List<dynamic>)
          .map((e) => AllocationLine.fromJson(e as Map<String, dynamic>))
          .toList(),
      rendementAnnuelEspere: (json['rendement_annuel_espere'] as num).toDouble(),
      volatiliteAnnuelleEstimee: (json['volatilite_annuelle_estimee'] as num).toDouble(),
      ratioSharpeEstime: (json['ratio_sharpe_estime'] as num).toDouble(),
      hypotheses: json['hypotheses'] as String,
      avertissement: json['avertissement'] as String,
    );
  }
}

/// Résumé d'une simulation enregistrée (GET /v1/portfolio/simulations), sans le
/// détail par classe — suffisant pour une liste d'historique compacte.
class SimulationSummary {
  SimulationSummary({
    required this.id,
    required this.methode,
    required this.partCroissance,
    required this.partDefensive,
    required this.rendementAnnuelEspere,
    required this.volatiliteAnnuelleEstimee,
    required this.ratioSharpeEstime,
    required this.sourceDonnees,
    required this.createdAt,
    this.goalId,
    this.montant,
  });

  final int id;
  final String methode;
  final int? goalId;
  final double? montant;
  final double partCroissance;
  final double partDefensive;
  final double rendementAnnuelEspere;
  final double volatiliteAnnuelleEstimee;
  final double ratioSharpeEstime;
  final String sourceDonnees;
  final DateTime createdAt;

  factory SimulationSummary.fromJson(Map<String, dynamic> json) {
    return SimulationSummary(
      id: json['id'] as int,
      methode: json['methode'] as String,
      goalId: json['goal_id'] as int?,
      montant: json['montant'] == null ? null : (json['montant'] as num).toDouble(),
      partCroissance: (json['part_croissance'] as num).toDouble(),
      partDefensive: (json['part_defensive'] as num).toDouble(),
      rendementAnnuelEspere: (json['rendement_annuel_espere'] as num).toDouble(),
      volatiliteAnnuelleEstimee: (json['volatilite_annuelle_estimee'] as num).toDouble(),
      ratioSharpeEstime: (json['ratio_sharpe_estime'] as num).toDouble(),
      sourceDonnees: json['source_donnees'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}
