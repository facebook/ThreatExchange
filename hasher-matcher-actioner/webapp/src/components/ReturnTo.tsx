/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {Button} from 'react-bootstrap';
import {useHistory, Link} from 'react-router-dom';

type ReturnToProps = {
  to?: string;
  children?: string | JSX.Element[];
};

/**
 * A utility control that returns you to a page. Can either go back in history
 * or to a specified page. Automatically provides the ← arrow.
 */
export default function ReturnTo({to, children}: ReturnToProps): JSX.Element {
  const history = useHistory();

  const fullText =
    children === undefined || children.length === 0 ? 'Back' : children;

  if (to) {
    return <Link to={to}>&larr; {fullText}</Link>;
  }
  return (
    <Button variant="link" onClick={() => history.goBack()}>
      &larr; {fullText}
    </Button>
  );
}

ReturnTo.defaultProps = {
  to: undefined,
  children: [],
};
