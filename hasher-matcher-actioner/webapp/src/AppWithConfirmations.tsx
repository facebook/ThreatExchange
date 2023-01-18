/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {Button, Modal} from 'react-bootstrap';

type ConfirmationMessage = {
  message: string;
  ctaText: string;
  ctaVariant: 'primary' | 'success' | 'danger'; // Figure out how to refer to bootstrap variants
  onConfirm: () => void;
  onCancel: () => void;
};

type AppWithConfirmationsProps = {
  children: JSX.Element | JSX.Element[];
};

export const ConfirmationsContext = React.createContext({
  /* eslint-disable @typescript-eslint/no-empty-function */
  confirm: ({
    message,
    ctaText,
    ctaVariant,
    onConfirm,
    onCancel,
  }: ConfirmationMessage) => {},
  /* eslint-enable @typescript-eslint/no-empty-function */
});

export function AppWithConfirmations({children}: AppWithConfirmationsProps) {
  const [confirmation, setConfirmation] = useState<
    ConfirmationMessage | undefined
  >(undefined);

  const inAppConfirmations = {
    confirm: ({
      message,
      ctaText,
      ctaVariant,
      onConfirm,
      onCancel,
    }: ConfirmationMessage) => {
      setConfirmation({message, ctaText, ctaVariant, onConfirm, onCancel});
    },
  };

  const handleConfirm = () => {
    setConfirmation(undefined);
    confirmation?.onConfirm();
  };

  const handleCancel = () => {
    setConfirmation(undefined);
    confirmation?.onCancel();
  };

  return (
    <ConfirmationsContext.Provider value={inAppConfirmations}>
      {children}
      <Modal show={!!confirmation}>
        <Modal.Body>{confirmation?.message}</Modal.Body>
        <Modal.Footer>
          <Button onClick={handleConfirm} variant={confirmation?.ctaVariant}>
            {confirmation?.ctaText}
          </Button>
          <Button onClick={handleCancel} variant="light">
            Cancel
          </Button>
        </Modal.Footer>
      </Modal>
    </ConfirmationsContext.Provider>
  );
}
