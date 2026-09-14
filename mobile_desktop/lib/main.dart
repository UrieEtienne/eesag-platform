import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'api_client.dart';

void main() {
  runApp(const EesagApp());
}

class EesagApp extends StatelessWidget {
  const EesagApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'EESAG',
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF102A43),
        scaffoldBackgroundColor: const Color(0xFFF5F7FB),
      ),
      home: const GatePage(),
    );
  }
}

class GatePage extends StatefulWidget {
  const GatePage({super.key});

  @override
  State<GatePage> createState() => _GatePageState();
}

class _GatePageState extends State<GatePage> {
  final ApiClient api = ApiClient();
  Map<String, dynamic>? user;

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    try {
      final me = await api.me();
      if (mounted) {
        setState(() => user = me);
      }
    } catch (_) {}
  }

  void _onLogout() {
    if (mounted) {
      setState(() => user = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (user == null) {
      return LoginPage(
        onLogin: (loggedUser) {
          setState(() => user = loggedUser);
        },
      );
    }

    return HomePage(
      user: user!,
      api: api,
      onLogout: _onLogout,
    );
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.onLogin});

  final void Function(Map<String, dynamic>) onLogin;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final ApiClient api = ApiClient();
  final TextEditingController identifiant = TextEditingController();
  final TextEditingController password = TextEditingController();

  bool busy = false;
  String error = '';

  @override
  void dispose() {
    identifiant.dispose();
    password.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (identifiant.text.trim().isEmpty || password.text.isEmpty) {
      setState(() => error = 'Veuillez renseigner votre identifiant et votre mot de passe.');
      return;
    }

    setState(() {
      busy = true;
      error = '';
    });

    try {
      final loggedUser = await api.login(
        identifiant.text.trim(),
        password.text,
      );
      if (mounted) {
        widget.onLogin(loggedUser);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          error = e.toString().replaceFirst('Exception: ', '');
        });
      }
    } finally {
      if (mounted) {
        setState(() => busy = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 460),
          child: Card(
            margin: const EdgeInsets.all(24),
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircleAvatar(
                    radius: 34,
                    backgroundColor: Colors.white,
                    backgroundImage: const AssetImage('assets/logo_eesag.jpg'),
                  ),
                  const SizedBox(height: 18),
                  const Text(
                    'EESAG',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 22,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text('Portail sécurisé mobile & desktop'),
                  const SizedBox(height: 24),
                  TextField(
                    controller: identifiant,
                    decoration: const InputDecoration(
                      labelText: 'Identifiant',
                      prefixIcon: Icon(Icons.badge_outlined),
                    ),
                    textInputAction: TextInputAction.next,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: password,
                    obscureText: true,
                    onSubmitted: (_) => busy ? null : submit(),
                    decoration: const InputDecoration(
                      labelText: 'Code secret',
                      prefixIcon: Icon(Icons.lock_outline),
                    ),
                  ),
                  if (error.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Text(
                      error,
                      style: const TextStyle(color: Colors.red),
                      textAlign: TextAlign.center,
                    ),
                  ],
                  const SizedBox(height: 18),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: busy ? null : submit,
                      child: Text(
                        busy ? 'Connexion…' : 'Se connecter',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({
    super.key,
    required this.user,
    required this.api,
    required this.onLogout,
  });

  final Map<String, dynamic> user;
  final ApiClient api;
  final VoidCallback onLogout;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  List<dynamic> notifications = [];
  File? localPhoto;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final values = await widget.api.notifications();
      if (mounted) {
        setState(() => notifications = values);
      }
    } catch (_) {
      // L'API peut être indisponible lors du premier démarrage.
    } finally {
      if (mounted) {
        setState(() => loading = false);
      }
    }
  }

  Future<void> _photo() async {
    final XFile? selected = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );

    if (selected == null) {
      return;
    }

    final file = File(selected.path);

    try {
      await widget.api.uploadProfilePhoto(file);
      if (mounted) {
        setState(() => localPhoto = file);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Photo mise à jour.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
  }

  Future<void> _logout() async {
    try {
      await widget.api.logout();
    } finally {
      if (mounted) {
        widget.onLogout();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final String name =
        '${widget.user['prenom'] ?? ''} ${widget.user['nom'] ?? ''}'.trim();
    final String role =
        widget.user['role_libelle'] ?? widget.user['role'] ?? '';

    final int unread = notifications
        .where((item) => item is Map && item['lu'] == false)
        .length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('EESAG'),
        actions: [
          IconButton(
            onPressed: loading ? null : _load,
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualiser',
          ),
          IconButton(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Déconnexion',
          ),
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: const BoxDecoration(
                color: Color(0xFF102A43),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 54,
                        height: 54,
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(9),
                          child: Image.asset(
                            'assets/logo_eesag.jpg',
                            fit: BoxFit.cover,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'EESAG',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Espace sécurisé',
                    style: TextStyle(color: Colors.white70),
                  ),
                ],
              ),
            ),
            const ListTile(
              leading: Icon(Icons.home_outlined),
              title: Text('Accueil'),
            ),
            ListTile(
              leading: const Icon(Icons.notifications_none),
              title: Text('Notifications ($unread)'),
              onTap: () {},
            ),
            ListTile(
              leading: const Icon(Icons.person_outline),
              title: const Text('Mon profil'),
              onTap: _photo,
            ),
          ],
        ),
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Centre de contrôle',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 6),
                Text(
                  name.isEmpty ? 'Mon espace' : name,
                  style: Theme.of(context)
                      .textTheme
                      .headlineMedium
                      ?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                Text(role),
                const SizedBox(height: 20),
                Wrap(
                  spacing: 14,
                  runSpacing: 14,
                  children: [
                    _stat(
                      Icons.notifications_none,
                      'Notifications',
                      notifications.length.toString(),
                    ),
                    _stat(Icons.security_outlined, 'Sécurité', 'Active'),
                    _stat(
                      Icons.account_circle_outlined,
                      'Compte',
                      widget.user['identifiant']?.toString() ?? '',
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Row(
                      children: [
                        localPhoto != null
                            ? CircleAvatar(
                                radius: 30,
                                backgroundImage: FileImage(localPhoto!),
                              )
                            : const CircleAvatar(
                                radius: 30,
                                child: Icon(Icons.person),
                              ),
                        const SizedBox(width: 14),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Photo de profil',
                                style: TextStyle(fontWeight: FontWeight.w800),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Ajoutez ou mettez à jour votre photo directement depuis le téléphone ou le poste de travail.',
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        OutlinedButton.icon(
                          onPressed: null,
                          icon: Icon(Icons.photo_camera_outlined),
                          label: Text('Modifier'),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                const Text(
                  'Dernières notifications',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 10),
                if (notifications.isEmpty)
                  const Card(
                    child: ListTile(
                      leading: Icon(Icons.inbox_outlined),
                      title: Text('Aucune notification'),
                      subtitle: Text('Votre espace est à jour.'),
                    ),
                  ),
                ...notifications.take(8).map((item) {
                  final Map<String, dynamic> notification =
                      item is Map<String, dynamic>
                          ? item
                          : Map<String, dynamic>.from(item as Map);
                  final bool lu = notification['lu'] == true;
                  return Card(
                    child: ListTile(
                      leading: Icon(
                        lu ? Icons.drafts_outlined : Icons.markunread,
                      ),
                      title: Text(
                        notification['titre']?.toString() ?? 'Notification',
                      ),
                      subtitle: Text(
                        notification['message']?.toString() ?? '',
                      ),
                    ),
                  );
                }),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _stat(IconData icon, String label, String value) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 20,
              ),
            ),
            Text(label),
          ],
        ),
      ),
    );
  }
}
