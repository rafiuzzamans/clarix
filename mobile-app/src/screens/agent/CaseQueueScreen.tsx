import React, {useEffect, useState, useCallback} from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  RefreshControl, ActivityIndicator, TextInput,
} from 'react-native';
import {casesApi} from '../../api';
import {theme, priorityConfig, statusConfig} from '../../theme';
import {format} from 'date-fns';
import {useNavigation} from '@react-navigation/native';

export default function CaseQueueScreen() {
  const navigation = useNavigation<any>();
  const [cases, setCases]       = useState<any[]>([]);
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch]     = useState('');
  const [filterPriority, setFilterPri] = useState('');
  const [page, setPage]         = useState(1);
  const [total, setTotal]       = useState(0);

  const loadCases = useCallback(async (reset = false) => {
    try {
      const p = reset ? 1 : page;
      const {data} = await casesApi.list({
        page: p, page_size: 20,
        search: search || undefined,
        priority: filterPriority || undefined,
        status: 'open,in_progress,escalated',
      });
      setCases(reset ? data.items : prev => [...prev, ...data.items]);
      setTotal(data.total);
      if (!reset) setPage(p + 1);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [page, search, filterPriority]);

  useEffect(() => {loadCases(true);}, [search, filterPriority]);

  const onRefresh = () => {
    setRefreshing(true);
    setPage(1);
    loadCases(true);
  };

  const PRIORITIES = ['', 'urgent', 'high', 'medium', 'low'];

  const renderItem = ({item}: {item: any}) => {
    const pc = priorityConfig[item.priority as keyof typeof priorityConfig];
    const sc = statusConfig[item.status as keyof typeof statusConfig];
    return (
      <TouchableOpacity
        testID={`case-item-${item.case_number}`}
        style={[styles.caseCard, item.is_escalated && styles.escalatedCard]}
        onPress={() => navigation.navigate('CaseDetail', {caseId: item.id})}>

        <View style={styles.caseHeader}>
          <Text style={styles.caseNum}>#{item.case_number}</Text>
          <View style={styles.badges}>
            <View style={[styles.badge, {backgroundColor: pc?.color + '33', borderColor: pc?.color + '88'}]}>
              <Text style={[styles.badgeText, {color: pc?.color}]}>{pc?.label}</Text>
            </View>
            <View style={[styles.badge, {backgroundColor: sc?.color + '33', borderColor: sc?.color + '88'}]}>
              <Text style={[styles.badgeText, {color: sc?.color}]}>{sc?.label}</Text>
            </View>
          </View>
        </View>

        <Text style={styles.caseTitle} numberOfLines={2}>{item.title}</Text>

        <View style={styles.caseMeta}>
          <Text style={styles.caseMetaText}>📁 {item.category?.replace('_', ' ') || 'Uncategorised'}</Text>
          <Text style={styles.caseMetaText}>
            {item.assigned_to ? '👤 Assigned' : '⚠️ Unassigned'}
          </Text>
          <Text style={styles.caseMetaText}>
            {format(new Date(item.created_at), 'MMM d, HH:mm')}
          </Text>
        </View>

        {item.is_escalated && (
          <View style={styles.escalatedBadge}>
            <Text style={styles.escalatedText}>🚨 ESCALATED</Text>
          </View>
        )}

        {item.sla_deadline && new Date(item.sla_deadline) < new Date() && item.status !== 'resolved' && (
          <View style={styles.slaBreach}>
            <Text style={styles.slaText}>⏰ SLA BREACHED</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      {/* Search */}
      <View style={styles.searchBar}>
        <TextInput
          testID="case-search-input"
          style={styles.searchInput}
          placeholder="Search cases..."
          placeholderTextColor={theme.colors.textMuted}
          value={search}
          onChangeText={t => {setSearch(t); setPage(1);}}
        />
      </View>

      {/* Priority filter */}
      <View style={styles.filterRow}>
        {PRIORITIES.map(p => (
          <TouchableOpacity
            key={p || 'all'}
            testID={`filter-${p || 'all'}`}
            style={[styles.filterChip, filterPriority === p && styles.filterChipActive]}
            onPress={() => {setFilterPri(p); setPage(1);}}>
            <Text style={[styles.filterChipText, filterPriority === p && styles.filterChipTextActive]}>
              {p || 'All'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.countText}>{total} cases</Text>

      {loading ? (
        <View style={styles.centered}><ActivityIndicator color={theme.colors.primary} size="large" /></View>
      ) : (
        <FlatList
          data={cases}
          keyExtractor={item => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
          onEndReached={() => {if (cases.length < total) loadCases();}}
          onEndReachedThreshold={0.3}
          ListEmptyComponent={() => (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>No cases found</Text>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container:        {flex: 1, backgroundColor: theme.colors.bg},
  searchBar:        {padding: theme.spacing.md, paddingBottom: 0},
  searchInput:      {
    backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.md,
    borderWidth: 1, borderColor: theme.colors.border,
    color: theme.colors.textPrimary, paddingHorizontal: theme.spacing.md,
    paddingVertical: 10, fontSize: theme.font.base,
  },
  filterRow:        {flexDirection: 'row', paddingHorizontal: theme.spacing.md, paddingVertical: theme.spacing.sm, gap: 8},
  filterChip:       {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: theme.radius.full,
    backgroundColor: theme.colors.bgCard, borderWidth: 1, borderColor: theme.colors.border,
  },
  filterChipActive: {backgroundColor: theme.colors.primary + '33', borderColor: theme.colors.primary},
  filterChipText:   {fontSize: theme.font.xs, color: theme.colors.textSecondary, fontWeight: '600', textTransform: 'capitalize'},
  filterChipTextActive: {color: theme.colors.primary},
  countText:        {fontSize: theme.font.xs, color: theme.colors.textMuted, paddingHorizontal: theme.spacing.lg, marginBottom: 4},
  list:             {padding: theme.spacing.md, gap: 12},
  caseCard:         {
    backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.lg,
    padding: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.border,
  },
  escalatedCard:    {borderColor: theme.colors.danger + '66'},
  caseHeader:       {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8},
  caseNum:          {fontSize: theme.font.xs, color: theme.colors.textMuted, fontFamily: 'monospace', fontWeight: '600'},
  badges:           {flexDirection: 'row', gap: 6},
  badge:            {paddingHorizontal: 8, paddingVertical: 3, borderRadius: theme.radius.sm, borderWidth: 1},
  badgeText:        {fontSize: 10, fontWeight: '700', textTransform: 'uppercase'},
  caseTitle:        {fontSize: theme.font.base, fontWeight: '600', color: theme.colors.textPrimary, marginBottom: 8},
  caseMeta:         {flexDirection: 'row', flexWrap: 'wrap', gap: 8},
  caseMetaText:     {fontSize: theme.font.xs, color: theme.colors.textSecondary},
  escalatedBadge:   {marginTop: 8, backgroundColor: theme.colors.danger + '22', borderRadius: theme.radius.sm, padding: 6, alignSelf: 'flex-start'},
  escalatedText:    {fontSize: 10, color: theme.colors.danger, fontWeight: '800'},
  slaBreach:        {marginTop: 4, backgroundColor: theme.colors.warning + '22', borderRadius: theme.radius.sm, padding: 6, alignSelf: 'flex-start'},
  slaText:          {fontSize: 10, color: theme.colors.warning, fontWeight: '800'},
  centered:         {flex: 1, alignItems: 'center', justifyContent: 'center'},
  empty:            {padding: 40, alignItems: 'center'},
  emptyText:        {color: theme.colors.textMuted, fontSize: theme.font.base},
});
