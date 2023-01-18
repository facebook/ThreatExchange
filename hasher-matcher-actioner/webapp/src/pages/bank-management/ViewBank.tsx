/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState} from 'react';
import {Row, Col} from 'react-bootstrap';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import {generatePath, useHistory, useParams} from 'react-router-dom';

import {fetchBank, updateBank} from '../../Api';
import ReturnTo from '../../components/ReturnTo';

import BankDetailsForm from '../../forms/BankDetailsForm';
import {Bank} from '../../messages/BankMessages';
import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import {BankTabProps, VideoMembers, PhotoMembers} from './Members';

function BankDetails({bankId}: BankTabProps): JSX.Element {
  const [bank, setBank] = useState<Bank>();
  const [formResetCounter, setFormResetCounter] = useState<number>(0);

  useEffect(() => {
    fetchBank(bankId).then(setBank);
  }, []);

  return (
    <Row>
      <Col xs={{span: 6}}>
        {bank !== undefined ? (
          <BankDetailsForm
            bankName={bank.bank_name}
            bankDescription={bank.bank_description}
            isActive={bank.is_active}
            tags={bank.bank_tags}
            handleSubmit={(bankName, bankDescription, isActive, tags) => {
              updateBank(
                bankId,
                bankName,
                bankDescription,
                isActive,
                tags,
              ).then(setBank);
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

export default function ViewBank(): JSX.Element {
  const {bankId, tab} = useParams<{bankId: string; tab: string}>();
  const [bank, setBank] = useState<Bank>();
  const history = useHistory();

  useEffect(() => {
    fetchBank(bankId).then(setBank);
  }, []);

  const pageTitle =
    bank && bank.bank_name ? `Edit Bank: ${bank.bank_name}` : 'Edit Bank';
  const returnURL = '/banks/';

  return (
    <FixedWidthCenterAlignedLayout>
      <Row>
        <Col className="my-4">
          <ReturnTo to={returnURL}>Back to all Banks</ReturnTo>
        </Col>
      </Row>
      <Row>
        <Col>
          <h2>{pageTitle}</h2>
        </Col>
      </Row>
      <Row>
        <Col className="py-2">
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
