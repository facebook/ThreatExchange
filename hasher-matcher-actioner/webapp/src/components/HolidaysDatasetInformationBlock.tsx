/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState} from 'react';
import {Card, Button} from 'react-bootstrap';
import PropTypes from 'prop-types';
import {createDataset} from '../Api';

export const SAMPLE_PG_ID = 'inria-holidays-test';

/**
 * Super simple informational component. Drop in anywhere.
 */
type HolidaysDatasetInformationBlock = {
  samplePGExists: boolean;
  refresh: () => void;
};

export function HolidaysDatasetInformationBlock({
  samplePGExists,
  refresh,
}: HolidaysDatasetInformationBlock): JSX.Element {
  const [loading, setLoading] = useState(false);

  const createSampleDataPG = () => {
    createDataset(
      SAMPLE_PG_ID,
      'Holiday Sample Set',
      'Sample set of hashes from the file in open source',
    );
  };

  return (
    // <Card bg="light" body style={{maxWidth: '720px'}}>
    <>
      <h3>Test Photos</h3>
      <p>
        In addition to ThreatExchange data, HMA also comes with a set of image
        hashes baked in. The images are from a dataset called the INRIA Holidays
        dataset.
      </p>
      <ul>
        <li>
          Go to{' '}
          <a href="https://lear.inrialpes.fr/~jegou/data.php#holidays">
            this page
          </a>{' '}
          and find the link labeled <code>jpg1.tar.gz</code>. Any photo from
          that archive file will match in the HMA system.
        </li>
        <li>
          The matched photos will have a privacy group of{' '}
          <code>{SAMPLE_PG_ID}</code>.{' '}
          <Button
            variant="secondary"
            className="float-right"
            disabled={loading || samplePGExists}
            onClick={() => {
              setLoading(true);
              createSampleDataPG();
              setTimeout(() => {
                if (refresh) {
                  refresh();
                }
                setLoading(false);
              }, 1000);
            }}
            style={{marginLeft: 10}}>
            {samplePGExists ? 'Created' : 'Create'}
          </Button>
        </li>
      </ul>
    </>
  );
}

HolidaysDatasetInformationBlock.propTypes = {
  samplePGExists: PropTypes.bool,
  refresh: PropTypes.func,
};

HolidaysDatasetInformationBlock.defaultProps = {
  samplePGExists: false,
  refresh: null,
};
