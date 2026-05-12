import React, {useEffect, useState} from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  TextInput, ActivityIndicator, Alert,
} from 'react-native';
import {casesApi} from '../../api';
import {theme, priorityConfig, statusConfig} from '../../theme';
import {format} from 'date-fns';
import {useRoute} from '@react-navigation/native';

export default function CaseDetailScreen() {
  const route = useRoute<any>();
  const {caseId} = route.params;
  const [caseData, setCaseData] = useState<any>(null);
  const [notes, setNotes]       = useState<any[]>([]);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [note, setNote]         = useState('');
  const [isInternal, setIsInternal] = useState(true);
  const [loading, setLoading]   = useState(true);
  const [tab, setTab]           = useState<'notes' | 'timeline' | 'ai'>('notes');
  const [adding, setAdding]     = useState(false);

  const load = async () => {
    try {
      const [caseRes, notesRes, timelineRes] = await Promise.all([
        casesApi.get(caseId),
        casesApi.getNotes(caseId),
        casesApi.getTimeline(caseId),
      ]);
      setCaseData(caseRes.data);
      setNotes(notesRes.data);
      setTimeline(timelineRes.data);
    } catch (e) {console.error(e);}
    finally {setLoading(false);}
  };

  useEffect(() => {load();}, [caseId]);

  const handleUpdateStatus = (status: string) => {
    Alert.alert('Confirm', `Mark case as ${status}?`, [
      {text: 'Cancel', style: 'cancel'},
      {
        text: 'Confirm',
        onPress: async () => {
          await casesApi.update(caseId, {status});
          load();
        },
      },
    ]);
  };

  const handleEscalate = () => {
    Alert.prompt('Escalate Case', 'Enter escalation reason:', async reason => {
      if (reason) {
        await casesApi.escalate(caseId, reason);
        load();
      }
    });
  };

  const handleAddNote = async () => {
    if (!note.trim()) return;
    setAdding(true);
    try {
      await casesApi.addNote(caseId, note.trim(), isInternal);
      setNote('');
      await load();
    } finally {setAdding(false);}
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={theme.colors.primary} size="large" />
      </View>
    );
  }

  const c = caseData;
  const pc = priorityConfig[c?.priority as keyof typeof priorityConfig];
  const sc = statusConfig[c?.status as keyof typeof statusConfig];

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>

      {/* Header card */}
      <View style={styles.headerCard}>
        <View style={styles.headerTop}>
          <Text style={styles.caseNum}>Case #{c?.case_number}</Text>
          <View style={styles.badges}>
            {pc && (
              <View style={[styles.badge, {backgroundColor: pc.color + '33', borderColor: pc.color + '88'}]}>
                <Text style={[styles.badgeText, {color: pc.color}]}>{pc.label}</Text>
              </View>
            )}
            {sc && (
              <View style={[styles.badge, {backgroundColor: sc.color + '33', borderColor: sc.color + '88'}]}>
                <Text style={[styles.badgeText, {color: sc.color}]}>{sc.label}</Text>
              </View>
            )}
          </View>
        </View>
        <Text style={styles.caseTitle}>{c?.title}</Text>
        <Text style={styles.caseMessage}>{c?.message}</Text>

        <View style={styles.metaGrid}>
          {[
            ['Category', c?.category?.replace('_', ' ') || '—'],
            ['Source',   c?.source],
            ['Created',  c?.created_at ? format(new Date(c.created_at), 'MMM d, HH:mm') : '—'],
            ['SLA',      c?.sla_deadline ? format(new Date(c.sla_deadline), 'MMM d, HH:mm') : '—'],
          ].map(([label, value]) => (
            <View key={label} style={styles.metaItem}>
              <Text style={styles.metaLabel}>{label}</Text>
              <Text style={styles.metaValue}>{value}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actionsRow}>
        {c?.status !== 'resolved' && c?.status !== 'closed' && (
          <TouchableOpacity
            testID="resolve-btn"
            style={[styles.actionBtn, styles.resolveBtn]}
            onPress={() => handleUpdateStatus('resolved')}>
            <Text style={styles.resolveBtnText}>✓ Resolve</Text>
          </TouchableOpacity>
        )}
        {!c?.is_escalated && (
          <TouchableOpacity
            testID="escalate-btn"
            style={[styles.actionBtn, styles.escalateBtn]}
            onPress={handleEscalate}>
            <Text style={styles.escalateBtnText}>⬆ Escalate</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.actionBtn, styles.closeBtn]}
          onPress={() => handleUpdateStatus('closed')}>
          <Text style={styles.closeBtnText}>Close</Text>
        </TouchableOpacity>
      </View>

      {/* AI Analysis */}
      {(c?.ai_category || c?.ai_priority) && (
        <View style={styles.aiCard}>
          <Text style={styles.aiTitle}>🤖 AI Analysis</Text>
          <View style={styles.aiGrid}>
            {[
              ['Category',  c.ai_category?.replace('_', ' ')],
              ['Priority',  c.ai_priority],
              ['Sentiment', c.ai_sentiment],
              ['Confidence', c.ai_confidence ? `${Math.round(c.ai_confidence * 100)}%` : '—'],
            ].map(([label, val]) => (
              <View key={label} style={styles.aiItem}>
                <Text style={styles.aiLabel}>{label}</Text>
                <Text style={styles.aiValue}>{val || '—'}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Tabs */}
      <View style={styles.tabRow}>
        {(['notes', 'timeline', 'ai'] as const).map(t => (
          <TouchableOpacity
            key={t}
            testID={`tab-${t}`}
            style={[styles.tab, tab === t && styles.tabActive]}
            onPress={() => setTab(t)}>
            <Text style={[styles.tabText, tab === t && styles.tabTextActive]}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Notes */}
      {tab === 'notes' && (
        <View style={styles.section}>
          {notes.map((n: any) => (
            <View key={n.id} style={[styles.noteCard, n.is_internal && styles.internalNote]}>
              <Text style={styles.noteType}>{n.is_internal ? '🔒 Internal' : '💬 Public'}</Text>
              <Text style={styles.noteContent}>{n.content}</Text>
              <Text style={styles.noteTime}>{format(new Date(n.created_at), 'MMM d, HH:mm')}</Text>
            </View>
          ))}
          {notes.length === 0 && <Text style={styles.emptyText}>No notes yet</Text>}

          <View style={styles.addNoteRow}>
            <View style={styles.noteTypeToggle}>
              {[['🔒 Internal', true], ['💬 Public', false]].map(([label, val]) => (
                <TouchableOpacity
                  key={String(val)}
                  style={[styles.toggleBtn, isInternal === val && styles.toggleBtnActive]}
                  onPress={() => setIsInternal(val as boolean)}>
                  <Text style={[styles.toggleText, isInternal === val && styles.toggleTextActive]}>
                    {label as string}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <View style={styles.noteInputRow}>
              <TextInput
                testID="note-input"
                style={styles.noteInput}
                placeholder="Add a note..."
                placeholderTextColor={theme.colors.textMuted}
                value={note}
                onChangeText={setNote}
                multiline
              />
              <TouchableOpacity
                testID="add-note-btn"
                style={[styles.sendBtn, adding && styles.sendBtnDisabled]}
                onPress={handleAddNote}
                disabled={adding || !note.trim()}>
                {adding
                  ? <ActivityIndicator color="#fff" size="small" />
                  : <Text style={styles.sendBtnText}>Send</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {/* Timeline */}
      {tab === 'timeline' && (
        <View style={styles.section}>
          {timeline.map((t: any, i: number) => (
            <View key={t.id} style={styles.timelineItem}>
              <View style={styles.timelineDot} />
              {i < timeline.length - 1 && <View style={styles.timelineLine} />}
              <View style={styles.timelineContent}>
                <Text style={styles.timelineDesc}>{t.description}</Text>
                <Text style={styles.timelineTime}>{format(new Date(t.created_at), 'MMM d, HH:mm')}</Text>
              </View>
            </View>
          ))}
          {timeline.length === 0 && <Text style={styles.emptyText}>No timeline entries</Text>}
        </View>
      )}

      <View style={{height: 32}} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:       {flex: 1, backgroundColor: theme.colors.bg},
  centered:        {flex: 1, alignItems: 'center', justifyContent: 'center'},
  headerCard:      {margin: theme.spacing.md, backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.xl, padding: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.border},
  headerTop:       {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8},
  caseNum:         {fontSize: theme.font.xs, color: theme.colors.textMuted, fontFamily: 'monospace', fontWeight: '700'},
  badges:          {flexDirection: 'row', gap: 6},
  badge:           {paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, borderWidth: 1},
  badgeText:       {fontSize: 10, fontWeight: '800', textTransform: 'uppercase'},
  caseTitle:       {fontSize: theme.font.md, fontWeight: '700', color: theme.colors.textPrimary, marginBottom: 8},
  caseMessage:     {fontSize: theme.font.base, color: theme.colors.textSecondary, lineHeight: 22, marginBottom: theme.spacing.md},
  metaGrid:        {flexDirection: 'row', flexWrap: 'wrap', gap: 12},
  metaItem:        {minWidth: '45%'},
  metaLabel:       {fontSize: theme.font.xs, color: theme.colors.textMuted, marginBottom: 2},
  metaValue:       {fontSize: theme.font.sm, color: theme.colors.textPrimary, fontWeight: '600', textTransform: 'capitalize'},
  actionsRow:      {flexDirection: 'row', gap: 8, paddingHorizontal: theme.spacing.md, marginBottom: theme.spacing.md},
  actionBtn:       {flex: 1, paddingVertical: 10, borderRadius: theme.radius.md, alignItems: 'center'},
  resolveBtn:      {backgroundColor: theme.colors.success},
  resolveBtnText:  {color: '#fff', fontWeight: '700', fontSize: theme.font.sm},
  escalateBtn:     {backgroundColor: theme.colors.warning + '33', borderWidth: 1, borderColor: theme.colors.warning + '88'},
  escalateBtnText: {color: theme.colors.warning, fontWeight: '700', fontSize: theme.font.sm},
  closeBtn:        {backgroundColor: theme.colors.bgCardAlt, borderWidth: 1, borderColor: theme.colors.border},
  closeBtnText:    {color: theme.colors.textSecondary, fontWeight: '600', fontSize: theme.font.sm},
  aiCard:          {margin: theme.spacing.md, marginTop: 0, backgroundColor: '#3730a333', borderRadius: theme.radius.xl, padding: theme.spacing.md, borderWidth: 1, borderColor: '#6366f133'},
  aiTitle:         {fontSize: theme.font.sm, fontWeight: '700', color: theme.colors.primaryLight, marginBottom: theme.spacing.sm},
  aiGrid:          {flexDirection: 'row', flexWrap: 'wrap', gap: 12},
  aiItem:          {minWidth: '45%'},
  aiLabel:         {fontSize: theme.font.xs, color: theme.colors.textMuted, marginBottom: 2},
  aiValue:         {fontSize: theme.font.sm, color: theme.colors.textPrimary, fontWeight: '600', textTransform: 'capitalize'},
  tabRow:          {flexDirection: 'row', paddingHorizontal: theme.spacing.md, gap: 8, marginBottom: theme.spacing.sm},
  tab:             {paddingHorizontal: 16, paddingVertical: 8, borderRadius: theme.radius.md, backgroundColor: theme.colors.bgCard, borderWidth: 1, borderColor: theme.colors.border},
  tabActive:       {backgroundColor: theme.colors.primary + '33', borderColor: theme.colors.primary},
  tabText:         {fontSize: theme.font.sm, color: theme.colors.textSecondary, fontWeight: '600'},
  tabTextActive:   {color: theme.colors.primary},
  section:         {paddingHorizontal: theme.spacing.md, gap: 8},
  noteCard:        {backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.md, padding: theme.spacing.md, borderWidth: 1, borderColor: theme.colors.border},
  internalNote:    {borderColor: '#92400e66', backgroundColor: '#78350f11'},
  noteType:        {fontSize: theme.font.xs, color: theme.colors.textMuted, marginBottom: 4},
  noteContent:     {fontSize: theme.font.base, color: theme.colors.textPrimary, lineHeight: 20},
  noteTime:        {fontSize: theme.font.xs, color: theme.colors.textMuted, marginTop: 4},
  addNoteRow:      {marginTop: theme.spacing.sm},
  noteTypeToggle:  {flexDirection: 'row', gap: 8, marginBottom: 8},
  toggleBtn:       {paddingHorizontal: 12, paddingVertical: 6, borderRadius: theme.radius.sm, backgroundColor: theme.colors.bgCard, borderWidth: 1, borderColor: theme.colors.border},
  toggleBtnActive: {backgroundColor: theme.colors.primary + '33', borderColor: theme.colors.primary},
  toggleText:      {fontSize: theme.font.xs, color: theme.colors.textSecondary, fontWeight: '600'},
  toggleTextActive:{color: theme.colors.primary},
  noteInputRow:    {flexDirection: 'row', gap: 8},
  noteInput:       {flex: 1, backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.border, color: theme.colors.textPrimary, padding: theme.spacing.md, fontSize: theme.font.base, minHeight: 60},
  sendBtn:         {backgroundColor: theme.colors.primary, borderRadius: theme.radius.md, paddingHorizontal: theme.spacing.md, justifyContent: 'center'},
  sendBtnDisabled: {opacity: 0.5},
  sendBtnText:     {color: '#fff', fontWeight: '700', fontSize: theme.font.sm},
  timelineItem:    {flexDirection: 'row', gap: 12, position: 'relative', paddingLeft: 12},
  timelineDot:     {width: 10, height: 10, borderRadius: 5, backgroundColor: theme.colors.primary, marginTop: 4, flexShrink: 0},
  timelineLine:    {position: 'absolute', left: 16, top: 14, bottom: -8, width: 1, backgroundColor: theme.colors.border},
  timelineContent: {flex: 1, paddingBottom: theme.spacing.md},
  timelineDesc:    {fontSize: theme.font.sm, color: theme.colors.textPrimary},
  timelineTime:    {fontSize: theme.font.xs, color: theme.colors.textMuted, marginTop: 2},
  emptyText:       {color: theme.colors.textMuted, fontSize: theme.font.base, textAlign: 'center', padding: 24},
});
