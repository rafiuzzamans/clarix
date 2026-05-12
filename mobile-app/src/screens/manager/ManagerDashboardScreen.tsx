import React, {useEffect, useState} from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  ActivityIndicator, RefreshControl,
} from 'react-native';
import {analyticsApi} from '../../api';
import {theme} from '../../theme';
import {BarChart, LineChart, PieChart} from 'react-native-chart-kit';
import {Dimensions} from 'react-native';

const {width} = Dimensions.get('window');
const CHART_W = width - 32;

const chartConfig = {
  backgroundColor: theme.colors.bgCard,
  backgroundGradientFrom: theme.colors.bgCard,
  backgroundGradientTo: theme.colors.bgCard,
  decimalPlaces: 0,
  color: (opacity = 1) => `rgba(99, 102, 241, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(148, 163, 184, ${opacity})`,
  style: {borderRadius: 12},
  propsForDots: {r: '4', strokeWidth: '2', stroke: '#6366f1'},
};

export default function ManagerDashboardScreen() {
  const [overview, setOverview]   = useState<any>(null);
  const [agents, setAgents]       = useState<any[]>([]);
  const [sla, setSla]             = useState<any>(null);
  const [priority, setPriority]   = useState<any[]>([]);
  const [volumeData, setVolumeData] = useState<any>(null);
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const [ov, ag, sl, pri, vol] = await Promise.all([
        analyticsApi.overview(),
        analyticsApi.agentPerformance(),
        analyticsApi.slaCompliance(),
        analyticsApi.priorityBreakdown(),
        analyticsApi.caseVolume(7),
      ]);
      setOverview(ov.data);
      setAgents(ag.data?.data ?? []);
      setSla(sl.data);
      setPriority(pri.data?.data ?? []);

      // Format for chart
      const volItems = vol.data?.data ?? [];
      if (volItems.length > 0) {
        setVolumeData({
          labels: volItems.map((d: any) => {
            const dt = new Date(d.day);
            return `${dt.getMonth() + 1}/${dt.getDate()}`;
          }),
          datasets: [{data: volItems.map((d: any) => d.total || 0)}],
        });
      }
    } catch (e) {console.error(e);}
    finally {setLoading(false); setRefreshing(false);}
  };

  useEffect(() => {load();}, []);

  const onRefresh = () => {setRefreshing(true); load();};

  const statCards = overview ? [
    {label: 'Open Cases',    value: overview.open_cases,      color: theme.colors.primary},
    {label: 'Resolved',      value: overview.resolved_cases,  color: theme.colors.success},
    {label: 'Escalated',     value: overview.escalated_cases, color: theme.colors.warning},
    {label: 'Urgent',        value: overview.urgent_cases,    color: theme.colors.danger},
    {label: 'Today',         value: overview.cases_today,     color: theme.colors.info},
    {label: 'Avg. Res. (h)', value: overview.avg_resolution_hours ?? '—', color: theme.colors.secondary},
  ] : [];

  const pieData = priority.map((p: any, i: number) => ({
    name: p.priority,
    population: p.total,
    color: [theme.colors.danger, theme.colors.warning, theme.colors.primary, theme.colors.success][i] || '#888',
    legendFontColor: theme.colors.textSecondary,
    legendFontSize: 11,
  }));

  if (loading) {
    return <View style={styles.centered}><ActivityIndicator color={theme.colors.primary} size="large"/></View>;
  }

  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary}/>}>

      {/* KPI grid */}
      <View style={styles.kpiGrid}>
        {statCards.map(({label, value, color}) => (
          <View key={label} style={styles.kpiCard}>
            <View style={[styles.kpiDot, {backgroundColor: color}]}/>
            <Text style={styles.kpiValue}>{value}</Text>
            <Text style={styles.kpiLabel}>{label}</Text>
          </View>
        ))}
      </View>

      {/* SLA Compliance */}
      {sla && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🛡 SLA Compliance</Text>
          <View style={styles.slaRow}>
            {[
              {label: 'Total',     value: sla.total,         color: theme.colors.textPrimary},
              {label: 'Within',    value: sla.within_sla,    color: theme.colors.success},
              {label: 'Breached',  value: sla.breached_sla,  color: theme.colors.danger},
              {label: 'Rate',      value: sla.compliance_pct ? `${sla.compliance_pct}%` : '—', color: theme.colors.primary},
            ].map(({label, value, color}) => (
              <View key={label} style={styles.slaCard}>
                <Text style={[styles.slaValue, {color}]}>{value}</Text>
                <Text style={styles.slaLabel}>{label}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Volume line chart */}
      {volumeData && volumeData.labels.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📈 Case Volume (7 Days)</Text>
          <LineChart
            data={volumeData}
            width={CHART_W}
            height={180}
            chartConfig={chartConfig}
            bezier
            style={styles.chart}
          />
        </View>
      )}

      {/* Priority pie */}
      {pieData.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🎯 Priority Breakdown</Text>
          <PieChart
            data={pieData}
            width={CHART_W}
            height={180}
            chartConfig={chartConfig}
            accessor="population"
            backgroundColor="transparent"
            paddingLeft="10"
          />
        </View>
      )}

      {/* Agent performance table */}
      {agents.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>👥 Agent Performance</Text>
          <View style={styles.agentTable}>
            <View style={styles.agentHeaderRow}>
              {['Agent', 'Assigned', 'Resolved', 'Avg (h)'].map(h => (
                <Text key={h} style={styles.agentHeader}>{h}</Text>
              ))}
            </View>
            {agents.map((a: any) => (
              <View key={a.agent_id} style={styles.agentRow}>
                <Text style={[styles.agentCell, {flex: 1.5, color: theme.colors.textPrimary}]} numberOfLines={1}>
                  {a.full_name?.split(' ')[0]}
                </Text>
                <Text style={styles.agentCell}>{a.assigned_cases}</Text>
                <Text style={[styles.agentCell, {color: theme.colors.success}]}>{a.resolved_cases}</Text>
                <Text style={styles.agentCell}>{a.avg_resolution_hours ?? '—'}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      <View style={{height: 32}}/>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:     {flex: 1, backgroundColor: theme.colors.bg},
  centered:      {flex: 1, alignItems: 'center', justifyContent: 'center'},
  kpiGrid:       {flexDirection: 'row', flexWrap: 'wrap', padding: 8, gap: 0},
  kpiCard:       {
    width: '33.3%', padding: 12,
    backgroundColor: theme.colors.bgCard,
    borderWidth: 0.5, borderColor: theme.colors.border,
    alignItems: 'center',
  },
  kpiDot:        {width: 8, height: 8, borderRadius: 4, marginBottom: 4},
  kpiValue:      {fontSize: theme.font.xl, fontWeight: '800', color: theme.colors.textPrimary},
  kpiLabel:      {fontSize: 10, color: theme.colors.textMuted, textAlign: 'center', marginTop: 2},
  section:       {padding: theme.spacing.md},
  sectionTitle:  {fontSize: theme.font.base, fontWeight: '700', color: theme.colors.textPrimary, marginBottom: theme.spacing.sm},
  chart:         {borderRadius: theme.radius.md},
  slaRow:        {flexDirection: 'row', gap: 8},
  slaCard:       {flex: 1, backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.md, padding: 12, borderWidth: 1, borderColor: theme.colors.border, alignItems: 'center'},
  slaValue:      {fontSize: theme.font.xl, fontWeight: '800'},
  slaLabel:      {fontSize: theme.font.xs, color: theme.colors.textMuted, marginTop: 2},
  agentTable:    {backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.md, borderWidth: 1, borderColor: theme.colors.border, overflow: 'hidden'},
  agentHeaderRow:{flexDirection: 'row', backgroundColor: theme.colors.bgCardAlt, paddingVertical: 8, paddingHorizontal: 12},
  agentHeader:   {flex: 1, fontSize: 10, color: theme.colors.textMuted, fontWeight: '700', textTransform: 'uppercase'},
  agentRow:      {flexDirection: 'row', paddingVertical: 10, paddingHorizontal: 12, borderTopWidth: 1, borderTopColor: theme.colors.border},
  agentCell:     {flex: 1, fontSize: theme.font.sm, color: theme.colors.textSecondary},
});
