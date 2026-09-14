import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? const String.fromEnvironment('API_URL', defaultValue: 'http://127.0.0.1:8000/api');
  final String baseUrl;

  Future<Map<String, String>> _headers() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    return {
      'Content-Type': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  Future<Map<String, dynamic>> login(String identifiant, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'identifiant': identifiant, 'password': password}),
    );
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode >= 400) throw Exception(data['detail'] ?? 'Connexion impossible.');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', data['access']);
    await prefs.setString('refresh_token', data['refresh']);
    return data['utilisateur'] as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> me() async {
    final response = await http.get(Uri.parse('$baseUrl/auth/moi/'), headers: await _headers());
    if (response.statusCode >= 400) throw Exception('Session expirée.');
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> notifications() async {
    final response = await http.get(Uri.parse('$baseUrl/notifications/'), headers: await _headers());
    if (response.statusCode >= 400) throw Exception('Impossible de charger les notifications.');
    final data = jsonDecode(response.body);
    return data is Map<String, dynamic> ? (data['results'] as List<dynamic>? ?? []) : (data as List<dynamic>);
  }

  Future<void> uploadProfilePhoto(File file) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    final request = http.MultipartRequest('PATCH', Uri.parse('$baseUrl/auth/profil/'));
    if (token != null) request.headers['Authorization'] = 'Bearer $token';
    request.files.add(await http.MultipartFile.fromPath('photo', file.path));
    final response = await request.send();
    if (response.statusCode >= 400) throw Exception('Impossible de mettre à jour la photo.');
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
