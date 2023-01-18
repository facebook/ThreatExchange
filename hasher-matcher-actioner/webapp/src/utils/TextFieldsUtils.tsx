/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState, useCallback, CSSProperties} from 'react';
import {Popover, OverlayTrigger} from 'react-bootstrap';
import copy from 'clipboard-copy';

type CopyableFieldProps = {
  text: string;
  tooltip?: string;
};

type CopyableFieldPropsWithColor = CopyableFieldProps & {
  color?: string;
};
export function CopyableTextField({
  text,
  tooltip,
  color,
}: CopyableFieldPropsWithColor): JSX.Element {
  const helpText = tooltip;
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
      overlay={
        <Popover id="copy-me">
          <div className="p-2">{message}</div>
        </Popover>
      }>
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
  tooltip: 'Copy to clipboard?',
  color: undefined,
};

export function CopyableHashField({
  text,
  tooltip,
}: CopyableFieldProps): JSX.Element {
  return (
    <td style={{maxWidth: '250px', overflow: 'hidden'}}>
      <span style={{overflow: 'hidden'}} />
      <CopyableTextField text={text} tooltip={tooltip} />
    </td>
  );
}

CopyableHashField.defaultProps = {
  tooltip: 'Copy to clipboard?',
};
