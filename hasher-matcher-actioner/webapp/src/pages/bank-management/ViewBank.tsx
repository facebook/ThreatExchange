/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {Container, Row, Col, Form, Button, Card} from 'react-bootstrap';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import {generatePath, useHistory, useParams} from 'react-router-dom';
import {fetchBank, updateBank} from '../../Api';
import BankDetailsForm from '../../forms/BankDetailsForm';
import {Bank} from '../../messages/BankMessages';
import {BlurImage} from '../../utils/MediaUtils';

import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';

type BankTabProps = {
  bankId: string;
};

function BankDetails({bankId}: BankTabProps): JSX.Element {
  const [bank, setBank] = useState<Bank>();
  const [formResetCounter, setFormResetCounter] = useState<number>(0);

  useEffect(() => {
    fetchBank(bankId).then(setBank);
  }, []);

  return (
    <Row>
      <Col xs="6">
        {bank !== undefined ? (
          <BankDetailsForm
            bankName={bank.bank_name}
            bankDescription={bank.bank_description}
            handleSubmit={(bankName, bankDescription) => {
              updateBank(bankId, bankName, bankDescription).then(setBank);
              setFormResetCounter(formResetCounter + 1);
            }}
            formResetCounter={formResetCounter}
          />
        ) : (
          <p>Loading ...</p>
        )}
      </Col>
    </Row>
  );
}

function MemberPreview(): JSX.Element {
  return (
    <Col xs="3" className="mb-4">
      <Card>
        <BlurImage src="https://upload.wikimedia.org/wikipedia/commons/b/b1/VAN_CAT.png" />
        <Card.Body>
          <p className="text-small">First Updated: yesterday</p>
          <p className="text-small">Last Seen: seconds ago`</p>
        </Card.Body>
      </Card>
    </Col>
  );
}

function VideoMembers({bankId}: BankTabProps): JSX.Element {
  return (
    <Container>
      <Row className="my-4">
        <Col xs="10">
          <h4>Videos in this bank.</h4>
        </Col>
        <Col xs="2" className="text-right">
          <Button variant="primary">Add Video</Button>
        </Col>
      </Row>
      <Row>
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
      </Row>
    </Container>
  );
}

function PhotoMembers({bankId}: BankTabProps): JSX.Element {
  return (
    <Container>
      <Row className="my-4">
        <Col xs="10">
          <h4>Photos in this bank.</h4>
        </Col>
        <Col xs="2" className="text-right">
          <Button variant="primary">Add Photo</Button>
        </Col>
      </Row>
      <Row>
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
        <MemberPreview />
      </Row>
    </Container>
  );
}

export default function ViewBank(): JSX.Element {
  const {bankId, tab} = useParams<{bankId: string; tab: string}>();
  const history = useHistory();

  const pageTitle = 'Edit Bank';

  return (
    <FixedWidthCenterAlignedLayout title={pageTitle}>
      <Row>
        <Col>
          <Tabs
            onSelect={key => {
              history.push(
                generatePath('/banks/bank/:bankId/:tab', {
                  bankId,
                  tab: key !== null ? key : 'bank-details',
                }),
              );
            }}
            activeKey={tab}>
            <Tab eventKey="bank-details" title="Bank Details">
              <BankDetails bankId={bankId} />
            </Tab>
            <Tab eventKey="video-memberships" title="Video Memberships">
              <VideoMembers bankId={bankId} />
            </Tab>
            <Tab eventKey="photo-memberships" title="Photo Memberships">
              <PhotoMembers bankId={bankId} />
            </Tab>
          </Tabs>
        </Col>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}
