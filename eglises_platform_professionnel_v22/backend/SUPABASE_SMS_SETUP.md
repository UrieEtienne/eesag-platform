# EESAG — OTP SMS avec Supabase Auth

EESAG utilise maintenant **Supabase Auth** pour générer et vérifier les codes OTP de téléphone. Django reste le système métier principal : comptes, rôles, églises, permissions et activation.

## Important

Supabase Auth ne livre pas physiquement des SMS « tout seul ». Le projet Supabase doit avoir l'authentification téléphone activée et un fournisseur SMS configuré. La documentation Supabase indique notamment MessageBird, Twilio, Vonage et TextLocal comme fournisseurs supportés. Voir : https://supabase.com/docs/guides/auth/phone-login

Si tu refuses Twilio, sélectionne un autre fournisseur disponible dans Supabase et configure-le dans **Authentication → Providers → Phone**.

## Variables Django

Dans `backend/.env` :

```env
SMS_PROVIDER=supabase
SUPABASE_URL=https://VOTRE-PROJET.supabase.co
SUPABASE_PUBLISHABLE_KEY=VOTRE_CLE_PUBLISHABLE
```

Ne mets jamais une `secret` key Supabase dans React, Flutter ou dans une application cliente.

## Flux EESAG

1. Django crée le compte local avec `actif=False`.
2. Django demande à Supabase Auth d'envoyer un OTP au numéro en E.164.
3. Le membre reçoit le code SMS.
4. Django reçoit le code depuis le formulaire EESAG et demande à Supabase de le vérifier.
5. Si Supabase confirme l'OTP, Django active le compte et délivre le JWT EESAG.

Supabase documente `sign_in_with_otp`/`verify_otp` pour ce flux. Le projet utilise directement les endpoints Auth de Supabase afin de ne pas dépendre d'un SDK côté serveur.

## Test

```bash
python manage.py check
python manage.py tester_sms +224XXXXXXXX
```

Le journal `Journal SMS` indique si l'appel à Supabase a été accepté ou refusé.
