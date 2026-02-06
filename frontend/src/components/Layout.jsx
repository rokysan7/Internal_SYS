import { useEffect, useState, useRef, useCallback } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getNotifications, markAsRead } from '../api/notifications';
import { subscribePush, unsubscribePush, getPushSubscription } from '../api/push';
import { ROLES } from '../constants/roles';
import './Layout.css';

const POLL_INTERVAL = 30_000; // 30초 주기 fetch
const NOTIFICATION_TITLE = 'CS Dashboard';

/** 폴링으로 감지한 새 알림을 OS 알림으로 표시 (FCM 미전달 대비 fallback) */
function showOSNotification(notification) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;

  const title = NOTIFICATION_TITLE;
  const options = {
    body: notification.message,
    icon: '/favicon.ico',
    tag: `notif-${notification.id}`,
    data: { case_id: notification.case_id },
  };

  if (navigator.serviceWorker?.controller) {
    navigator.serviceWorker.ready.then((reg) => {
      reg.showNotification(title, options);
    });
  } else {
    new Notification(title, options);
  }
}

function formatTime(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now - d;
  if (diff < 60_000) return '방금 전';
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)}분 전`;
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)}시간 전`;
  return d.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function typeLabel(type) {
  switch (type) {
    case 'ASSIGNEE': return 'assignee';
    case 'REMINDER': return 'reminder';
    case 'COMMENT': return 'comment';
    default: return '';
  }
}

export default function Layout() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [panelOpen, setPanelOpen] = useState(false);
  const [pushEnabled, setPushEnabled] = useState(false);
  const [pushPermission, setPushPermission] = useState(
    'Notification' in window ? Notification.permission : 'unsupported'
  );
  const wrapperRef = useRef(null);
  const seenIdsRef = useRef(new Set());

  const fetchNotifications = useCallback(async () => {
    if (!user?.id) return;
    try {
      const res = await getNotifications({ user_id: user.id, unread_only: false });
      const data = res.data;

      // 첫 로드 시 기존 ID를 모두 seen 처리 (페이지 새로고침 시 중복 알림 방지)
      if (seenIdsRef.current.size === 0) {
        data.forEach((n) => seenIdsRef.current.add(n.id));
      } else {
        // 새로 등장한 미읽은 알림 → OS 알림 표시
        data.forEach((n) => {
          if (!n.is_read && !seenIdsRef.current.has(n.id)) {
            showOSNotification(n);
          }
          seenIdsRef.current.add(n.id);
        });
      }

      setNotifications(data);
    } catch {
      // 실패 시 무시 — 백그라운드 폴링이므로
    }
  }, [user?.id]);

  // Push 구독 상태 초기화
  useEffect(() => {
    getPushSubscription().then((sub) => setPushEnabled(!!sub)).catch(() => {});
  }, []);

  const handleTogglePush = useCallback(async () => {
    try {
      if (pushEnabled) {
        await unsubscribePush();
        setPushEnabled(false);
      } else {
        await subscribePush();
        setPushEnabled(true);
        setPushPermission('granted');
      }
    } catch {
      setPushPermission(Notification.permission);
      if (Notification.permission === 'denied') {
        alert('알림이 차단되어 있습니다. 브라우저 설정에서 알림을 허용해주세요.');
      }
    }
  }, [pushEnabled]);

  // 초기 로드 + 주기적 폴링
  useEffect(() => {
    fetchNotifications();
    const timer = setInterval(fetchNotifications, POLL_INTERVAL);
    return () => clearInterval(timer);
  }, [fetchNotifications]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleMarkRead = async (notification) => {
    if (notification.is_read) return;
    try {
      await markAsRead(notification.id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n))
      );
    } catch {
      // 무시
    }
  };

  const handleClickNotification = (notification) => {
    handleMarkRead(notification);
    if (notification.case_id) {
      setPanelOpen(false);
      navigate(`/cases/${notification.case_id}`);
    }
  };

  const handleMarkAllRead = async () => {
    const unread = notifications.filter((n) => !n.is_read);
    try {
      await Promise.all(unread.map((n) => markAsRead(n.id)));
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // 무시
    }
  };

  return (
    <div className="layout">
      {/* 사이드바 */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>CS Dashboard</h2>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end>
            <span className="nav-icon">📊</span>
            Dashboard
          </NavLink>
          <NavLink to="/cases">
            <span className="nav-icon">📋</span>
            CS Cases
          </NavLink>
          <NavLink to="/products">
            <span className="nav-icon">📦</span>
            Products
          </NavLink>
          {user?.role === ROLES.ADMIN && (
            <>
              <div className="nav-divider" />
              <NavLink to="/admin/users">
                <span className="nav-icon">👥</span>
                User Management
              </NavLink>
            </>
          )}
        </nav>
      </aside>

      {/* 메인 콘텐츠 영역 */}
      <div className="main-wrapper">
        <header className="topbar">
          <div className="topbar-title">CS Case Management</div>
          <div className="topbar-actions">
            {'Notification' in window && pushPermission !== 'unsupported' && (
              <button
                className={`push-toggle-btn ${pushEnabled ? 'active' : ''}`}
                onClick={handleTogglePush}
                title={
                  pushPermission === 'denied'
                    ? '알림 차단됨 — 브라우저 설정에서 허용 필요'
                    : pushEnabled
                      ? '푸시 알림 끄기'
                      : '푸시 알림 켜기'
                }
                aria-label={pushEnabled ? '푸시 알림 비활성화' : '푸시 알림 활성화'}
              >
                {pushPermission === 'denied' ? '🔇' : pushEnabled ? '🔊' : '🔈'}
              </button>
            )}
            <div className="notification-wrapper" ref={wrapperRef}>
              <button
                className="notification-btn"
                title="알림"
                onClick={() => setPanelOpen((prev) => !prev)}
              >
                🔔
                {unreadCount > 0 && (
                  <span className="notification-badge">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>

              {panelOpen && (
                <>
                  <div
                    className="notification-overlay"
                    onClick={() => setPanelOpen(false)}
                  />
                  <div className="notification-panel">
                    <div className="notification-panel-header">
                      <h3>알림 {unreadCount > 0 && `(${unreadCount})`}</h3>
                      {unreadCount > 0 && (
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={handleMarkAllRead}
                        >
                          모두 읽음
                        </button>
                      )}
                    </div>
                    <div className="notification-panel-body">
                      {notifications.length === 0 ? (
                        <div className="notification-empty">알림이 없습니다.</div>
                      ) : (
                        notifications.map((n) => (
                          <div
                            key={n.id}
                            className={`notification-item ${n.is_read ? '' : 'unread'}`}
                            onClick={() => handleClickNotification(n)}
                          >
                            <span
                              className={`notification-dot ${n.is_read ? 'read' : 'unread'}`}
                            />
                            <div className="notification-body">
                              <div className="notification-message">{n.message}</div>
                              <div className="notification-meta">
                                <span
                                  className={`notification-type-tag ${typeLabel(n.type)}`}
                                >
                                  {typeLabel(n.type)}
                                </span>
                                <span>{formatTime(n.created_at)}</span>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
            <div className="user-info">
              <span className="user-name">{user?.name || 'User'}</span>
              <span className="user-role">{user?.role || ''}</span>
            </div>
            <button className="logout-btn" onClick={logout} title="Logout">
              🚪
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
