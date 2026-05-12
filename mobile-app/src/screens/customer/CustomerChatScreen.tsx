import React, {useState, useRef, useEffect} from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import {chatbotApi} from '../../api';
import {useAuthStore} from '../../store/authStore';
import {theme} from '../../theme';
import {format} from 'date-fns';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  intent?: string;
  case_id?: string;
}

export default function CustomerChatScreen() {
  const {user} = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: "Hello! 👋 Welcome to Customer Support. How can I help you today?\n\nYou can ask me about orders, billing, account issues, or just describe your problem.",
    timestamp: new Date().toISOString(),
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState('idle');
  const listRef = useRef<FlatList>(null);

  useEffect(() => {
    listRef.current?.scrollToEnd({animated: true});
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput('');

    const userMsg: Message = {role: 'user', content: text, timestamp: new Date().toISOString()};
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const {data} = await chatbotApi.sendMessage(sessionId, text, user?.id);
      if (!sessionId) setSessionId(data.session_id);
      setState(data.state);

      const botMsg: Message = {
        role: 'assistant',
        content: data.reply,
        timestamp: new Date().toISOString(),
        intent: data.intent,
        case_id: data.case_id,
      };

      if (data.action === 'create_case' && data.case_id) {
        const sysMsg: Message = {
          role: 'system',
          content: `✅ Case created: ${data.case_id?.slice(0, 8)}...`,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, botMsg, sysMsg]);
      } else {
        setMessages(prev => [...prev, botMsg]);
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'system',
        content: '⚠️ Something went wrong. Please try again.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const SUGGESTIONS = ['Reset my password', 'Track my order', 'Request a refund', 'Speak to an agent'];

  const renderItem = ({item}: {item: Message}) => {
    const isUser = item.role === 'user';
    const isSystem = item.role === 'system';
    return (
      <View style={[styles.messageRow, isUser ? styles.messageRowRight : styles.messageRowLeft]}>
        {!isUser && (
          <View style={[styles.avatar, isSystem ? styles.avatarSystem : styles.avatarBot]}>
            <Text style={styles.avatarText}>{isSystem ? '🎫' : '🤖'}</Text>
          </View>
        )}
        <View style={[
          styles.bubble,
          isUser ? styles.bubbleUser : isSystem ? styles.bubbleSystem : styles.bubbleBot,
        ]}>
          <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>{item.content}</Text>
          <Text style={styles.bubbleTime}>{format(new Date(item.timestamp), 'HH:mm')}</Text>
          {item.intent && !isSystem && (
            <Text style={styles.intentTag}>· {item.intent}</Text>
          )}
        </View>
        {isUser && (
          <View style={styles.avatarUser}>
            <Text style={styles.avatarText}>{user?.full_name?.[0] || '?'}</Text>
          </View>
        )}
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}>

      {/* Status */}
      <View style={styles.statusBar}>
        <View style={[styles.statusDot, {backgroundColor: state === 'idle' ? theme.colors.success : theme.colors.warning}]}/>
        <Text style={styles.statusText}>
          {state === 'idle' ? 'Connected' : state}
        </Text>
        {sessionId && <Text style={styles.sessionId}>{sessionId.slice(0, 8)}...</Text>}
      </View>

      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderItem}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => listRef.current?.scrollToEnd({animated: true})}
      />

      {/* Typing indicator */}
      {loading && (
        <View style={styles.typingRow}>
          <ActivityIndicator size="small" color={theme.colors.primary}/>
          <Text style={styles.typingText}> Typing...</Text>
        </View>
      )}

      {/* Suggestions (only at start) */}
      {messages.length === 1 && (
        <View style={styles.suggestions}>
          {SUGGESTIONS.map(s => (
            <TouchableOpacity key={s} style={styles.suggestion} onPress={() => setInput(s)}>
              <Text style={styles.suggestionText}>{s}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Input bar */}
      <View style={styles.inputBar}>
        <TextInput
          testID="chat-input"
          style={styles.chatInput}
          placeholder="Type a message..."
          placeholderTextColor={theme.colors.textMuted}
          value={input}
          onChangeText={setInput}
          onSubmitEditing={send}
          returnKeyType="send"
          editable={state !== 'escalated' && state !== 'resolved'}
        />
        <TouchableOpacity
          testID="chat-send-btn"
          style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnDisabled]}
          onPress={send}
          disabled={!input.trim() || loading}>
          <Text style={styles.sendIcon}>➤</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container:        {flex: 1, backgroundColor: theme.colors.bg},
  statusBar:        {flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: theme.spacing.md, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: theme.colors.border, backgroundColor: theme.colors.bgCard},
  statusDot:        {width: 8, height: 8, borderRadius: 4},
  statusText:       {fontSize: theme.font.xs, color: theme.colors.textSecondary, fontWeight: '600'},
  sessionId:        {fontSize: 10, color: theme.colors.textMuted, fontFamily: 'monospace', marginLeft: 'auto'},
  messageList:      {padding: theme.spacing.md, gap: 12},
  messageRow:       {flexDirection: 'row', alignItems: 'flex-end', gap: 8},
  messageRowLeft:   {justifyContent: 'flex-start'},
  messageRowRight:  {justifyContent: 'flex-end'},
  avatar:           {width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', flexShrink: 0},
  avatarBot:        {backgroundColor: '#065f46'},
  avatarSystem:     {backgroundColor: theme.colors.bgCardAlt},
  avatarUser:       {width: 32, height: 32, borderRadius: 16, backgroundColor: theme.colors.primary, alignItems: 'center', justifyContent: 'center', flexShrink: 0},
  avatarText:       {fontSize: 16},
  bubble:           {maxWidth: '75%', borderRadius: 16, padding: 12},
  bubbleBot:        {backgroundColor: theme.colors.bgCard, borderTopLeftRadius: 4, borderWidth: 1, borderColor: theme.colors.border},
  bubbleSystem:     {backgroundColor: theme.colors.bgCardAlt, borderRadius: 8, borderWidth: 1, borderColor: theme.colors.border},
  bubbleUser:       {backgroundColor: theme.colors.primary, borderTopRightRadius: 4},
  bubbleText:       {fontSize: theme.font.base, color: theme.colors.textPrimary, lineHeight: 20},
  bubbleTextUser:   {color: '#fff'},
  bubbleTime:       {fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 4},
  intentTag:        {fontSize: 10, color: theme.colors.textMuted, marginTop: 2},
  typingRow:        {flexDirection: 'row', alignItems: 'center', paddingHorizontal: theme.spacing.lg, paddingBottom: 4},
  typingText:       {fontSize: theme.font.sm, color: theme.colors.textMuted},
  suggestions:      {flexDirection: 'row', flexWrap: 'wrap', padding: theme.spacing.sm, gap: 8},
  suggestion:       {paddingHorizontal: 12, paddingVertical: 6, backgroundColor: theme.colors.bgCard, borderRadius: theme.radius.full, borderWidth: 1, borderColor: theme.colors.border},
  suggestionText:   {fontSize: theme.font.sm, color: theme.colors.textSecondary},
  inputBar:         {flexDirection: 'row', gap: 8, padding: theme.spacing.md, borderTopWidth: 1, borderTopColor: theme.colors.border, backgroundColor: theme.colors.bgCard},
  chatInput:        {flex: 1, backgroundColor: theme.colors.bgCardAlt, borderRadius: theme.radius.full, borderWidth: 1, borderColor: theme.colors.border, color: theme.colors.textPrimary, paddingHorizontal: theme.spacing.md, paddingVertical: 10, fontSize: theme.font.base},
  sendBtn:          {width: 44, height: 44, borderRadius: 22, backgroundColor: theme.colors.primary, alignItems: 'center', justifyContent: 'center'},
  sendBtnDisabled:  {opacity: 0.4},
  sendIcon:         {color: '#fff', fontSize: 16},
});
