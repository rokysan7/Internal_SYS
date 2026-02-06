import client from './client';

/**
 * URL-safe base64 문자열을 Uint8Array로 변환한다.
 * pushManager.subscribe()의 applicationServerKey에 필요.
 */
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) {
    arr[i] = raw.charCodeAt(i);
  }
  return arr;
}

/** 백엔드에서 VAPID 공개키를 가져온다. */
export async function getVapidPublicKey() {
  const res = await client.get('/push/vapid-public-key');
  return res.data.public_key;
}

/**
 * Push 알림을 구독한다.
 * 1) 알림 권한 요청
 * 2) SW 등록 확인
 * 3) pushManager.subscribe()
 * 4) 백엔드에 구독 정보 전송
 */
export async function subscribePush() {
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    throw new Error('Notification permission denied');
  }

  const registration = await navigator.serviceWorker.ready;
  const vapidKey = await getVapidPublicKey();

  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidKey),
  });

  const { endpoint } = subscription;
  const keys = subscription.toJSON().keys;

  await client.post('/push/subscribe', {
    endpoint,
    p256dh: keys.p256dh,
    auth: keys.auth,
  });

  return subscription;
}

/**
 * Push 알림 구독을 해제한다.
 * 1) SW에서 구독 해제
 * 2) 백엔드에 구독 삭제 요청
 */
export async function unsubscribePush() {
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();

  if (subscription) {
    const { endpoint } = subscription;
    await subscription.unsubscribe();
    await client.delete('/push/unsubscribe', { data: { endpoint } });
  }
}

/** 현재 Push 구독 상태를 확인한다. */
export async function getPushSubscription() {
  if (!('serviceWorker' in navigator)) return null;
  const registration = await navigator.serviceWorker.ready;
  return registration.pushManager.getSubscription();
}
