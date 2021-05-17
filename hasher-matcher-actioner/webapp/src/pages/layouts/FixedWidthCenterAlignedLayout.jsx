/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import PropTypes from 'prop-types';
import {Container, Row, Col} from 'react-bootstrap';

/**
 * Uses a bootstrap container to put all content in the center of the main area.
 * Supports a title and any children.
 *
 * Does not provide rows and cols. That is for pages to provide.
 *
 * A page impl using this class would look like.
 *
 * ```
 * return (
 *   <FixedWidthCenterAlignedLayout title="Recipe Details">
 *     <Row>
 *       <Col>
 *         ... your content here.
 *       </Col>
 *     </Row>
 *   </FixedWidthCenterAlignedLayout>
 * )
 * ```
 *
 * Centralizing the layouts like this allows page authors to focus on the
 * page.
 */
export default function FixedWidthCenterAlignedLayout({title, children}) {
  return (
    <Container>
      <Row>
        <Col className="mt-4">
          <h1>{title}</h1>
        </Col>
      </Row>
      {children}
    </Container>
  );
}

FixedWidthCenterAlignedLayout.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.arrayOf(PropTypes.node),
};

FixedWidthCenterAlignedLayout.defaultProps = {
  children: [],
};
