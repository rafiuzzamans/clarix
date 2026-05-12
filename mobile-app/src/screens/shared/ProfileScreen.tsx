import React from 'react';
import {View, Text, TouchableOpacity, StyleSheet, Alert, ScrollView} from 'react-native';
import {useAuthStore} from '../../store/authStore';
import {theme} from '../../theme';

export default function ProfileScreen() {
  const {user, logout} = useAuthStore();

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      {text: 'Cancel', style: 'cancel'},
      {text: 'Sign Out', style: 'destructive', onPress: logout},
    ]);
  };

  const roleColors: Record<string, string> = {
    admin: theme.colors.danger,
    manager: theme.colors.warning,
    supervisor: theme.colors.info,
    agent: theme.colors.primary,
    customer: theme.colors.success,
  };

  return (
    <ScrollView style={styles.container}>
      {/* Avatar */}
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user?.full_name?.[0] || '?'}</Text>
        </View>
        <Text style={styles.name}>{user?.full_name}</Text>
        <Text style={styles.email}>{user?.email}</Text>
        <View style={[styles.roleBadge, {backgroundColor: (roleColors[user?.role || ''] || theme.colors.primary) + '33', borderColor: roleColors[user?.role || ''] + '88'}]}>
          <Text style={[styles.roleText, {color: roleColors[user?.role || ''] || theme.colors.primary}]}>
            {user?.role?.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Details */}
      <View style={styles.card}>
        {[
          ['Department',    user?.department || '—'],
          ['Account Status', user?.status],
          ['MFA Enabled',   user?.mfa_enabled ? '✅ Yes' : '❌ No'],
          ['User ID',       user?.id?.slice(0, 16) + '...'],
        ].map(([label, value]) => (
          <View key={label} style={styles.infoRow}>
            <Text style={styles.infoLabel}>{label}</Text>
            <Text style={styles.infoValue}>{value as string}</Text>
          </View>
        ))}
      </View>

      {/* Sign out */}
      <TouchableOpacity testID="logout-btn" style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>

      {/* Version */}
      <Text style={styles.version}>CS Platform v1.0.0</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:   {flex: 1, backgroundColor: theme.colors.bg},
  header:      {alignItems: 'center', padding: theme.spacing.xl, paddingBottom: theme.spacing.lg},
  avatar:      {width: 80, height: 80, borderRadius: 40, backgroundColor: theme.colors.primary, alignItems: 'center', justifyContent: 'center', marginBottom: theme.spacing.md, ...theme.shadow.md},
  avatarText:  {fontSize: 36, color: '#fff', fontWeight: '700'},
  name:        {fontSize: theme.font.xl, fontWeight: '800', color: theme.colors.textPrimary},
  email:       {fontSize: theme.font.sm, color: theme.colors.textSecondary, marginTop: 4},
  roleBadge:   {marginTop: theme.spacing.sm, paddingHorizontal: 16, paddingVertical: 6, borderRadius: theme.radius.full, borderWidth: 1},
  roleText:    {fontSize: theme.font.xs, fontWeight: '800', letterSpacing: 1},
  card:        {margin: theme.spacing.md, backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.xl, borderWidth: 1, borderColor: theme.colors.border, overflow: 'hidden'},
  infoRow:     {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: theme.spacing.md, borderBottomWidth: 1, borderBottomColor: theme.colors.border},
  infoLabel:   {fontSize: theme.font.sm, color: theme.colors.textMuted},
  infoValue:   {fontSize: theme.font.sm, color: theme.colors.textPrimary, fontWeight: '600'},
  logoutBtn:   {margin: theme.spacing.md, backgroundColor: theme.colors.danger + '22', borderWidth: 1, borderColor: theme.colors.danger + '66', borderRadius: theme.radius.xl, paddingVertical: 14, alignItems: 'center'},
  logoutText:  {color: theme.colors.danger, fontSize: theme.font.base, fontWeight: '700'},
  version:     {textAlign: 'center', color: theme.colors.textMuted, fontSize: theme.font.xs, marginBottom: theme.spacing.xl},
});
