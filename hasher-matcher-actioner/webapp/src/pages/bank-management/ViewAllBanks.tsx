/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {Row, Col, Card, Button} from 'react-bootstrap';
import {generatePath, useHistory} from 'react-router-dom';
import {fetchAllBanks} from '../../Api';
import {Bank} from '../../messages/BankMessages';

import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import AddBankModal from './AddBankModal';

// TODO: Move to components, and other files
type BankDetails = {
  bankName: string;
  bankDescription: string;
  bankId: string;
};

function BankCard({
  bankName,
  bankDescription,
  bankId,
}: BankDetails): JSX.Element {
  const history = useHistory();

  const navigateToBank = () => {
    history.push(generatePath('/banks/bank/:bankId/bank-details', {bankId}));
  };

  return (
    <Card className="my-4" onClick={navigateToBank}>
      <Card.Body>
        <h2>{bankName}</h2>
        <p>{bankDescription}</p>
      </Card.Body>
    </Card>
  );
}
// TODO: move to components and other files
type EmptyStateProps = {
  onCreate: () => void;
};

function EmptyState({onCreate}: EmptyStateProps): JSX.Element {
  return (
    <Col xs={{offset: 2, span: 8}} className="py-4">
      <div className="h-100" style={{textAlign: 'center', paddingTop: '40%)'}}>
        <p className="lead">
          You have not created banks yet. Create your first bank!
        </p>
        <p className="text-center">
          <Button variant="success" size="lg" onClick={onCreate}>
            Create Bank
          </Button>
        </p>
      </div>
    </Col>
  );
}

export default function ViewAllBanks(): JSX.Element {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [banks, setBanks] = useState<Bank[]>([]);

  // Increment value every time create modal is closed to trigger refetch
  const [createModalClosed, setCreateModalClosed] = useState(0);

  useEffect(() => {
    fetchAllBanks().then(setBanks);
  }, [createModalClosed]);

  return (
    <FixedWidthCenterAlignedLayout>
      <Row className="mt-4">
        <Col xs={{offset: 2, span: 6}}>
          <h1>Banks</h1>
        </Col>
        <Col xs="2">
          <div className="float-right">
            {/* Only show the right-aligned create button if we have banks. Do not want to have multiple CTAs. */}
            {banks.length === 0 ? null : (
              <Button onClick={() => setShowCreateModal(true)}>Add Bank</Button>
            )}
          </div>
        </Col>
      </Row>
      <Row>
        <Col xs={{offset: 2, span: 8}}>
          <p className="description text-muted mt-4">
            Use banks to manage sets of images or videos you want to action on.
            When you &ldquo;submit&rdquo; images or videos, HMA will
            automatically try to match against these banks. Banks can be
            configured to automatically take action or prevent other actions
            from being taken.
          </p>
        </Col>
      </Row>
      <Row>
        {banks.length === 0 ? (
          <EmptyState onCreate={() => setShowCreateModal(true)} />
        ) : (
          <Col xs={{offset: 2, span: 8}}>
            {banks.map(bank => (
              <BankCard
                bankId={bank.bank_id}
                bankName={bank.bank_name}
                bankDescription={bank.bank_description}
              />
            ))}
          </Col>
        )}
      </Row>
      <AddBankModal
        onCloseClick={() => {
          setShowCreateModal(false);
          setCreateModalClosed(createModalClosed + 1);
        }}
        show={showCreateModal}
      />
    </FixedWidthCenterAlignedLayout>
  );
}
