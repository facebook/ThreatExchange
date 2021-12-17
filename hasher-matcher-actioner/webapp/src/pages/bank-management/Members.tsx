/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {
  Container,
  Row,
  Col,
  Button,
  Card,
  Spinner,
  ResponsiveEmbed,
} from 'react-bootstrap';
import {Link} from 'react-router-dom';
import {fetchBank, fetchBankMembersPage} from '../../Api';
import {BankMember} from '../../messages/BankMessages';
import {ContentType} from '../../utils/constants';
import {timeAgoForDate} from '../../utils/DateTimeUtils';
import Loader from '../../components/Loader';
import {BlurImage, BlurVideo} from '../../utils/MediaUtils';
import AddBankMemberModal from './AddBankMemberModal';

export type BankTabProps = {
  bankId: string;
};

type OptionalString = string | undefined;

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

export function MediaUnavailablePreview(): JSX.Element {
  return (
    <div className="p-4 bg-light" style={{borderBottom: '1px solid #6c757d'}}>
      <p className="lead">Media Not Provided</p>
      <p>Member was added without associated media.</p>
    </div>
  );
}

type MemberPreviewProps = {
  thumbnailSrc: string;
  lastUpdated: Date;
  type: ContentType;
  isMediaUnavailable: boolean;
  bankMemberId: string;
};

function MemberPreview({
  type,
  thumbnailSrc,
  lastUpdated,
  isMediaUnavailable,
  bankMemberId,
}: MemberPreviewProps): JSX.Element {
  return (
    <Col xs="4" className="mb-4">
      <Card>
        {isMediaUnavailable ? (
          <MediaUnavailablePreview />
        ) : (
          <ResponsiveEmbed aspectRatio="16by9">
            {type === ContentType.Video ? (
              <BlurVideo src={thumbnailSrc} />
            ) : (
              <BlurImage src={thumbnailSrc} />
            )}
          </ResponsiveEmbed>
        )}

        <Card.Body>
          <p className="text-small">
            <Link to={`/banks/member/${bankMemberId}`}>View Member</Link>
          </p>
          <p className="text-small">Updated: {timeAgoForDate(lastUpdated)}</p>
        </Card.Body>
      </Card>
    </Col>
  );
}

type BaseMembersProps = BankTabProps & {
  type: ContentType;
};

function BaseMembers({bankId, type}: BaseMembersProps): JSX.Element {
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
    fetchBankMembersPage(bankId, type, continuationToken).then(resp => {
      setNeverFetched(false);
      setMembers(resp[0]);
      setContinuationToken(resp[1]);

      if (resp[1] === null) {
        // If there is no continuation token, indicates we reached the end of the list.
        setNoMoreMembers(true);
      }
    });

    fetchBank(bankId).then(resp => setBankName(resp.bank_name));
  }, [refetchCounter]);

  const empty = members.length === 0 && noMoreMembers === true;

  let title = 'Photos in this bank';
  if (type === ContentType.Video) {
    title = 'Videos in this bank';
  }

  const ctaLabel = type === ContentType.Video ? 'Add Video' : 'Add Photo';

  return (
    <Container>
      <Row className="my-4">
        <Col xs="10">
          <h4>{title}</h4>
        </Col>
        {/* Only show the CTA when not empty. The empty state has its own CTA. */}
        {!empty ? (
          <Col xs="2" className="text-right">
            <Button
              variant="primary"
              onClick={() => setShowAddMemberModal(true)}>
              {ctaLabel}
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
            bankMemberId={member.bank_member_id}
            type={type}
            isMediaUnavailable={member.is_media_unavailable}
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
        contentType={type}
      />
    </Container>
  );
}

export function PhotoMembers({bankId}: BankTabProps): JSX.Element {
  return <BaseMembers type={ContentType.Photo} bankId={bankId} />;
}

export function VideoMembers({bankId}: BankTabProps): JSX.Element {
  return <BaseMembers type={ContentType.Video} bankId={bankId} />;
}
