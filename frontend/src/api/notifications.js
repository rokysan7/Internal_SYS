import client from './client';

/** 알림 목록 조회 (user_id, unread_only 필터 지원) */
export const getNotifications = (params = {}) =>
  client.get('/notifications', { params });

/** 알림 읽음 처리 */
export const markAsRead = (notificationId) =>
  client.patch(`/notifications/${notificationId}/read`);
