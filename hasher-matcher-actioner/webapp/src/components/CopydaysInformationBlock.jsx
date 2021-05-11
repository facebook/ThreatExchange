/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React from 'react';
import {Card} from 'react-bootstrap';

/**
 * Super simple informational component. Drop in anywhere.
 */
export default function CopydaysInformationBlock() {
  return (
    <Card bg="light" body style={{maxWidth: '720px'}}>
      <h2>Test Photos</h2>
      <p>
        In addition to ThreatExchange data, HMA also comes with a set of image
        hashes baked in. The images are from a dataset called the Copydays
        dataset.
      </p>

      <ul>
        <li>
          Go to{' '}
          <a href="https://lear.inrialpes.fr/~jegou/data.php">this page</a> and
          find the link labeled <code>jpg1.tar.gz</code>. Any photo from that
          archive file will match in the HMA system.
        </li>
        <li>
          The matched photos will have a privacy group of{' '}
          <code>copydays-test</code>.
        </li>
      </ul>
    </Card>
  );
}
