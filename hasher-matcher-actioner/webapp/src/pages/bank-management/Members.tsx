/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {Container, Row, Col, Button, Card, Spinner} from 'react-bootstrap';
import {fetchBank, fetchBankMembersPage} from '../../Api';
import {BankMember} from '../../messages/BankMessages';
import {ContentType} from '../../utils/constants';
import {timeAgoForDate} from '../../utils/DateTimeUtils';

import {BlurImage} from '../../utils/MediaUtils';
import AddBankMemberModal from './AddBankMemberModal';

export type BankTabProps = {
  bankId: string;
};

type OptionalString = string | undefined;

function Loader(): JSX.Element {
  return (
    <Col>
      <h5>
        <Spinner
          style={{verticalAlign: 'middle'}}
          className="mr-2"
          animation="border"
          variant="primary"
        />
        Loading...
      </h5>
    </Col>
  );
}

type EmptyStateProps = {
  onAdd: () => void;
};

function EmptyState({onAdd}: EmptyStateProps): JSX.Element {
  return (
    <Col xs={{offset: 2, span: 8}} className="py-4">
      <div className="h-100 text-center mt-4">
        <p className="lead">You have not added any members to this bank yet!</p>
        <p className="text-center">
          <Button variant="success" size="lg" onClick={onAdd}>
            Add Member
          </Button>
        </p>
      </div>
    </Col>
  );
}

type MemberPreviewProps = {
  thumbnailSrc: string;
  lastUpdated: Date;
};

function MemberPreview({
  thumbnailSrc,
  lastUpdated,
}: MemberPreviewProps): JSX.Element {
  return (
    <Col xs="3" className="mb-4">
      <Card>
        <BlurImage src={thumbnailSrc} />
        <Card.Body>
          <p className="text-small">Updated: {timeAgoForDate(lastUpdated)}</p>
        </Card.Body>
      </Card>
    </Col>
  );
}

export function VideoMembers({bankId}: BankTabProps): JSX.Element {
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
        <h1>Coming soon!</h1>
      </Row>
    </Container>
  );
}

export function PhotoMembers({bankId}: BankTabProps): JSX.Element {
  const [neverFetched, setNeverFetched] = useState<boolean>(true);
  const [showAddMemberModal, setShowAddMemberModal] = useState<boolean>(false);

  const [bankName, setBankName] = useState<string>('');
  const [members, setMembers] = useState<BankMember[]>([]);
  const [noMoreMembers, setNoMoreMembers] = useState<boolean>(false);
  const [continuationToken, setContinuationToken] =
    useState<OptionalString>(undefined);

  // Use this to refresh the banks list when a member is added.
  const [refetchCounter, setRefetchCounter] = useState<number>(0);

  useEffect(() => {
    fetchBankMembersPage(bankId, ContentType.Photo, continuationToken).then(
      resp => {
        setNeverFetched(false);
        setMembers(resp[0]);
        setContinuationToken(resp[1]);

        if (resp[1] === null) {
          // If there is no continuation token, indicates we reached the end of the list.
          setNoMoreMembers(true);
        }
      },
    );

    fetchBank(bankId).then(resp => setBankName(resp.bank_name));
  }, [refetchCounter]);

  const empty = members.length === 0 && noMoreMembers === true;

  return (
    <Container>
      <Row className="my-4">
        <Col xs="10">
          <h4>Photos in this bank.</h4>
        </Col>
        {/* Only show the CTA when not empty. The empty state has its own CTA. */}
        {!empty ? (
          <Col xs="2" className="text-right">
            <Button
              variant="primary"
              onClick={() => setShowAddMemberModal(true)}>
              Add Photo
            </Button>
          </Col>
        ) : null}
      </Row>
      <Row>
        {neverFetched ? <Loader /> : null}
        {empty ? (
          <EmptyState onAdd={() => setShowAddMemberModal(true)} />
        ) : null}
        {members.map(member => (
          <MemberPreview
            thumbnailSrc={member.preview_url!}
            lastUpdated={member.updated_at}
          />
        ))}
      </Row>
      <AddBankMemberModal
        onCloseClick={(didAdd = false) => {
          if (didAdd) {
            setRefetchCounter(refetchCounter + 1);
          }

          setShowAddMemberModal(false);
        }}
        bankId={bankId}
        bankName={bankName}
        show={showAddMemberModal}
        contentType={ContentType.Photo}
      />
    </Container>
  );
}
