/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect, useCallback, CSSProperties} from 'react';
import {Popover, OverlayTrigger, PopoverProps} from 'react-bootstrap';
import copy from 'clipboard-copy';

type CopyableFieldProps = {
  tooltip: string;
  text: string;
};

type CopyableFieldPropsWithColor = CopyableFieldProps & {
  color?: string;
};

export function CopyableTextField({
  text,
  tooltip,
  color,
}: CopyableFieldPropsWithColor) {
  const helpText = tooltip ?? 'Copy to clipboard?';
  const [message, setMessage] = useState(helpText);

  const copyText = useCallback(() => {
    copy(text).then(() => setMessage('Copied!'));
    setTimeout(() => {
      setMessage(helpText);
    }, 1000);
  }, [text]);

  const linkButtonStyle: CSSProperties = {
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    display: 'inline',
    margin: 0,
    padding: 0,
    color: color ?? 'black',
    whiteSpace: 'nowrap',
    maxWidth: '250px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  };

  return (
    <OverlayTrigger
      delay={{show: 250, hide: 250}}
      trigger={['hover', 'focus']}
      // @BarrettOlson. UpdatingPopover is really, really hard to type in
      // typescript. Let's discuss what it was helping with and if it is
      // necessary.
      overlay={<Popover id="copy-me">{message}</Popover>}>
      <button
        type="button"
        role="link"
        style={linkButtonStyle}
        onClick={copyText}
        tabIndex={0}>
        {text}
      </button>
    </OverlayTrigger>
  );
}

CopyableTextField.defaultProps = {
  color: undefined,
};

export function CopyableHashField({
  text,
  tooltip = 'Copy hash to clipboard?',
}: CopyableFieldProps) {
  return (
    <td style={{maxWidth: '250px', overflow: 'hidden'}}>
      <span style={{overflow: 'hidden'}} />
      <CopyableTextField text={text} tooltip={tooltip} />
    </td>
  );
}
