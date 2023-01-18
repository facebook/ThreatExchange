/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {Toast} from 'react-bootstrap';

// How long to wait before
const AUTOHIDE_DELAY = 5000;

/**
 * If you decide to expand the set of arguments a notification needs, remember
 * to make them backwards compatible, or you'll need to update all callsites.
 */
type NotificationProps = {
  message: string;
  header?: string;
};

type ToastMessage = NotificationProps & {
  level: 'info' | 'success' | 'warn' | 'error';
  id: string;
};

type AppWithNotificationsProps = {
  children: JSX.Element | JSX.Element[];
};

export const NotificationsContext = React.createContext({
  /* eslint-disable @typescript-eslint/no-empty-function */
  info: ({message, header}: NotificationProps) => {},
  success: ({message, header}: NotificationProps) => {},
  warn: ({message, header}: NotificationProps) => {},
  error: ({message, header}: NotificationProps) => {},
  /* eslint-enable @typescript-eslint/no-empty-function */
});

let counter = 0;

export function AppWithNotifications({children}: AppWithNotificationsProps) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const appendToast = (toast: Omit<ToastMessage, 'id'>) => {
    // autoincrementing counter for toast ids.
    counter += 1;
    const id = `${counter}`;

    setToasts(toasts.concat([{...toast, id}]));
  };

  const inAppNotify = {
    info: ({message, header}: NotificationProps) => {
      appendToast({level: 'info', message, header});
    },
    success: ({message, header}: NotificationProps) => {
      appendToast({level: 'success', message, header});
    },
    warn: ({message, header}: NotificationProps) => {
      appendToast({level: 'warn', message, header});
    },
    error: ({message, header}: NotificationProps) => {
      appendToast({level: 'error', message, header});
    },
  };

  const removeToast = (id: string) => () => {
    setToasts(toasts.filter(x => x.id !== id));
  };

  return (
    <NotificationsContext.Provider value={inAppNotify}>
      {children}
      <div className="toast-container">
        {toasts &&
          toasts.map(toast => (
            <Toast
              key={toast.id}
              className={toast.level}
              autohide
              onClose={removeToast(toast.id)}
              delay={AUTOHIDE_DELAY}>
              {toast.header ? (
                <Toast.Header>{toast.header}</Toast.Header>
              ) : null}
              <Toast.Body>{toast.message}</Toast.Body>
            </Toast>
          ))}
      </div>
    </NotificationsContext.Provider>
  );
}
