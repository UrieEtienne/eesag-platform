
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'api_client.dart';

void main() => runApp(const EesagApp());

class EesagApp extends StatelessWidget {
  const EesagApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'EESAG',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorSchemeSeed: const Color(0xFF102A43),
          scaffoldBackgroundColor: const Color(0xFFF5F7FB),
        ),
        home: const GatePage(),
      );
}

class GatePage extends StatefulWidget {
  const GatePage({super.key});

  @override
  State<GatePage> createState() => _GatePageState();
}

class _GatePageState extends State<GatePage> {
  final api = ApiClient();
  Map<String, dynamic>? user;
  bool checking = true;

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    try {
      user = await api.me();
    } catch (_) {
      user = null;
    } finally {
      if (mounted) setState(() => checking = false);
    }
  }

  void logout() => setState(() => user = null);

  @override
  Widget build(BuildContext context) {
    if (checking) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return user == null
        ? LoginPage(onLogin: (u) => setState(() => user = u))
        : HomePage(user: user!, api: api, onLogout: logout);
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.onLogin});
  final ValueChanged<Map<String, dynamic>> onLogin;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final api = ApiClient();
  final identifiant = TextEditingController();
  final password = TextEditingController();
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
      setState(() => error = 'Renseignez votre identifiant et votre mot de passe.');
      return;
    }

    setState(() {
      busy = true;
      error = '';
    });

    try {
      widget.onLogin(await api.login(
        identifiant.text.trim(),
        password.text,
      ));
    } catch (e) {
      if (mounted) {
        setState(() => error = e.toString().replaceFirst('Exception: ', ''));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
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
                    const CircleAvatar(
                      radius: 34,
                      backgroundImage: AssetImage('assets/logo_eesag.jpg'),
                    ),
                    const SizedBox(height: 16),
                    const Text('EESAG', style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                    )),
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
                      onSubmitted: (_) {
                        if (!busy) submit();
                      },
                      decoration: const InputDecoration(
                        labelText: 'Code secret',
                        prefixIcon: Icon(Icons.lock_outline),
                      ),
                    ),
                    if (error.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(error, style: const TextStyle(color: Colors.red),
                          textAlign: TextAlign.center),
                    ],
                    const SizedBox(height: 18),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: busy ? null : submit,
                        child: Text(busy ? 'Connexion…' : 'Se connecter'),
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
  File? photo;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      notifications = await widget.api.notifications();
    } catch (_) {
      // L'API peut être indisponible.
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> changePhoto() async {
    final selected = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );
    if (selected == null) return;

    final file = File(selected.path);

    try {
      await widget.api.uploadProfilePhoto(file);
      if (!mounted) return;
      setState(() => photo = file);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Photo mise à jour.')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> logout() async {
    try {
      await widget.api.logout();
    } finally {
      if (mounted) widget.onLogout();
    }
  }

  Widget stat(IconData icon, String label, String value) => SizedBox(
        width: 180,
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(icon),
                const SizedBox(height: 8),
                Text(value, style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                )),
                Text(label),
              ],
            ),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final name =
        '${widget.user['prenom'] ?? ''} ${widget.user['nom'] ?? ''}'.trim();
    final role = widget.user['role_libelle'] ?? widget.user['role'] ?? '';
    final unread = notifications
        .where((n) => n is Map && n['lu'] == false)
        .length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('EESAG'),
        actions: [
          IconButton(
            onPressed: loading ? null : load,
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualiser',
          ),
          IconButton(
            onPressed: logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Déconnexion',
          ),
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: Color(0xFF102A43)),
              child: Align(
                alignment: Alignment.bottomLeft,
                child: Text('EESAG\nEspace sécurisé',
                    style: TextStyle(color: Colors.white, fontSize: 20)),
              ),
            ),
            const ListTile(
              leading: Icon(Icons.home_outlined),
              title: Text('Accueil'),
            ),
            ListTile(
              leading: const Icon(Icons.notifications_none),
              title: Text('Notifications ($unread)'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.person_outline),
              title: const Text('Mon profil'),
              onTap: () {
                Navigator.pop(context);
                changePhoto();
              },
            ),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text('Centre de contrôle'),
          const SizedBox(height: 6),
          Text(name.isEmpty ? 'Mon espace' : name,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  )),
          Text(role),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              stat(Icons.notifications_none, 'Notifications',
                  '${notifications.length}'),
              stat(Icons.security_outlined, 'Sécurité', 'Active'),
              stat(Icons.account_circle_outlined, 'Compte',
                  widget.user['identifiant']?.toString() ?? ''),
            ],
          ),
          Card(
            child: ListTile(
              leading: photo == null
                  ? const CircleAvatar(child: Icon(Icons.person))
                  : CircleAvatar(backgroundImage: FileImage(photo!)),
              title: const Text('Photo de profil'),
              subtitle: const Text('Ajouter ou modifier votre photo'),
              trailing: IconButton(
                onPressed: changePhoto,
                icon: const Icon(Icons.photo_camera_outlined),
                tooltip: 'Modifier la photo',
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text('Dernières notifications',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          if (notifications.isEmpty)
            const Card(
              child: ListTile(
                leading: Icon(Icons.inbox_outlined),
                title: Text('Aucune notification'),
                subtitle: Text('Votre espace est à jour.'),
              ),
            ),
          ...notifications.take(8).map((item) {
            final n = Map<String, dynamic>.from(item as Map);
            final lu = n['lu'] == true;
            return Card(
              child: ListTile(
                leading: Icon(lu ? Icons.drafts_outlined : Icons.markunread),
                title: Text(n['titre']?.toString() ?? 'Notification'),
                subtitle: Text(n['message']?.toString() ?? ''),
              ),
            );
          }),
        ],
      ),
    );
  }
}
