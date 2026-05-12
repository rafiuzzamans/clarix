import React, {useState} from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert,
} from 'react-native';
import {theme} from '../../theme';
import {useAuthStore} from '../../store/authStore';

export default function LoginScreen() {
  const {login} = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [showMfa, setShowMfa] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {Alert.alert('Error', 'Please enter email and password'); return;}
    setLoading(true);
    try {
      await login(email, password, mfaCode || undefined);
    } catch (err: any) {
      const msg = err?.response?.data?.detail;
      if (msg === 'MFA code required') {
        setShowMfa(true);
        Alert.alert('MFA Required', 'Please enter your 6-digit authenticator code');
      } else {
        Alert.alert('Login Failed', msg || 'Invalid credentials');
      }
    } finally {
      setLoading(false);
    }
  };

  const quickFill = (role: string) => {
    setEmail(`${role}@csplatform.local`);
    setPassword('Admin@123');
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logoBox}>
            <Text style={styles.logoIcon}>🤖</Text>
          </View>
          <Text style={styles.appName}>CS Platform</Text>
          <Text style={styles.tagline}>AI-Powered Customer Service</Text>
        </View>

        {/* Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Sign in to your account</Text>

          <View style={styles.field}>
            <Text style={styles.label}>Email address</Text>
            <TextInput
              testID="email-input"
              style={styles.input}
              placeholder="you@company.com"
              placeholderTextColor={theme.colors.textMuted}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>Password</Text>
            <View style={styles.inputRow}>
              <TextInput
                testID="password-input"
                style={[styles.input, {flex: 1, marginBottom: 0}]}
                placeholder="••••••••"
                placeholderTextColor={theme.colors.textMuted}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPw}
              />
              <TouchableOpacity
                onPress={() => setShowPw(!showPw)}
                style={styles.eyeBtn}>
                <Text style={styles.eyeText}>{showPw ? '🙈' : '👁'}</Text>
              </TouchableOpacity>
            </View>
          </View>

          {showMfa && (
            <View style={styles.field}>
              <Text style={styles.label}>🔐 MFA Code</Text>
              <TextInput
                testID="mfa-input"
                style={[styles.input, styles.mfaInput]}
                placeholder="000000"
                placeholderTextColor={theme.colors.textMuted}
                value={mfaCode}
                onChangeText={setMfaCode}
                keyboardType="number-pad"
                maxLength={6}
              />
            </View>
          )}

          <TouchableOpacity
            testID="login-btn"
            style={[styles.loginBtn, loading && styles.loginBtnDisabled]}
            onPress={handleLogin}
            disabled={loading}>
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.loginBtnText}>Sign In</Text>}
          </TouchableOpacity>

          {/* Demo quick-fill */}
          <View style={styles.demoSection}>
            <Text style={styles.demoTitle}>Demo accounts (Admin@123)</Text>
            <View style={styles.demoGrid}>
              {['admin', 'manager', 'agent1', 'customer'].map(role => (
                <TouchableOpacity
                  key={role}
                  testID={`demo-${role}`}
                  style={styles.demoBtn}
                  onPress={() => quickFill(role)}>
                  <Text style={styles.demoBtnText}>{role}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container:       {flex: 1, backgroundColor: theme.colors.bg},
  scroll:          {flexGrow: 1, justifyContent: 'center', padding: theme.spacing.lg},
  logoContainer:   {alignItems: 'center', marginBottom: theme.spacing.xl},
  logoBox:         {
    width: 72, height: 72, borderRadius: theme.radius.xl,
    backgroundColor: theme.colors.primary,
    alignItems: 'center', justifyContent: 'center', marginBottom: theme.spacing.md,
    ...theme.shadow.md,
  },
  logoIcon:        {fontSize: 32},
  appName:         {fontSize: theme.font.xxl, fontWeight: '800', color: theme.colors.textPrimary},
  tagline:         {fontSize: theme.font.sm, color: theme.colors.textSecondary, marginTop: 4},
  card:            {
    backgroundColor: theme.colors.bgCard,
    borderRadius: theme.radius.xl,
    padding: theme.spacing.lg,
    borderWidth: 1, borderColor: theme.colors.border,
  },
  cardTitle:       {fontSize: theme.font.md, fontWeight: '700', color: theme.colors.textPrimary, marginBottom: theme.spacing.lg},
  field:           {marginBottom: theme.spacing.md},
  label:           {fontSize: theme.font.sm, color: theme.colors.textSecondary, fontWeight: '600', marginBottom: 6},
  input:           {
    backgroundColor: theme.colors.bgInput,
    borderRadius: theme.radius.md,
    borderWidth: 1, borderColor: theme.colors.border,
    color: theme.colors.textPrimary,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: 12,
    fontSize: theme.font.base,
  },
  inputRow:        {flexDirection: 'row', alignItems: 'center', gap: 8},
  eyeBtn:          {padding: 8},
  eyeText:         {fontSize: 18},
  mfaInput:        {textAlign: 'center', fontSize: theme.font.xl, letterSpacing: 8},
  loginBtn:        {
    backgroundColor: theme.colors.primary,
    borderRadius: theme.radius.md,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: theme.spacing.sm,
    ...theme.shadow.sm,
  },
  loginBtnDisabled: {opacity: 0.6},
  loginBtnText:    {color: '#fff', fontSize: theme.font.base, fontWeight: '700'},
  demoSection:     {marginTop: theme.spacing.lg, paddingTop: theme.spacing.md, borderTopWidth: 1, borderTopColor: theme.colors.border},
  demoTitle:       {fontSize: theme.font.xs, color: theme.colors.textMuted, textAlign: 'center', marginBottom: theme.spacing.sm},
  demoGrid:        {flexDirection: 'row', flexWrap: 'wrap', gap: 8},
  demoBtn:         {
    flex: 1, minWidth: '45%',
    backgroundColor: theme.colors.bgCardAlt,
    borderRadius: theme.radius.sm, borderWidth: 1, borderColor: theme.colors.border,
    paddingVertical: 8, alignItems: 'center',
  },
  demoBtnText:     {color: theme.colors.textSecondary, fontSize: theme.font.xs, fontWeight: '600'},
});
