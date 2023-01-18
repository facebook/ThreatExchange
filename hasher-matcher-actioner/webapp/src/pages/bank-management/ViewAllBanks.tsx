/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState} from 'react';
import {Row, Col, Card, Button} from 'react-bootstrap';
import {generatePath, useHistory} from 'react-router-dom';
import {fetchAllBanks} from '../../Api';
import EmptyState from '../../components/EmptyState';
import Loader from '../../components/Loader';
import {Bank} from '../../messages/BankMessages';

import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import AddBankModal from './AddBankModal';

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

export default function ViewAllBanks(): JSX.Element {
  const [neverFetched, setNeverFetched] = useState<boolean>(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [banks, setBanks] = useState<Bank[]>([]);

  // Increment value every time create modal is closed to trigger refetch
  const [createModalClosed, setCreateModalClosed] = useState(0);

  useEffect(() => {
    fetchAllBanks().then(banks_response => {
      setBanks(banks_response);
      setNeverFetched(false);
    });
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
            configured to automatically take actions on matches. Read more in{' '}
            <a href="https://github.com/facebook/ThreatExchange/wiki/Creating-and-Managing-Banks">
              the wiki
            </a>
            .
          </p>
        </Col>
      </Row>
      <Row>
        {neverFetched ? (
          <Col xs={{offset: 2, span: 8}}>
            <Loader />
          </Col>
        ) : null}

        {neverFetched === false && banks.length === 0 ? (
          <EmptyState>
            <EmptyState.Lead>
              You have not created banks yet. Create your first bank!
            </EmptyState.Lead>
            <EmptyState.CTA onClick={() => setShowCreateModal(true)}>
              Create Bank
            </EmptyState.CTA>
          </EmptyState>
        ) : null}
        {neverFetched === false && banks.length !== 0 ? (
          <Col xs={{offset: 2, span: 8}}>
            {banks.map(bank => (
              <BankCard
                bankId={bank.bank_id}
                bankName={bank.bank_name}
                bankDescription={bank.bank_description}
              />
            ))}
          </Col>
        ) : null}
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
