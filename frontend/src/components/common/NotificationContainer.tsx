import React, { useEffect } from 'react';
import { notification } from 'antd';
import { useAppSelector, useAppDispatch, RootState } from '@/store';
import { markNotificationAsRead } from '@/store/slices/uiSlice';
import { SystemNotification } from '@/types';

const NotificationContainer: React.FC = () => {
  const dispatch = useAppDispatch();
  const { notifications } = useAppSelector((state: RootState) => (state.ui as { notifications: SystemNotification[] }));
  const [api, contextHolder] = notification.useNotification();

  useEffect(() => {
    // 显示未读通知
    notifications
      .filter((notif: SystemNotification) => !notif.read)
      .forEach((notif: SystemNotification) => {
        // 确保 notif.type 是有效的通知类型
        const notificationType = notif.type as keyof typeof api;
        if (api[notificationType] && typeof api[notificationType] === 'function') {
          (api[notificationType] as Function)({
            message: notif.title,
            description: notif.message,
            duration: notif.type === 'error' ? 0 : 4.5,
            onClose: () => {
              dispatch(markNotificationAsRead(notif.id));
            },
          });
        }
      });
  }, [notifications, api, dispatch]);

  return contextHolder;
};

export default NotificationContainer;