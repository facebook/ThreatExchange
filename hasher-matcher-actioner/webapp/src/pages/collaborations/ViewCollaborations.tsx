/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState} from 'react';
import {Row, Col, Card, Button} from 'react-bootstrap';
import {generatePath, NavLink} from 'react-router-dom';
import {fetchAllCollabs} from '../../Api';
import EmptyState from '../../components/EmptyState';
import Loader from '../../components/Loader';
import {Collab} from '../../messages/CollabMessages';
import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import AddCollaborationModal from './AddCollaborationModal';

const KNOWN_PYTX_TYPES: Map<string, string> = new Map();
KNOWN_PYTX_TYPES.set(
  'threatexchange.exchanges.impl.fb_threatexchange_api.FBThreatExchangeCollabConfig',
  'ThreatExchange',
);
KNOWN_PYTX_TYPES.set(
  'threatexchange.exchanges.impl.ncmec_api.NCMECCollabConfig',
  'NCMEC',
);

function mapPyTXClassToShorthand(pytxClass: string): string {
  return KNOWN_PYTX_TYPES.get(pytxClass) || pytxClass;
}

function CollabCard({
  name,
  import_as_bank_id,
  collab_config_class,
  attributes,
}: Collab): JSX.Element {
  return (
    <Card className="my-4">
      <Card.Body>
        <h3>{name}</h3>
        <p>
          <NavLink
            to={generatePath('/banks/bank/:bankId/bank-details', {
              bankId: import_as_bank_id,
            })}>
            Go to bank.
          </NavLink>
        </p>
        <p>Type: {mapPyTXClassToShorthand(collab_config_class)}</p>
        <p>Attributes:</p>
        <ul>
          {Object.entries(attributes).map((values: [string, string]) => (
            <li key={values[0]}>
              {values[0]}: {values[1]}
            </li>
          ))}
        </ul>
      </Card.Body>
    </Card>
  );
}

export default function ViewCollaborations(): JSX.Element {
  const [neverFetched, setNeverFetched] = useState<boolean>(true);
  const [collabs, setCollabs] = useState<Collab[]>([]);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [refetchCounter, setRefetchCounter] = useState<number>(1);

  useEffect(() => {
    fetchAllCollabs().then(_collabs => {
      setCollabs(_collabs);
      setNeverFetched(false);
    });
  }, [refetchCounter]);

  return (
    <FixedWidthCenterAlignedLayout>
      <Row className="mt-4">
        <Col xs={{span: 8}}>
          <h1>Collaborations</h1>
        </Col>
        <Col xs={{span: 4}}>
          <div className="float-right">
            <Button onClick={() => setShowAddModal(true)}>Add Collab</Button>
          </div>
        </Col>
      </Row>
      <Row>
        {neverFetched ? (
          <Col>
            <Loader />
          </Col>
        ) : null}

        {neverFetched === false && collabs.length === 0 ? (
          <EmptyState>
            <EmptyState.Lead>
              You have not created a collab yet. Create your first collab!
            </EmptyState.Lead>
          </EmptyState>
        ) : null}

        {neverFetched === false && collabs.length !== 0 ? (
          <Col>
            {collabs.map(collab => (
              <CollabCard
                key={collab.name}
                name={collab.name}
                import_as_bank_id={collab.import_as_bank_id}
                collab_config_class={collab.collab_config_class}
                attributes={collab.attributes}
              />
            ))}
          </Col>
        ) : null}
      </Row>
      <AddCollaborationModal
        show={showAddModal}
        onHide={() => setShowAddModal(false)}
        didAdd={() => {
          setShowAddModal(false);
          setRefetchCounter(refetchCounter + 1);
        }}
      />
    </FixedWidthCenterAlignedLayout>
  );
}
