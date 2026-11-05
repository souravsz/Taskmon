import { Text, View } from 'react-native';

import { tokens as tm } from '../../theme/tokens';

export function UserBubble({ text }: { text: string }) {
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
      <View
        style={{
          maxWidth: '82%',
          paddingVertical: 12,
          paddingHorizontal: 17,
          ...tm.radius.userBubble,
          backgroundColor: tm.color.ink,
        }}
      >
        <Text selectable style={{ fontFamily: tm.font.body[400], fontSize: 16, lineHeight: 23, color: tm.color.cream }}>
          {text}
        </Text>
      </View>
    </View>
  );
}
