import '../../../core/network/api_client.dart';
import 'allocation_models.dart';
import 'asset_class_info.dart';

class AllocationRepository {
  AllocationRepository(this._apiClient);

  final ApiClient _apiClient;

  /// Récupère une allocation adaptée au profil. `montant` (capital total placé)
  /// est optionnel : s'il est fourni, chaque ligne porte un montant en euros.
  /// `save: false` : simulation interactive, non ajoutée à l'historique.
  Future<PortfolioAllocation> getAllocation({
    required String methode,
    double? montant,
    bool save = false,
  }) async {
    final response = await _apiClient.get<Map<String, dynamic>>(
      '/portfolio/allocation',
      queryParameters: {
        'methode': methode,
        if (montant != null) 'montant': montant,
        'save': save,
      },
    );
    return PortfolioAllocation.fromJson(response.data!);
  }

  Future<List<AssetClassInfo>> listAssetClasses() async {
    final response = await _apiClient.get<List<dynamic>>('/portfolio/asset-classes');
    return (response.data ?? [])
        .map((e) => AssetClassInfo.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<SimulationSummary>> listSimulations({int limit = 20}) async {
    final response = await _apiClient.get<List<dynamic>>(
      '/portfolio/simulations',
      queryParameters: {'limit': limit},
    );
    return (response.data ?? [])
        .map((e) => SimulationSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
