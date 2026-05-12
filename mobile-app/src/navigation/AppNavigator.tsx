import React from 'react';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {useAuthStore} from '../store/authStore';

// Screens
import LoginScreen from '../screens/auth/LoginScreen';
import CaseQueueScreen from '../screens/agent/CaseQueueScreen';
import CaseDetailScreen from '../screens/agent/CaseDetailScreen';
import ManagerDashboardScreen from '../screens/manager/ManagerDashboardScreen';
import CustomerChatScreen from '../screens/customer/CustomerChatScreen';
import ProfileScreen from '../screens/shared/ProfileScreen';
import {theme} from '../theme';
import {View, Text} from 'react-native';

const Stack = createNativeStackNavigator();
const Tab   = createBottomTabNavigator();

function TabIcon({name, focused}: {name: string; focused: boolean}) {
  const icons: Record<string, string> = {
    Cases: '🎫', Dashboard: '📊', Chat: '💬', Profile: '👤',
  };
  return (
    <Text style={{fontSize: 20, opacity: focused ? 1 : 0.5}}>{icons[name] || '📱'}</Text>
  );
}

// Agent tabs
function AgentTabs() {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: theme.colors.bgCard,
          borderTopColor: theme.colors.border,
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textMuted,
        tabBarIcon: ({focused}) => <TabIcon name={route.name} focused={focused}/>,
      })}>
      <Tab.Screen name="Cases" component={AgentCasesStack}/>
      <Tab.Screen name="Profile" component={ProfileScreen}/>
    </Tab.Navigator>
  );
}

function AgentCasesStack() {
  return (
    <Stack.Navigator screenOptions={{
      headerStyle: {backgroundColor: theme.colors.bgCard},
      headerTintColor: theme.colors.textPrimary,
      headerTitleStyle: {fontWeight: '700'},
    }}>
      <Stack.Screen name="Queue" component={CaseQueueScreen} options={{title: 'Case Queue'}}/>
      <Stack.Screen name="CaseDetail" component={CaseDetailScreen} options={{title: 'Case Details'}}/>
    </Stack.Navigator>
  );
}

// Manager tabs
function ManagerTabs() {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        headerShown: false,
        tabBarStyle: {backgroundColor: theme.colors.bgCard, borderTopColor: theme.colors.border},
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textMuted,
        tabBarIcon: ({focused}) => <TabIcon name={route.name} focused={focused}/>,
      })}>
      <Tab.Screen name="Dashboard" component={ManagerDashboardScreen}
        options={{header: () => null}}/>
      <Tab.Screen name="Cases" component={AgentCasesStack}/>
      <Tab.Screen name="Profile" component={ProfileScreen}/>
    </Tab.Navigator>
  );
}

// Customer tabs
function CustomerTabs() {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        headerShown: false,
        tabBarStyle: {backgroundColor: theme.colors.bgCard, borderTopColor: theme.colors.border},
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textMuted,
        tabBarIcon: ({focused}) => <TabIcon name={route.name} focused={focused}/>,
      })}>
      <Tab.Screen name="Chat" component={CustomerChatScreen}
        options={{
          header: () => (
            <View style={{
              backgroundColor: theme.colors.bgCard, paddingTop: 44, paddingBottom: 12,
              paddingHorizontal: 20, borderBottomWidth: 1, borderBottomColor: theme.colors.border,
            }}>
              <Text style={{color: theme.colors.textPrimary, fontSize: 18, fontWeight: '700'}}>
                🤖 Support Chat
              </Text>
            </View>
          ),
          headerShown: true,
        }}/>
      <Tab.Screen name="Cases" component={AgentCasesStack}/>
      <Tab.Screen name="Profile" component={ProfileScreen}/>
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const {user, loading} = useAuthStore();

  if (loading) return null; // splash

  if (!user || !['admin','manager','supervisor','agent','customer'].includes(user.role)) {
    return (
      <Stack.Navigator screenOptions={{headerShown: false}}>
        <Stack.Screen name="Login" component={LoginScreen}/>
      </Stack.Navigator>
    );
  }

  // Route by role
  const MainTabs = () => {
    if (user.role === 'customer') return <CustomerTabs/>;
    if (user.role === 'manager' || user.role === 'admin' || user.role === 'supervisor')
      return <ManagerTabs/>;
    return <AgentTabs/>;
  };

  return (
    <Stack.Navigator screenOptions={{headerShown: false}}>
      <Stack.Screen name="Main" component={MainTabs}/>
    </Stack.Navigator>
  );
}
