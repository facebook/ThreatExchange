/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect, useCallback} from 'react';
import {Popover, OverlayTrigger} from 'react-bootstrap';
import copy from 'clipboard-copy';

function truncateString(input, maxLength = 25) {
  if (input == null) {
    return '';
  }
  if (input.length <= maxLength) {
    return input;
  }
  return `${input.substring(0, maxLength)}...`;
}

// eslint-disable-next-line react/prop-types
export function CopyableHashField({text, tooltip}) {
  return (
    <td style={{maxWidth: '250px', overflow: 'hidden'}}>
      <span style={{overflow: 'hidden'}} />
      <CopyableTextField
        text={text}
        tooltip={tooltip ?? 'Copy hash to clipboard?'}
      />
    </td>
  );
}

const UpdatingPopover = React.forwardRef(
  // eslint-disable-next-line react/prop-types
  ({popper, children, ...props}, ref) => {
    useEffect(() => {
      // eslint-disable-next-line react/prop-types
      popper.scheduleUpdate();
    }, [children, popper]);

    return (
      // eslint-disable-next-line react/jsx-props-no-spreading
      <Popover ref={ref} content {...props}>
        {children}
      </Popover>
    );
  },
);

// eslint-disable-next-line react/prop-types
export function CopyableTextField({text, tooltip}) {
  const helpText = tooltip ?? 'Copy to clipboard?';
  const [message, setMessage] = useState(helpText);

  const copyText = useCallback(() => {
    copy(text).then(setMessage('Copied!'));
    setTimeout(() => {
      setMessage(helpText);
    }, 1000);
  }, [text]);

  const linkButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    display: 'inline',
    margin: 0,
    padding: 0,
    hover: {},
    focus: {
      textDecoration: 'none',
    },
  };

  return (
    <OverlayTrigger
      delay={{show: 250}}
      type="hover"
      overlay={<UpdatingPopover>{message}</UpdatingPopover>}>
      <button
        type="button"
        role="link"
        style={linkButtonStyle}
        onClick={copyText}
        onKeyDown={e => {
          if (e.code === 'Enter') {
            copyText();
          }
        }}
        tabIndex={0}>
        {truncateString(text)}
      </button>
    </OverlayTrigger>
  );
}
