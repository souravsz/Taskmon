import { useRef, useState } from 'react';
import { Modal, Pressable, Text, useWindowDimensions, View, type HostInstance } from 'react-native';

import { tokens as tm } from '../../theme/tokens';

export const initialsOf = (name: string) =>
  name
    .split(/[\s_]+/)
    .filter(Boolean)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

interface ProfileAvatarProps {
  name: string;
  subtitle?: string | null;
  onLogout: () => void;
}

/** Initials button that opens a small menu (name, number, Log out) under it. */
export function ProfileAvatar({ name, subtitle, onLogout }: ProfileAvatarProps) {
  const { width } = useWindowDimensions();
  const buttonRef = useRef<HostInstance>(null);
  const [anchor, setAnchor] = useState<{ top: number; right: number } | null>(null);
  const open = Boolean(anchor);

  const openMenu = () =>
    buttonRef.current?.measureInWindow((x, y, w, h) => setAnchor({ top: y + h + 8, right: width - (x + w) }));

  return (
    <>
      <Pressable
        ref={buttonRef}
        accessibilityRole="button"
        accessibilityLabel="Profile"
        accessibilityState={{ expanded: open }}
        onPress={openMenu}
        style={({ pressed }) => ({
          width: 40,
          height: 40,
          borderRadius: 20,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: tm.color.profileBg,
          boxShadow:
            pressed || open
              ? `0px 0px 0px 2px ${tm.color.cream}, 0px 0px 0px 4px ${tm.color.violet}`
              : `0px 0px 0px 2px ${tm.color.cream}, 0px 0px 0px 3px ${tm.color.hairlineStrong}`,
        })}
      >
        <Text style={{ fontFamily: tm.font.body[700], fontSize: 14, color: tm.color.profileText }}>{initialsOf(name)}</Text>
      </Pressable>

      <Modal visible={open} transparent animationType="fade" statusBarTranslucent onRequestClose={() => setAnchor(null)}>
        <Pressable style={{ flex: 1 }} onPress={() => setAnchor(null)}>
          {anchor && (
            <View
              accessibilityRole="menu"
              style={{
                position: 'absolute',
                top: anchor.top,
                right: anchor.right,
                minWidth: 200,
                paddingVertical: 8,
                borderRadius: tm.radius.small,
                borderWidth: 1,
                borderColor: tm.color.hairline,
                backgroundColor: tm.color.surface,
                boxShadow: tm.shadow.inputBar,
              }}
            >
              <View style={{ paddingHorizontal: 16, paddingVertical: 8 }}>
                <Text style={{ fontFamily: tm.font.body[700], fontSize: 15, color: tm.color.ink }}>{name}</Text>
                {Boolean(subtitle) && <Text style={{ fontFamily: tm.font.body[400], fontSize: 13, color: tm.color.inkSoft }}>{subtitle}</Text>}
              </View>
              <View style={{ height: 1, marginVertical: 8, backgroundColor: tm.color.hairlineStrong }} />
              <Pressable
                accessibilityRole="menuitem"
                onPress={() => {
                  setAnchor(null);
                  onLogout();
                }}
                style={({ pressed }) => ({
                  minHeight: 48,
                  justifyContent: 'center',
                  paddingHorizontal: 16,
                  backgroundColor: pressed ? tm.color.tintHover : 'transparent',
                })}
              >
                <Text style={{ fontFamily: tm.font.body[600], fontSize: 14, color: tm.color.ink }}>Log out</Text>
              </Pressable>
            </View>
          )}
        </Pressable>
      </Modal>
    </>
  );
}
