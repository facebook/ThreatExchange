/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import PropTypes from 'prop-types';
import {Container, Row, Col} from 'react-bootstrap';

/**
 * Usage is exactly the same as FixedWidthCenterAlignedLayout. Might be worth it
 * to abstract out common pieces at some point.
 *
 * Salient features:
 * - Full width beyond the sidebar
 * - The layout by itself does not do any scrolling, left for children to implement
 */
export default function FullWidthLocalScrollingLeftAlignedLayout({
  title,
  children,
}: {
  title: string;
  children: JSX.Element;
}): JSX.Element {
  return (
    <Container
      fluid
      className="d-flex flex-column justify-content-start align-items-stretch h-100 w-100 py-0">
      <Row className="full-width-header flex-grow-0">
        <Col className="mt-4">
          <h1>{title}</h1>
        </Col>
      </Row>
      <Row className="flex-grow-1">{children}</Row>
    </Container>
  );
}

FullWidthLocalScrollingLeftAlignedLayout.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.arrayOf(PropTypes.node),
};

FullWidthLocalScrollingLeftAlignedLayout.defaultProps = {
  children: [],
};
